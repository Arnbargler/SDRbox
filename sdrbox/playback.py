"""Local PCM playback: buffered writer isolated from SDR capture and FFT CPU work.

PCM is 24 kHz signed 16-bit mono. One bounded queue absorbs short producer
jitter; the writer alone owns aplay stdin. Overlong writer stalls never block
USB reads. Statistics are diagnostic, not audio hardware timestamps.
"""
from collections import deque
import queue
import subprocess
import threading
import time

AUDIO_RATE = 24_000
CHANNELS = 1
SAMPLE_BYTES = 2
PREBUFFER_CHUNKS = 4  # 4 x 85ms chunks ~= 341ms jitter buffer
QUEUE_CAPACITY = 16  # 16 x 85ms chunks ~= 1.37s


class BufferedAudioPlayer:
    def __init__(self, executable="aplay", process_factory=subprocess.Popen):
        self.executable = executable
        self.process_factory = process_factory
        self.process = None
        self.queue = queue.Queue(maxsize=QUEUE_CAPACITY)
        self.stop_event = threading.Event()
        self.writer = None
        self.error = None
        self.sent_chunks = 0
        self.dropped_chunks = 0
        self.writer_gap_max_ms = 0.0
        self.writes_blocked = 0
        self._last_written = None
        self._chunk_ms = 16.0
        self._lock = threading.Lock()
        self._stderr_tail = deque(maxlen=5)

    def start(self):
        if self.writer is not None:
            return
        self.stop_event.clear()
        self.process = self.process_factory(
            [self.executable, "-q", "-r", str(AUDIO_RATE),
             "-f", "S16_LE", "-c", str(CHANNELS),
             "-B", "400000", "-F", "80000"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.writer = threading.Thread(target=self._write_loop, daemon=True, name="rackio-pcm")
        self.writer.start()

    def offer(self, pcm):
        """Nonblocking queue insertion. Retain recent audio if overloaded."""
        if self.writer is None or self.error is not None:
            return
        block = pcm.tobytes() if hasattr(pcm, "tobytes") else bytes(pcm)
        self._chunk_ms = 1000.0 * len(block) / (AUDIO_RATE * CHANNELS * SAMPLE_BYTES)
        try:
            self.queue.put_nowait(block)
        except queue.Full:
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                pass
            with self._lock:
                self.dropped_chunks += 1
            try:
                self.queue.put_nowait(block)
            except queue.Full:
                with self._lock:
                    self.dropped_chunks += 1

    def stats(self):
        with self._lock:
            return {
                "queued_ms": round(self.queue.qsize() * self._chunk_ms, 0),
                "written_chunks": self.sent_chunks,
                "dropped_chunks": self.dropped_chunks,
                "max_writer_gap_ms": round(self.writer_gap_max_ms, 1),
                "slow_writes": self.writes_blocked,
                "error": self.error,
            }

    def _write_loop(self):
        try:
            # Initial jitter buffer: the capture thread is just starting and
            # FFT/USB startup should not immediately starve ALSA.
            while self.queue.qsize() < PREBUFFER_CHUNKS and not self.stop_event.is_set():
                if self.process.poll() is not None:
                    raise RuntimeError(f"aplay exited: {self.process.returncode}")
                time.sleep(0.005)
            while not self.stop_event.is_set():
                try:
                    chunk = self.queue.get(timeout=0.06)
                except queue.Empty:
                    if self.process.poll() is not None:
                        raise RuntimeError(f"aplay exited: {self.process.returncode}")
                    continue
                try:
                    now = time.monotonic()
                    if self._last_written is not None:
                        with self._lock:
                            self.writer_gap_max_ms = max(
                                self.writer_gap_max_ms,
                                (now - self._last_written) * 1000,
                            )
                    started = time.monotonic()
                    self.process.stdin.write(chunk)
                    duration = time.monotonic() - started
                    with self._lock:
                        self.sent_chunks += 1
                        if duration > 0.04:
                            self.writes_blocked += 1
                    self._last_written = time.monotonic()
                finally:
                    self.queue.task_done()
        except (OSError, ValueError, RuntimeError) as exc:
            with self._lock:
                self.error = f"{type(exc).__name__}: {exc}"

    def stop(self):
        self.stop_event.set()
        if self.process is not None:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
            except (OSError, ValueError):
                pass
            if self.process.poll() is None:
                self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1)
        if self.writer is not None:
            self.writer.join(timeout=1)
        if self.process is not None and self.process.stderr is not None:
            self.process.stderr.close()
        self.writer = None
        self.process = None
