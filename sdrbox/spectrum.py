"""S4: single-window FFT, GMRS candidate selection and in-window NFM audio.

No tuner hops or confirmed hit logs; audio is local rackio ALSA only.
All SDR USB calls and streaming DSP belong to one worker thread.
"""
import subprocess
import threading
import time

import numpy as np
from scipy.ndimage import percentile_filter
from rtlsdr import RtlSdr

from .detector import CandidateTracker, detect_bins
from .selector import SignalSelector
from .audio import NfmDemodulator, silence

CENTER_HZ = 462_650_000
SAMPLE_RATE = 2_048_000
READ_SIZE = 32_768
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
        self.thread = threading.Thread(target=self._run, daemon=True, name="spectrum-462")
        self.thread.start()

    def stop(self):
        self._stop.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)
            if self.thread.is_alive():
                raise RuntimeError("RTL-SDR spectrum read did not stop within 3 seconds")
        self.thread = None

    def _run(self):
        sdr = None
        player = None
        demod = NfmDemodulator()
        audio_error = None
        last_selection = {"status": "SEARCHING", "frequency_mhz": None}
        try:
            sdr = RtlSdr(0)
            sdr.sample_rate = SAMPLE_RATE
            sdr.center_freq = CENTER_HZ
            sdr.gain = 30
            # Local speaker output, independent of browser sessions.
            # Keep ALSA clock fed with silence when not receiving, avoiding
            # expensive/repeated process starts and underruns on lock changes.
            try:
                player = subprocess.Popen(
                    ["aplay", "-q", "-r", "24000", "-f", "S16_LE", "-c", "1"],
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE, bufsize=0,
                )
            except OSError as exc:
                audio_error = f"Cannot start aplay: {exc}"
            sdr.read_samples(READ_SIZE)  # discard unsteady initial samples
            last_fft = 0.0
            while not self._stop.is_set():
                iq = sdr.read_samples(READ_SIZE)
                now = time.monotonic()
                if self._threshold_changed.is_set():
                    self._threshold_changed.clear()
                    self.tracker.reset()
                    self.selector.reset()
                    demod.reset()
                    last_selection = {"status": "SEARCHING", "frequency_mhz": None}
                if now - last_fft >= UPDATE_SECONDS:
                    # FFT + detector reuse the SAME measured averaged spectrum.
                    result, power, floor = analyze(iq, return_bins=True)
                    candidates = detect_bins(
                        power, floor, SAMPLE_RATE, CENTER_HZ,
                        threshold_db=self.threshold_db,
                    )
                    tracked = self.tracker.update(candidates)
                    # Show every RF candidate on FFT, but select/listen only
                    # near actual GMRS 1–7 channel centers in this S4 milestone.
                    # Map peaks to the SAME nominal GMRS channel center
                    # before matching. Frequency estimates can shift several
                    # kHz during FM speech; that is not a channel change.
                    def channel_candidates(items):
                        mapped = []
                        for c in items:
                            hz = c["frequency_mhz"] * 1e6
                            nearest = min(GMRS_CENTERS_HZ, key=lambda center: abs(center - hz))
                            if abs(nearest - hz) <= CHANNEL_TOLERANCE_HZ:
                                item = dict(c)
                                item["peak_frequency_mhz"] = c["frequency_mhz"]
                                item["frequency_mhz"] = nearest / 1e6
                                mapped.append(item)
                        # Only the strongest apparent peak per radio channel.
                        unique = {}
                        for item in mapped:
                            freq = item["frequency_mhz"]
                            if freq not in unique or item["contrast_db"] > unique[freq]["contrast_db"]:
                                unique[freq] = item
                        return list(unique.values())

                    eligible = channel_candidates(tracked)
                    # Hysteresis: keep a selected channel using weaker RF
                    # evidence, without letting weak peaks start new locks.
                    hold_db = max(5.0, self.threshold_db - 5.0)
                    weaker = detect_bins(
                        power, floor, SAMPLE_RATE, CENTER_HZ,
                        threshold_db=hold_db,
                    )
                    hold_candidates = channel_candidates(weaker)
                    last_selection = self.selector.update(
                        eligible, now, hold_candidates=hold_candidates
                    )
                    result["candidates"] = tracked
                    result["selection"] = last_selection
                    result["candidate_threshold_db"] = self.threshold_db
                    result["candidate_method"] = "local_contrast_2_of_3_gmrs_selection"
                    last_fft = now
                else:
                    result = None

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
                if player is not None and audio_error is None:
                    if player.poll() is not None:
                        audio_error = f"aplay exited: {player.returncode}"
                    else:
                        try:
                            if target_hz is None:
                                demod.reset()
                                pcm = silence(len(iq))
                            else:
                                demod.tune(target_hz, CENTER_HZ, len(iq))
                                pcm = demod.demodulate(iq)
                            player.stdin.write(pcm.tobytes())
                        except (OSError, BrokenPipeError) as exc:
                            audio_error = f"Local PCM write failed: {exc}"
                if result is not None:
                    result["audio"] = (
                        "ERROR: " + audio_error if audio_error
                        else "LOCAL NFM ACTIVE" if target_hz is not None
                        else "LOCAL AUDIO MUTED"
                    )
                    result["audio_frequency_mhz"] = (
                        target_hz / 1e6 if target_hz is not None and not audio_error
                        else None
                    )
                    result["selection"]["audio_active"] = bool(target_hz is not None and not audio_error)
                    result["selection"]["audio_hold"] = last_selection["status"] == "HANG"
                    result["audio_gate"] = "OPEN" if target_hz is not None else "CLOSED"
                    self.callback("spectrum", result)
        except Exception as exc:
            if not self._stop.is_set():
                self.error = f"{type(exc).__name__}: {exc}"
                self.callback("spectrum_error", self.error)
        finally:
            if player is not None:
                try:
                    player.stdin.close()
                except (OSError, ValueError):
                    pass
                if player.poll() is None:
                    player.terminate()
                try:
                    player.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    player.kill()
                    player.wait(timeout=1.0)
                if player.stderr is not None:
                    player.stderr.close()
            if sdr is not None:
                try:
                    sdr.close()
                except Exception:
                    pass
