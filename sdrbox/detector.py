"""S2 experimental spectrum candidates; no audio or confirmed-transmission claims.

Pure NumPy/SciPy code, intentionally separate from SDR hardware I/O so the
threshold/temporal behaviour can be tested with synthetic FFT measurements.
"""
from collections import deque

import numpy as np
from scipy.ndimage import binary_closing, label

OPEN_DB = 10.0                  # experimental contrast above local floor
MIN_WIDTH_BINS = 3              # three adjacent bins at the active FFT resolution
MAX_WIDTH_HZ = 45_000          # wideband interference not an NFM candidate
MAX_CANDIDATES = 8
DC_GUARD_HZ = 12_000
EDGE_GUARD_HZ = 35_000
USABLE_HALF_WIDTH_HZ = 650_000  # matches displayed 1.3 MHz FFT crop
MATCH_HZ = 8_000
STABLE_FRAMES = 2               # seen in two of latest three FFT updates
HISTORY_FRAMES = 3


def detect_bins(power_db, floor_db, sample_rate_hz, center_hz, threshold_db=OPEN_DB):
    """Find coarse RF blobs in an already-averaged, fftshifted power spectrum.

    Centers/widths are rough FFT estimates, not tuned or decoded voice.
    """
    power = np.asarray(power_db, dtype=np.float64)
    floor = np.asarray(floor_db, dtype=np.float64)
    if power.ndim != 1 or power.shape != floor.shape or len(power) < 128:
        raise ValueError("Expected equal one-dimensional FFT power and floor arrays")
    n = len(power)
    resolution = sample_rate_hz / n
    offsets = (np.arange(n) - n // 2) * resolution
    usable = (np.abs(offsets) <= USABLE_HALF_WIDTH_HZ - EDGE_GUARD_HZ) & (np.abs(offsets) >= DC_GUARD_HZ)
    contrast = power - floor
    above = usable & np.isfinite(contrast) & (contrast >= threshold_db)
    # Join only one-bin gaps between elevated bins; longer gaps split signals.
    joined = binary_closing(above, structure=np.ones(3, dtype=bool))
    joined &= usable
    components, count = label(joined)
    results = []
    for component in range(1, count + 1):
        ix = np.flatnonzero(components == component)
        if len(ix) < MIN_WIDTH_BINS:
            continue
        width_hz = len(ix) * resolution
        if width_hz > MAX_WIDTH_HZ:
            continue
        # Use the highest FFT bin for center rather than a smeared group mean.
        peak_index = int(ix[np.argmax(contrast[ix])])
        strength = float(np.max(contrast[ix]))
        if not np.isfinite(strength):
            continue
        results.append({
            "frequency_mhz": round((center_hz + offsets[peak_index]) / 1e6, 5),
            "width_khz": round(width_hz / 1000, 1),
            "contrast_db": round(strength, 1),
            "provisional": True,
        })
    results.sort(key=lambda c: c["contrast_db"], reverse=True)
    return results[:MAX_CANDIDATES]


class CandidateTracker:
    """Temporal confirmation: 2/3 successive displayed FFT frames.

    Repeated detection is NOT verification of modulation, intelligibility,
    legality, or even a true over-the-air transmitter (a spur can persist).
    """

    def __init__(self):
        self.history = deque(maxlen=HISTORY_FRAMES)

    def update(self, candidates):
        current = [dict(c) for c in candidates]
        for candidate in current:
            f = candidate["frequency_mhz"]
            distinct_frames = sum(
                any(abs(f - prior["frequency_mhz"]) <= MATCH_HZ / 1e6 for prior in frame)
                for frame in self.history
            )
            candidate["seen_frames"] = min(STABLE_FRAMES, distinct_frames + 1)
            candidate["provisional"] = candidate["seen_frames"] < STABLE_FRAMES
        self.history.append(current)
        return current

    def reset(self):
        self.history.clear()
