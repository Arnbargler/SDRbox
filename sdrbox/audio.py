"""S4 narrow-FM audio extraction from a selected subchannel of wideband IQ.

One owner feeds IQ chunks in sample order. Tuning remains fixed; the channel
is mixed and filtered digitally. PCM is 24 kHz mono signed 16-bit for aplay.
"""
import numpy as np
from scipy.signal import butter, resample_poly, sosfilt

RF_RATE = 2_048_000
AUDIO_RATE = 24_000
MIX_RATE = 64_000
DECIMATE = RF_RATE // MIX_RATE  # 32


class NfmDemodulator:
    def __init__(self):
        self._n = None
        self._osc = None
        self._block_step = None
        self._block_phase = 1.0 + 0j
        self._frequency = None
        self._previous = None
        self._sos = butter(3, [250, 3200], btype="bandpass", fs=MIX_RATE, output="sos")
        self._zi = np.zeros((len(self._sos), 2), dtype=np.float64)

    def tune(self, selected_hz, center_hz, block_size):
        """Reset state only when the selected channel or IQ chunk size changes."""
        key = (int(selected_hz), int(center_hz), int(block_size))
        if key == self._frequency:
            return
        offset = key[0] - key[1]
        n = np.arange(block_size, dtype=np.float64)
        self._osc = np.exp(-2j * np.pi * offset * n / RF_RATE).astype(np.complex64)
        self._block_step = np.exp(-2j * np.pi * offset * block_size / RF_RATE)
        self._block_phase = 1.0 + 0j
        self._previous = None
        self._zi[:] = 0
        self._frequency = key

    def reset(self):
        self._frequency = None
        self._previous = None

    def demodulate(self, iq):
        """Returns mono 24 kHz signed PCM, with sample count tied to IQ input."""
        if self._frequency is None:
            raise RuntimeError("NFM demodulator is not tuned")
        mixed = np.asarray(iq, dtype=np.complex64) * self._osc * self._block_phase
        self._block_phase *= self._block_step
        reduced = resample_poly(mixed, 1, DECIMATE).astype(np.complex64)
        if self._previous is None:
            self._previous = reduced[0]
        prev = np.concatenate(([self._previous], reduced[:-1]))
        discriminator = np.angle(reduced * np.conj(prev)).astype(np.float32)
        self._previous = reduced[-1]
        voice, self._zi = sosfilt(self._sos, discriminator, zi=self._zi)
        audio = resample_poly(voice, 3, 8)  # 64 kHz -> 24 kHz
        return np.clip(audio * 25000, -32767, 32767).astype(np.int16)


def silence(sample_count):
    # 2.048 MHz IQ -> 24 kHz PCM; exactly 384 samples for 32768 IQ.
    return np.zeros(round(sample_count * AUDIO_RATE / RF_RATE), dtype=np.int16)
