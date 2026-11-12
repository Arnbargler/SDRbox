"""S4: fixed SDR capture, concurrent NFM audio and FFT analysis.

No tuner hops or confirmed hit logs; audio is local rackio ALSA only.
Only the capture worker accesses RTL-SDR. PCM and FFT run independently.
"""
import queue
import threading
import time

import numpy as np
from scipy.ndimage import percentile_filter
from rtlsdr import RtlSdr

from .detector import CandidateTracker, detect_bins
from .selector import SignalSelector
from .audio import NfmDemodulator, silence
from .playback import BufferedAudioPlayer

CENTER_HZ = 462_650_000
SAMPLE_RATE = 1_536_000
READ_SIZE = 131_072  # 85.33 ms IQ at 1.536 MS/s
FFT_SIZE = 4096
POINTS = 512
# Preserve the center 1.3 MHz of the lower-rate IQ capture.
USABLE_HZ = 1_300_000
UPDATE_SECONDS = 0.35
DEFAULT_THRESHOLD_DB = 15.0
GMRS_CENTERS_HZ = tuple(462_562_500 + i * 25_000 for i in range(7))
# Stay within established GMRS channel centers, not arbitrary neighboring peaks.
CHANNEL_TOLERANCE_HZ = 9_000



def analyze(iq, return_bins=False):
    """Return relative averaged FFT power and locally estimated noise floor."""
    chunks = np.asarray(iq, dtype=np.complex64).reshape(-1, FFT_SIZE)
    window = np.hanning(FFT_SIZE).astype(np.float32)
    fft = np.fft.fftshift(np.fft.fft(chunks * window, axis=1), axes=1)
    averaged = np.mean(np.abs(fft) ** 2, axis=0)
    db = 10.0 * np.log10(np.maximum(averaged, 1e-15))
    # Local 25th-percentile baseline over a ~100 kHz neighborhood.
    # Relative arbitrary dB units, NOT dBm or calibrated SNR.
    floor = percentile_filter(db, percentile=25, size=201, mode="nearest")
    frequencies = (np.arange(FFT_SIZE) - FFT_SIZE // 2) * (SAMPLE_RATE / FFT_SIZE)
    keep = np.abs(frequencies) <= USABLE_HZ / 2
    data = db[keep]
    base = floor[keep]
    # Resample to 512 points using *max* power, retaining narrow peaks.
    indices = np.linspace(0, len(data), POINTS + 1, dtype=int)
    top = np.asarray([np.max(data[indices[i]:indices[i + 1]]) for i in range(POINTS)])
    noise = np.asarray([np.median(base[indices[i]:indices[i + 1]]) for i in range(POINTS)])
    result = {
        "center_mhz": CENTER_HZ / 1e6,
        "low_mhz": (CENTER_HZ - USABLE_HZ / 2) / 1e6,
        "high_mhz": (CENTER_HZ + USABLE_HZ / 2) / 1e6,
        "sample_rate_hz": SAMPLE_RATE,
        "fft_size": FFT_SIZE,
        "units": "relative_dB_uncalibrated",
        "power_db": np.around(top, 1).tolist(),
        "noise_db": np.around(noise, 1).tolist(),
        "captured_at": time.time(),
    }
    return (result, db, floor) if return_bins else result


class SpectrumMonitor:
    """Three independent workers: RTL I/O, NFM/PCM, and FFT/detection.

    RTL I/O never demodulates or computes FFTs. No IQ blocks are intentionally
    discarded except under measured overload; overloads are counted/reported.
    """

    def __init__(self, callback):
        self.callback = callback
        self._stop = threading.Event()
        self._threshold_changed = threading.Event()
        self.thread = None
        self._audio_thread = None
        self._fft_thread = None
        self._audio_queue = queue.Queue(maxsize=12)
        self._fft_queue = queue.Queue(maxsize=1)
        self.tracker = CandidateTracker()
        self.selector = SignalSelector()
        self.threshold_db = DEFAULT_THRESHOLD_DB
        self.error = None
        self._selection = {"status": "SEARCHING", "frequency_mhz": None}
        self._audio_status = "LOCAL AUDIO MUTED"
        self._audio_target_mhz = None
        self._audio_stats = {}
        self._capture_stats = {}
        self._discarded_iq = 0

    def set_threshold(self, threshold_db):
        value = float(threshold_db)
        if not 8.0 <= value <= 30.0:
            raise ValueError("Minimum RF contrast must be 8–30 dB")
        self.threshold_db = value
        self._threshold_changed.set()

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self.error = None
        self._discarded_iq = 0
        self.tracker.reset()
        self.selector.reset()
        self._selection = {"status": "SEARCHING", "frequency_mhz": None}
        self._threshold_changed.clear()
        self._audio_queue = queue.Queue(maxsize=12)
        self._fft_queue = queue.Queue(maxsize=1)
        self._audio_thread = threading.Thread(target=self._audio_loop, daemon=True, name="sdrbox-demod")
        self._fft_thread = threading.Thread(target=self._fft_loop, daemon=True, name="spectrum-fft")
        self._audio_thread.start()
        self._fft_thread.start()
        self.thread = threading.Thread(target=self._run, daemon=True, name="sdrbox-usb")
        self.thread.start()

    def stop(self):
        self._stop.set()
        for worker in (self.thread, self._fft_thread, self._audio_thread):
            if worker is not None and worker is not threading.current_thread():
                worker.join(timeout=3)
                if worker.is_alive():
                    raise RuntimeError(f"SDRbox {worker.name} did not stop in 3 seconds")
        self.thread = self._fft_thread = self._audio_thread = None

    @staticmethod
    def _channel_candidates(candidates):
        mapped = {}
        for candidate in candidates:
            hz = candidate["frequency_mhz"] * 1e6
            center = min(GMRS_CENTERS_HZ, key=lambda x: abs(x - hz))
            if abs(center - hz) > CHANNEL_TOLERANCE_HZ:
                continue
            item = dict(candidate)
            item["peak_frequency_mhz"] = candidate["frequency_mhz"]
            item["frequency_mhz"] = center / 1e6
            if center not in mapped or item["contrast_db"] > mapped[center]["contrast_db"]:
                mapped[center] = item
        return list(mapped.values())

    def _fft_loop(self):
        try:
            while not self._stop.is_set():
                try:
                    iq = self._fft_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if self._threshold_changed.is_set():
                    self._threshold_changed.clear()
                    self.tracker.reset()
                    self.selector.reset()
                    self._selection = {"status": "SEARCHING", "frequency_mhz": None}
                result, power, floor = analyze(iq, return_bins=True)
                detected = detect_bins(power, floor, SAMPLE_RATE, CENTER_HZ, self.threshold_db)
                tracked = self.tracker.update(detected)
                hold = detect_bins(power, floor, SAMPLE_RATE, CENTER_HZ,
                                   max(5.0, self.threshold_db - 5.0))
                selection = self.selector.update(
                    self._channel_candidates(tracked), time.monotonic(),
                    hold_candidates=self._channel_candidates(hold),
                )
                self._selection = selection
                result.update(
                    candidates=tracked,
                    selection={**selection,
                               "audio_active": self._audio_target_mhz is not None,
                               "audio_hold": selection["status"] == "HANG"},
                    candidate_threshold_db=self.threshold_db,
                    candidate_method="local_contrast_2_of_3_gmrs_selection",
                    audio=self._audio_status,
                    audio_frequency_mhz=self._audio_target_mhz,
                    audio_gate="OPEN" if self._audio_target_mhz is not None else "CLOSED",
                    audio_diagnostics={**self._audio_stats, **self._capture_stats},
                )
                self.callback("spectrum", result)
        except Exception as exc:
            self._failure("FFT", exc)

    def _audio_loop(self):
        demod = NfmDemodulator()
        player = BufferedAudioPlayer()
        audio_error = None
        total_processing_seconds = 0.0
        count = 0
        try:
            try:
                player.start()
            except OSError as exc:
                audio_error = f"Cannot start aplay: {exc}"
            while not self._stop.is_set():
                try:
                    iq = self._audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                began = time.monotonic()
                selection = self._selection
                target_hz = None
                if selection["status"] in ("SELECTED", "HANG") and selection.get("frequency_mhz") is not None:
                    target_hz = min(
                        GMRS_CENTERS_HZ,
                        key=lambda hz: abs(hz - selection["frequency_mhz"] * 1e6),
                    )
                if target_hz is None:
                    demod.reset()
                    pcm = silence(len(iq))
                else:
                    demod.tune(target_hz, CENTER_HZ, len(iq))
                    pcm = demod.demodulate(iq)
                elapsed = time.monotonic() - began
                total_processing_seconds += elapsed
                count += 1
                player.offer(pcm)
                audio_error = player.error or audio_error
                self._audio_status = (
                    "ERROR: " + audio_error if audio_error
                    else "LOCAL NFM ACTIVE" if target_hz is not None
                    else "LOCAL AUDIO MUTED"
                )
                self._audio_target_mhz = target_hz / 1e6 if target_hz is not None and not audio_error else None
                self._audio_stats = {
                    **player.stats(),
                    "avg_processing_ms": round(total_processing_seconds * 1000 / count, 1),
                    "iq_audio_queue_ms": round(self._audio_queue.qsize() * READ_SIZE * 1000 / SAMPLE_RATE, 1),
                }
        except Exception as exc:
            self._failure("audio", exc)
        finally:
            player.stop()

    def _run(self):
        sdr = None
        total_read_seconds = 0.0
        count = 0
        samples = 0
        try:
            sdr = RtlSdr(0)
            sdr.sample_rate = SAMPLE_RATE
            sdr.center_freq = CENTER_HZ
            sdr.gain = 30
            sdr.read_samples(READ_SIZE)  # discard tuner settling
            started = time.monotonic()
            last_fft = 0.0
            while not self._stop.is_set():
                begin = time.monotonic()
                iq = sdr.read_samples(READ_SIZE)
                now = time.monotonic()
                total_read_seconds += now - begin
                count += 1
                samples += len(iq)
                # The USB worker must not block waiting on audio DSP.
                try:
                    self._audio_queue.put_nowait(iq)
                except queue.Full:
                    # Losing a voice block is an error; report every loss.
                    self._discarded_iq += 1
                if now - last_fft >= UPDATE_SECONDS:
                    try:
                        self._fft_queue.put_nowait(iq)
                    except queue.Full:
                        pass  # stale FFT snapshots may be omitted
                    last_fft = now
                elapsed = max(time.monotonic() - started, 0.001)
                self._capture_stats = {
                    "pcm_supply_ratio": round((samples / SAMPLE_RATE) / elapsed, 3),
                    "avg_iq_read_ms": round(total_read_seconds * 1000 / count, 1),
                    "iq_block_ms": round(READ_SIZE * 1000 / SAMPLE_RATE, 1),
                    "iq_dropped_blocks": self._discarded_iq,
                }
        except Exception as exc:
            self._failure("RTL-SDR", exc)
        finally:
            self._stop.set()
            if sdr is not None:
                try:
                    sdr.close()
                except Exception:
                    pass

    def _failure(self, stage, exc):
        if not self._stop.is_set():
            self.error = f"{stage}: {type(exc).__name__}: {exc}"
            self.callback("spectrum_error", self.error)
            self._stop.set()
