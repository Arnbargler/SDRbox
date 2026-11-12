"""Offline S2 candidate detector tests. Run: python -m unittest discover -s tests."""
import unittest
import numpy as np

from sdrbox.detector import CandidateTracker, detect_bins

N = 4096
FS = 2_048_000
CENTER = 462_650_000


def measured_peaks(*offset_hz):
    power = np.zeros(N, dtype=float)
    floor = np.zeros(N, dtype=float)
    for hz in offset_hz:
        center_bin = round(hz / (FS / N)) + N // 2
        for delta, height in [(-2, 12), (-1, 17), (0, 24), (1, 17), (2, 12)]:
            power[center_bin + delta] = height
    return power, floor


class S2Tests(unittest.TestCase):
    def test_single_realistic_blob(self):
        power, floor = measured_peaks(-87_500)  # GMRS CH1
        found = detect_bins(power, floor, FS, CENTER)
        self.assertEqual(len(found), 1)
        self.assertAlmostEqual(found[0]["frequency_mhz"], 462.5625, delta=0.001)
        self.assertGreater(found[0]["contrast_db"], 20)

    def test_two_simultaneous_candidates(self):
        power, floor = measured_peaks(-87_500, 62_500)  # CH1 / CH7
        found = detect_bins(power, floor, FS, CENTER)
        self.assertEqual(len(found), 2)
        self.assertAlmostEqual(found[0]["frequency_mhz"], 462.5625, delta=0.001)
        self.assertTrue(any(abs(c["frequency_mhz"] - 462.7125) < 0.001 for c in found))

    def test_isolated_impulse_and_dc_rejected(self):
        power, floor = measured_peaks(0)
        power[3000] = 50  # lone spurious bin, not a signal blob
        self.assertEqual(detect_bins(power, floor, FS, CENTER), [])

    def test_temporal_confirmation_and_reset(self):
        power, floor = measured_peaks(-87_500)
        found = detect_bins(power, floor, FS, CENTER)
        tracker = CandidateTracker()
        self.assertTrue(tracker.update(found)[0]["provisional"])
        self.assertFalse(tracker.update(found)[0]["provisional"])
        tracker.reset()
        self.assertTrue(tracker.update(found)[0]["provisional"])

    def test_below_threshold_ignored(self):
        power, floor = measured_peaks(-87_500)
        self.assertEqual(detect_bins(power * 0.25, floor, FS, CENTER), [])


if __name__ == "__main__":
    unittest.main()
