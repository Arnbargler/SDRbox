"""Python-owned GMRS scan scheduler, using rtl_fm for single-channel NFM.

One rtl_fm child per channel: prioritizes channel attribution over retune speed.
Activity is inferred from nonzero squelched PCM or a lack of further audio.
"""
import os
import select
import shutil
import signal
import subprocess
import threading
import time

CHANNELS = (
    ("GMRS 01", 462562500), ("GMRS 02", 462587500),
    ("GMRS 03", 462612500), ("GMRS 04", 462637500),
    ("GMRS 05", 462662500), ("GMRS 06", 462687500),
    ("GMRS 07", 462712500),
)


class ManagedScanner:
    def __init__(self, callback):
        self.callback = callback
        self._stop = threading.Event()
        self._skip = threading.Event()
        self._hold = threading.Event()
        self.thread = None
        self.radio = None
        self.player = None
        self.error = None
        self.squelch = 15

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, squelch=15):
        if self.running:
            return
        for name in ("rtl_fm", "aplay"):
            if not shutil.which(name):
                raise RuntimeError(f"{name} is not installed")
        if not 1 <= squelch <= 100:
            raise ValueError("Squelch must be 1–100")
        self.squelch = squelch
        self.error = None
        self._stop.clear()
        self._skip.clear()
        self._hold.clear()
        self.thread = threading.Thread(target=self._run, daemon=True, name="gmrs-scanner")
        self.thread.start()

    @staticmethod
    def _terminate(proc):
        if proc is None:
            return
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=0.65)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=0.65)
        if proc.stdout:
            proc.stdout.close()
        if proc.stdin:
            proc.stdin.close()

    def stop(self):
        self._stop.set()
        self._terminate(self.radio)
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=3)
        self._terminate(self.player)
        self.radio = self.player = None
        self.thread = None

    def skip(self):
        self._skip.set()

    def hold(self):
        self._hold.set()
        self.callback("held", None)

    def resume(self):
        self._hold.clear()
        self.callback("resumed", None)

    def _run(self):
        index = 0
        try:
            self.player = subprocess.Popen(
                ["aplay", "-q", "-r", "24000", "-f", "S16_LE", "-c", "1"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, start_new_session=True, bufsize=0,
            )
            while not self._stop.is_set():
                channel, frequency = CHANNELS[index]
                self._skip.clear()
                self.radio = subprocess.Popen(
                    ["rtl_fm", "-d", "0", "-f", str(frequency),
                     "-M", "fm", "-s", "24000", "-r", "24000",
                     "-g", "30", "-l", str(self.squelch), "-t", "5"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    start_new_session=True, bufsize=0,
                )
                self.callback("tuned", (channel, frequency / 1_000_000))
                # One channel at a time. The 0.8s dwell starts on tuning.
                deadline = time.monotonic() + 0.8
                last_signal_at = None
                active = False
                hang_seconds = 1.1
                while not self._stop.is_set() and not self._skip.is_set():
                    if self.radio.poll() is not None:
                        raise RuntimeError(f"rtl_fm exited on {channel}: {self.radio.returncode}")
                    if self.player.poll() is not None:
                        raise RuntimeError("Local aplay process exited")
                    ready, _, _ = select.select([self.radio.stdout], [], [], 0.12)
                    if ready:
                        audio = os.read(self.radio.stdout.fileno(), 4096)
                        if not audio:
                            raise RuntimeError(f"No audio from rtl_fm on {channel}")
                        try:
                            self.player.stdin.write(audio)
                        except (BrokenPipeError, OSError) as exc:
                            raise RuntimeError("Local speaker output failed") from exc
                        # rtl_fm emits zero PCM on closed squelch in single-frequency mode.
                        # Ignore tiny nonzero samples to tolerate codec/settling artifacts.
                        samples = memoryview(audio[:len(audio) & ~1]).cast("h")
                        signal_open = any(abs(v) > 50 for v in samples[::8])
                        if signal_open:
                            last_signal_at = time.monotonic()
                            if not active:
                                active = True
                                self.callback("activity_start", None)
                    # On some rtl_fm builds, closed squelch stops writing PCM
                    # entirely rather than writing zero samples. Check elapsed
                    # wall time even when select() receives NO audio bytes.
                    if active and last_signal_at is not None and time.monotonic() - last_signal_at >= hang_seconds:
                        active = False
                        self.callback("activity_end", None)
                    if self._hold.is_set():
                        deadline = time.monotonic() + 0.8
                    elif not active and time.monotonic() >= deadline:
                        break
                if active:
                    self.callback("activity_end", None)
                self._terminate(self.radio)
                self.radio = None
                if self._skip.is_set():
                    self._hold.clear()
                index = (index + 1) % len(CHANNELS)
        except Exception as exc:
            if not self._stop.is_set():
                self.error = str(exc)
                self.callback("error", self.error)
        finally:
            self._terminate(self.radio)
            self._terminate(self.player)
            self.radio = self.player = None
