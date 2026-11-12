"""S2 diagnostic: single-window FFT spectrum and experimental RF candidates.

No demodulation, activity events, hit logs, automatic tuning or playback.
All USB access belongs to one worker thread, as in persistent.py.
"""
import threading
import time

import numpy as np
from scipy.ndimage import percentile_filter
from rtlsdr import RtlSdr

from .detector import CandidateTracker, detect_bins

CENTER_HZ = 462_650_000
SAMPLE_RATE = 2_048_000
READ_SIZE = 32_768
FFT_SIZE = 4096
POINTS = 512
# Deliberately use the center 1.7 MHz of the 2.048 MHz capture.
USABLE_HZ = 1_700_000
UPDATE_SECONDS = 0.35


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

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self.error = None
        self.tracker.reset()
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
        try:
            sdr = RtlSdr(0)
            sdr.sample_rate = SAMPLE_RATE
            sdr.center_freq = CENTER_HZ
            sdr.gain = 30
            # Discard the initial buffer while the tuner settles.
            sdr.read_samples(READ_SIZE)
            last = 0
            while not self._stop.is_set():
                iq = sdr.read_samples(READ_SIZE)
                if time.monotonic() - last < UPDATE_SECONDS:
                    continue
                # Reuse the SAME averaged FFT and local floor for spectrum and
                # detection; do not double the CPU load each refresh.
                result, power, floor = analyze(iq, return_bins=True)
                candidates = detect_bins(power, floor, SAMPLE_RATE, CENTER_HZ)
                result["candidates"] = self.tracker.update(candidates)
                result["candidate_threshold_db"] = 10.0
                result["candidate_method"] = "experimental_fft_contrast_2_of_3"
                self.callback("spectrum", result)
                last = time.monotonic()
        except Exception as exc:
            if not self._stop.is_set():
                self.error = f"{type(exc).__name__}: {exc}"
                self.callback("spectrum_error", self.error)
        finally:
            if sdr is not None:
                try:
                    sdr.close()
                except Exception:
                    pass
