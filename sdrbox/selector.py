"""S3 selection policy for provisional RF candidates, independent of hardware.

Locks strongest *persistent* candidate. A competing peak never preempts a
current selection. Short losses do not reset its frequency; a release timeout
returns to SEARCHING. This is not a demodulator or proof of real transmissions.
"""
from .detector import MATCH_HZ

RELEASE_SECONDS = 1.2


class SignalSelector:
    def __init__(self, release_seconds=RELEASE_SECONDS):
        if release_seconds < 0:
            raise ValueError("release_seconds must be non-negative")
        self.release_seconds = release_seconds
        self.reset()

    def reset(self):
        self._selected = None
        self._last_seen = None

    def update(self, candidates, now, hold_candidates=None):
        """Process an FFT frame and return a JSON-serializable selection state.

        now is monotonic seconds supplied by the caller for reliable timeout
        behaviour, independent of system wall-clock corrections.
        """
        stable = [
            c for c in candidates
            if not c.get("provisional", True) and c.get("seen_frames", 0) >= 2
        ]
        if self._selected is not None:
            chosen_hz = self._selected["frequency_mhz"] * 1e6
            # Existing locks use lower-threshold, possibly provisional
            # evidence; only NEW locks require two-frame confirmation.
            # A voice-modulated FM carrier is not guaranteed to have the
            # same 3-bin shape on every 350 ms FFT snapshot.
            evidence = hold_candidates if hold_candidates is not None else candidates
            matches = [
                c for c in evidence
                if abs(c["frequency_mhz"] * 1e6 - chosen_hz) <= MATCH_HZ
            ]
            if matches:
                best = max(matches, key=lambda c: c["contrast_db"])
                self._last_seen = now
                # Do not move the selected center on each FFT frame: it would
                # produce a jittering target for future NFM demodulation.
                self._selected["contrast_db"] = best["contrast_db"]
                self._selected["width_khz"] = best["width_khz"]
                self._selected["last_detected_mhz"] = best["frequency_mhz"]
                return self._snapshot("SELECTED", now)
            if now - self._last_seen < self.release_seconds:
                return self._snapshot("HANG", now)
            self.reset()

        if stable:
            best = max(stable, key=lambda c: c["contrast_db"])
            self._selected = {
                "frequency_mhz": best["frequency_mhz"],
                "last_detected_mhz": best["frequency_mhz"],
                "contrast_db": best["contrast_db"],
                "width_khz": best["width_khz"],
            }
            self._last_seen = now
            return self._snapshot("SELECTED", now)
        return self._snapshot("SEARCHING", now)

    def _snapshot(self, status, now):
        if self._selected is None:
            return {
                "status": status, "frequency_mhz": None,
                "contrast_db": None, "width_khz": None,
                "last_detected_mhz": None, "release_remaining_s": 0.0,
                "audio_active": False,
            }
        remaining = max(0.0, self.release_seconds - (now - self._last_seen))
        return {
            "status": status,
            **self._selected,
            "release_remaining_s": round(remaining, 2) if status == "HANG" else 0.0,
            "audio_active": False,
        }
