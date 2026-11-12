"""S4: single-window FFT, GMRS candidate selection and in-window NFM audio.

No tuner hops or confirmed hit logs; audio is local rackio ALSA only.
All SDR USB calls and streaming DSP belong to one worker thread.
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
SAMPLE_RATE = 2_048_000
READ_SIZE = 131_072  # 64 ms IQ blocks: amortize synchronous USB/Python overhead
FFT_SIZE = 4096
POINTS = 512
# Deliberately use the center 1.7 MHz of the 2.048 MHz capture.
USABLE_HZ = 1_700_000
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
    def __init__(self, callback):
        self.callback = callback
        self._stop = threading.Event()
        self.thread = None
        self.error = None
        self.tracker = CandidateTracker()
        self.selector = SignalSelector()
        self.threshold_db = DEFAULT_THRESHOLD_DB
        self._threshold_changed = threading.Event()
        self._fft_queue = queue.Queue(maxsize=1)
        self._fft_thread = None
        self._selection = {"status": "SEARCHING", "frequency_mhz": None}
        self._audio_status = "LOCAL AUDIO MUTED"
        self._audio_target_mhz = None
        self._audio_stats = {}

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
        self.tracker.reset()
        self.selector.reset()
        self._threshold_changed.clear()
        self._selection = {"status": "SEARCHING", "frequency_mhz": None}
        self._fft_queue = queue.Queue(maxsize=1)
        self._fft_thread = threading.Thread(target=self._fft_loop, daemon=True, name="spectrum-fft")
        self._fft_thread.start()
        self.thread = threading.Thread(target=self._run, daemon=True, name="spectrum-462")
        self.thread.start()

    def stop(self):
        self._stop.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)
            if self.thread.is_alive():
                raise RuntimeError("RTL-SDR spectrum read did not stop within 3 seconds")
        self.thread = None
        if self._fft_thread is not None:
            self._fft_thread.join(timeout=3)
            if self._fft_thread.is_alive():
                raise RuntimeError("FFT analysis worker did not stop")
            self._fft_thread = None

    def _fft_loop(self):
        """Analyze a recent IQ sample without delaying capture or audio delivery.

        A one-slot queue intentionally discards obsolete *visualization* frames.
        It never discards or consumes audio samples, which remain exclusively
        in the capture worker. Both workers only read immutable IQ arrays.
        """
        try:
            while not self._stop.is_set():
                try:
                    iq = self._fft_queue.get(timeout=0.10)
                except queue.Empty:
                    continue
                if self._threshold_changed.is_set():
                    self._threshold_changed.clear()
                    self.tracker.reset()
                    self.selector.reset()
                    self._selection = {"status": "SEARCHING", "frequency_mhz": None}
                result, power, floor = analyze(iq, return_bins=True)
                candidates = detect_bins(
                    power, floor, SAMPLE_RATE, CENTER_HZ,
                    threshold_db=self.threshold_db,
                )
                tracked = self.tracker.update(candidates)
                def channel_candidates(items):
                    unique = {}
                    for c in items:
                        hz = c["frequency_mhz"] * 1e6
                        center = min(GMRS_CENTERS_HZ, key=lambda ch: abs(ch - hz))
                        if abs(center - hz) > CHANNEL_TOLERANCE_HZ:
                            continue
                        item = dict(c)
                        item["peak_frequency_mhz"] = c["frequency_mhz"]
                        item["frequency_mhz"] = center / 1e6
                        if center not in unique or item["contrast_db"] > unique[center]["contrast_db"]:
                            unique[center] = item
                    return list(unique.values())
                eligible = channel_candidates(tracked)
                weaker = detect_bins(
                    power, floor, SAMPLE_RATE, CENTER_HZ,
                    threshold_db=max(5.0, self.threshold_db - 5.0),
                )
                selection = self.selector.update(
                    eligible, time.monotonic(), hold_candidates=channel_candidates(weaker)
                )
                self._selection = selection
                result["candidates"] = tracked
                result["selection"] = dict(selection)
                result["candidate_threshold_db"] = self.threshold_db
                result["candidate_method"] = "local_contrast_2_of_3_gmrs_selection"
                result["audio"] = self._audio_status
                result["audio_frequency_mhz"] = self._audio_target_mhz
                result["audio_gate"] = "OPEN" if self._audio_target_mhz is not None else "CLOSED"
                result["selection"]["audio_active"] = self._audio_target_mhz is not None
                result["selection"]["audio_hold"] = selection["status"] == "HANG"
                result["audio_diagnostics"] = dict(self._audio_stats)
                self.callback("spectrum", result)
        except Exception as exc:
            if not self._stop.is_set():
                self.error = f"FFT analysis: {type(exc).__name__}: {exc}"
                self.callback("spectrum_error", self.error)
                self._stop.set()

    def _run(self):
        sdr = None
        player = BufferedAudioPlayer()
        demod = NfmDemodulator()
        audio_error = None
        last_iq_at = None
        max_iq_gap_ms = 0.0
        max_dsp_ms = 0.0
        total_read_seconds = 0.0
        total_processing_seconds = 0.0
        processed_blocks = 0
        last_selection = {"status": "SEARCHING", "frequency_mhz": None}
        try:
            sdr = RtlSdr(0)
            sdr.sample_rate = SAMPLE_RATE
            sdr.center_freq = CENTER_HZ
            sdr.gain = 30
            # The PCM writer has its own queue/thread: ALSA pipe backpressure
            # must not stall USB capture or the time-critical demod path.
            try:
                player.start()
            except OSError as exc:
                audio_error = f"Cannot start aplay: {exc}"
            sdr.read_samples(READ_SIZE)  # discard unsteady initial samples
            last_fft = 0.0
            started_at = time.monotonic()
            produced_samples = 0
            while not self._stop.is_set():
                read_started = time.monotonic()
                iq = sdr.read_samples(READ_SIZE)
                now = time.monotonic()
                total_read_seconds += now - read_started
                produced_samples += len(iq)
                if last_iq_at is not None:
                    max_iq_gap_ms = max(max_iq_gap_ms, (now - last_iq_at) * 1000.0)
                last_iq_at = now
                if now - last_fft >= UPDATE_SECONDS:
                    # Sending to FFT is nonblocking: stale display frames can
                    # be skipped, but USB and PCM must never wait for an FFT.
                    try:
                        self._fft_queue.put_nowait(iq)
                    except queue.Full:
                        pass
                    last_fft = now
                last_selection = self._selection
                # Keep demodulation running through a short RF fade while
                # the selector is in HANG. The 1.2 s timeout still ends
                # the selection and mutes local audio on real release.
                audio_active = last_selection["status"] in ("SELECTED", "HANG")
                selected_mhz = last_selection.get("frequency_mhz")
                target_hz = None
                if audio_active and selected_mhz is not None:
                    target_hz = min(
                        GMRS_CENTERS_HZ,
                        key=lambda hz: abs(hz - selected_mhz * 1e6),
                    )
                # The capture worker never waits for ALSA writes. Record how
                # much time DSP itself consumes for comparison against 16ms IQ.
                dsp_started = time.monotonic()
                if target_hz is None:
                    demod.reset()
                    pcm = silence(len(iq))
                else:
                    demod.tune(target_hz, CENTER_HZ, len(iq))
                    pcm = demod.demodulate(iq)
                max_dsp_ms = max(max_dsp_ms, (time.monotonic() - dsp_started) * 1000)
                player.offer(pcm)
                audio_error = player.error or audio_error
                total_processing_seconds += time.monotonic() - now
                processed_blocks += 1
                self._audio_status = (
                    "ERROR: " + audio_error if audio_error
                    else "LOCAL NFM ACTIVE" if target_hz is not None
                    else "LOCAL AUDIO MUTED"
                )
                self._audio_target_mhz = target_hz / 1e6 if target_hz is not None and not audio_error else None
                elapsed = max(0.001, time.monotonic() - started_at)
                self._audio_stats = {
                    **player.stats(),
                    "max_iq_interval_ms": round(max_iq_gap_ms, 1),
                    "max_demod_ms": round(max_dsp_ms, 1),
                    "pcm_supply_ratio": round((produced_samples / SAMPLE_RATE) / elapsed, 3),
                    "avg_iq_read_ms": round(total_read_seconds * 1000 / max(1, processed_blocks), 1),
                    "avg_processing_ms": round(total_processing_seconds * 1000 / max(1, processed_blocks), 1),
                    "iq_block_ms": round(READ_SIZE * 1000 / SAMPLE_RATE, 1),
                }
        except Exception as exc:
            if not self._stop.is_set():
                self.error = f"{type(exc).__name__}: {exc}"
                self.callback("spectrum_error", self.error)
        finally:
            self._stop.set()
            player.stop()
            if sdr is not None:
                try:
                    sdr.close()
                except Exception:
                    pass
