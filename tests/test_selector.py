"""S3 selector tests: run python -m unittest discover -s tests."""
import unittest

from sdrbox.selector import SignalSelector


def candidate(mhz, strength=20.0, stable=True):
    return {
        "frequency_mhz": mhz,
        "contrast_db": strength,
        "width_khz": 8.0,
        "seen_frames": 2 if stable else 1,
        "provisional": not stable,
    }


class SelectorTests(unittest.TestCase):
    def test_does_not_select_provisional(self):
        s = SignalSelector()
        result = s.update([candidate(462.5625, stable=False)], 0.0)
        self.assertEqual(result["status"], "SEARCHING")
        self.assertIsNone(result["frequency_mhz"])

    def test_initial_strongest_qualified(self):
        s = SignalSelector()
        result = s.update([candidate(462.5625, 14), candidate(462.7125, 22)], 0.0)
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["frequency_mhz"], 462.7125)

    def test_no_preemption_by_stronger_neighbor(self):
        s = SignalSelector()
        s.update([candidate(462.5625, 18)], 0.0)
        result = s.update([candidate(462.5625, 12), candidate(462.7125, 35)], 0.4)
        self.assertEqual(result["frequency_mhz"], 462.5625)
        self.assertEqual(result["status"], "SELECTED")

    def test_short_dropout_and_release(self):
        s = SignalSelector(release_seconds=1.2)
        s.update([candidate(462.5625)], 10.0)
        result = s.update([], 10.8)
        self.assertEqual(result["status"], "HANG")
        self.assertGreater(result["release_remaining_s"], 0)
        result = s.update([], 11.21)
        self.assertEqual(result["status"], "SEARCHING")
        self.assertIsNone(result["frequency_mhz"])

    def test_reacquisition_cancels_release(self):
        s = SignalSelector(release_seconds=1.2)
        s.update([candidate(462.5625)], 10)
        s.update([], 10.8)
        result = s.update([candidate(462.5635)], 10.9)
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["frequency_mhz"], 462.5625)
        self.assertEqual(result["last_detected_mhz"], 462.5635)

    def test_competitor_only_after_selected_releases(self):
        s = SignalSelector(release_seconds=1.2)
        s.update([candidate(462.5625)], 10)
        self.assertEqual(s.update([candidate(462.7125, 30)], 10.3)["status"], "HANG")
        result = s.update([candidate(462.7125, 30)], 11.3)
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["frequency_mhz"], 462.7125)

    def test_reset_clears_selection(self):
        s = SignalSelector()
        s.update([candidate(462.5625)], 0)
        s.reset()
        self.assertEqual(s.update([], 1.0)["status"], "SEARCHING")

    def test_audio_remains_disabled(self):
        s = SignalSelector()
        self.assertFalse(s.update([candidate(462.5625)], 0)["audio_active"])


if __name__ == "__main__":
    unittest.main()
