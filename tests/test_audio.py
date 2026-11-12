"""S4 offline audio DSP tests (no RTL dongle or ALSA required)."""
import unittest

import numpy as np

from sdrbox.audio import NfmDemodulator, RF_RATE, silence
from sdrbox.detector import detect_bins


class NfmAudioTests(unittest.TestCase):
    def test_silence_is_exact_rate(self):
        pcm = silence(32768)
        self.assertEqual(len(pcm), 384)
        self.assertEqual(pcm.dtype, np.int16)
        self.assertFalse(np.any(pcm))

    def test_64ms_iq_chunk_produces_64ms_pcm(self):
        # S4 capture now uses 131072 IQ samples per read. Audio duration
        # must remain exact even when the USB read granularity changes.
        count = 131072
        d = NfmDemodulator()
        d.tune(462562500, 462650000, count)
        pcm = d.demodulate(np.zeros(count, dtype=np.complex64))
        self.assertEqual(len(pcm), 1536)
        self.assertEqual(len(silence(count)), 1536)

    def test_demodulator_requires_tuning(self):
        d = NfmDemodulator()
        with self.assertRaises(RuntimeError):
            d.demodulate(np.zeros(32768, np.complex64))

    def test_synthetic_wideband_fm_audio_tone(self):
        # A complex 2.048 MS/s RF stream: CH1 with 2.5 kHz FM deviation
        # modulated by a 1 kHz test tone. No real RF device is required.
        center = 462_650_000
        station = 462_562_500
        frames = []
        d = NfmDemodulator()
        d.tune(station, center, 32768)
        for block in range(12):
            n = block * 32768 + np.arange(32768)
            t = n / RF_RATE
            phase = (2 * np.pi * (station - center) * t
                     + 2500 / 1000 * (1 - np.cos(2 * np.pi * 1000 * t)))
            iq = np.exp(1j * phase).astype(np.complex64)
            frames.append(d.demodulate(iq))
        audio = np.concatenate(frames[4:]).astype(float)
        self.assertGreater(np.sqrt(np.mean(audio * audio)), 100)
        frequency = np.fft.rfftfreq(len(audio), 1 / 24000)
        peak = frequency[np.argmax(np.abs(np.fft.rfft(audio)))]
        self.assertAlmostEqual(peak, 1000, delta=100)

    def test_threshold_parameter_rejects_13db_peak(self):
        n = 4096
        power = np.zeros(n)
        floor = np.zeros(n)
        center = n // 2 - 175
        power[center - 2:center + 3] = [11, 12, 13, 12, 11]
        old = detect_bins(power, floor, 2_048_000, 462_650_000, threshold_db=10)
        new = detect_bins(power, floor, 2_048_000, 462_650_000, threshold_db=15)
        self.assertTrue(old)
        self.assertFalse(new)


if __name__ == "__main__":
    unittest.main()
