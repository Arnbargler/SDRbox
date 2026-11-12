"""Experimental single-open RTL-SDR GMRS scanner.

RtlSdr remains open across channel hops. A worker owns all USB calls.
The frontend receives the requested frequency and measured relative RF
channel-to-neighbor contrast (NOT calibrated RSSI/dBm).
"""
import math
import subprocess
import threading
import time

CHANNELS = (
    ("GMRS 01", 462562500), ("GMRS 02", 462587500),
    ("GMRS 03", 462612500), ("GMRS 04", 462637500),
    ("GMRS 05", 462662500), ("GMRS 06", 462687500),
    ("GMRS 07", 462712500),
)
SAMPLE_RATE = 1_024_000
CHUNK = 32_768                 # approx 32 ms IQ per read
TUNER_OFFSET = 100_000         # keep desired channel off tuner DC spike
DWELL_SECONDS = 0.38
HANG_SECONDS = 1.0


class PersistentScanner:
    """All SDR calls happen on one thread; callbacks are marshalled by FastAPI."""

    def __init__(self, callback):
        self.callback = callback
        self._stop = threading.Event()
        self._skip = threading.Event()
        self._hold = threading.Event()
        self.thread = None
        self.error = None
        self.squelch = 15
        self._sdr = None
        self._player = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, squelch=15):
        if self.running:
            return
        if not 1 <= squelch <= 100:
            raise ValueError("Squelch must be between 1 and 100")
        self.squelch = squelch
        self.error = None
        self._stop.clear()
        self._skip.clear()
        self._hold.clear()
        self.thread = threading.Thread(target=self._run, name="persistent-gmrs", daemon=True)
        self.thread.start()

    def hold(self):
        self._hold.set()
        self.callback("held", None)

    def resume(self):
        self._hold.clear()
        self.callback("resumed", None)

    def skip(self):
        self._skip.set()

    def stop(self):
        self._stop.set()
        if self.thread is not None and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)
            if self.thread.is_alive():
                # Never close a live SDR from a second thread; let its owner unwind.
                raise RuntimeError("SDR read did not stop within 3 seconds")
        self.thread = None

    def _run(self):
        sdr = None
        player = None
        try:
            import numpy as np
            from scipy.signal import butter, lfilter, resample_poly
            from rtlsdr import RtlSdr

            sdr = RtlSdr(0)
            self._sdr = sdr
            sdr.sample_rate = SAMPLE_RATE
            sdr.gain = 30
            player = subprocess.Popen(
                ["aplay", "-q", "-r", "24000", "-f", "S16_LE", "-c", "1"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, bufsize=0,
            )
            self._player = player
            # Filter voice after frequency discrimination at 64 kHz.
            b, a = butter(3, 3200, fs=64000)
            # FFT mask uses bins of the *original* IQ block to measure
            # narrow-channel power above adjacent-channel noise.
            freqs = np.fft.fftfreq(CHUNK, 1 / SAMPLE_RATE)
            target_mask = np.abs(freqs + TUNER_OFFSET) < 6500
            neighbor_mask = ((np.abs(freqs + TUNER_OFFSET - 30000) < 7000)
                             | (np.abs(freqs + TUNER_OFFSET + 30000) < 7000))
            index = 0
            while not self._stop.is_set():
                channel, hz = CHANNELS[index]
                self._skip.clear()
                sdr.center_freq = hz + TUNER_OFFSET
                # Reset buffer after tuning; ignore old samples from prior channel.
                sdr.read_samples(CHUNK)
                self.callback("tuned", (channel, hz / 1e6))
                entered = time.monotonic()
                last_open = None
                active = False
                prev = None
                phase = 0
                filter_state = np.zeros(max(len(a), len(b)) - 1)
                while not self._stop.is_set() and not self._skip.is_set():
                    iq = np.asarray(sdr.read_samples(CHUNK), dtype=np.complex64)
                    # Centered Welch-like FFT window for relative channel contrast.
                    spectrum = np.abs(np.fft.fft(iq * np.hanning(len(iq)))) ** 2
                    target = float(spectrum[target_mask].mean()) + 1e-12
                    neighbor = float(spectrum[neighbor_mask].mean()) + 1e-12
                    contrast_db = 10 * math.log10(target / neighbor)
                    # Threshold is a NEW experimental RF power-contrast scale.
                    # The previous rtl_fm squelch=15 is NOT equivalent to 5 dB.
                    open_db = 5.0
                    stay_db = 3.0
                    detected = contrast_db >= (stay_db if active else open_db)
                    now = time.monotonic()
                    if detected:
                        last_open = now
                        if not active:
                            active = True
                            self.callback("activity_start", None)
                    elif active and last_open is not None and now - last_open > HANG_SECONDS:
                        active = False
                        self.callback("activity_end", None)
                    # Frequency shift -100 kHz to baseband with continuous phase.
                    n = np.arange(len(iq), dtype=np.float32)
                    rate = -2 * np.pi * TUNER_OFFSET / SAMPLE_RATE
                    mixed = iq * np.exp(1j * (phase + n * rate))
                    phase = float((phase + len(iq) * rate) % (2 * np.pi))
                    narrow = resample_poly(mixed, 1, 16)   # complex, 64 kHz
                    if prev is None:
                        prev = narrow[0]
                    pairs = narrow * np.conjugate(np.concatenate(([prev], narrow[:-1])))
                    prev = narrow[-1]
                    discriminator = np.angle(pairs).astype(np.float32)
                    voice, filter_state = lfilter(b, a, discriminator, zi=filter_state)
                    pcm = resample_poly(voice, 3, 8)     # 24 kHz
                    if active and player.poll() is None:
                        samples = np.int16(np.clip(pcm * 16000, -32767, 32767))
                        try:
                            player.stdin.write(samples.tobytes())
                        except BrokenPipeError as exc:
                            raise RuntimeError("Local ALSA audio player exited") from exc
                    if player.poll() is not None:
                        raise RuntimeError(f"Local ALSA player exited ({player.returncode})")
                    if self._hold.is_set():
                        entered = now  # hold the same frequency indefinitely
                    elif not active and now - entered >= DWELL_SECONDS:
                        break
                if active:
                    self.callback("activity_end", None)
                if self._skip.is_set():
                    self._hold.clear()
                index = (index + 1) % len(CHANNELS)
        except Exception as exc:
            if not self._stop.is_set():
                self.error = f"{type(exc).__name__}: {exc}"
                self.callback("error", self.error)
        finally:
            if player is not None:
                try:
                    player.stdin.close()
                except (OSError, ValueError):
                    pass
                try:
                    player.terminate()
                    player.wait(timeout=1)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    if player.poll() is None:
                        player.kill()
                        player.wait(timeout=1)
            if sdr is not None:
                try:
                    sdr.close()
                except Exception:
                    pass
            self._player = None
            self._sdr = None
