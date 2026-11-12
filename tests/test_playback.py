"""Buffered PCM writer tests without ALSA or RTL-SDR hardware."""
import io
import time
import unittest

from sdrbox.playback import BufferedAudioPlayer


class FakeStream:
    def __init__(self):
        self.bytes_written = 0
        self.closed = False

    def write(self, chunk):
        self.bytes_written += len(chunk)
        return len(chunk)

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self):
        self.stdin = FakeStream()
        self.stderr = io.BytesIO()
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = 0

    def kill(self):
        self.returncode = -9

    def wait(self, timeout=None):
        self.returncode = 0 if self.returncode is None else self.returncode
        return self.returncode


class PlaybackTests(unittest.TestCase):
    def test_buffers_pcm_in_background(self):
        proc = FakeProcess()
        player = BufferedAudioPlayer(process_factory=lambda *args, **kwargs: proc)
        player.start()
        try:
            for _ in range(20):
                player.offer(bytes(768))  # 16 ms at 24 kHz S16 mono
            deadline = time.monotonic() + 1
            while player.stats()["written_chunks"] < 10 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertGreaterEqual(player.stats()["written_chunks"], 10)
            self.assertIsNone(player.stats()["error"])
            self.assertGreater(proc.stdin.bytes_written, 0)
        finally:
            player.stop()

    def test_offer_does_not_block_when_queue_full(self):
        player = BufferedAudioPlayer()
        # No audio worker consuming the queue: enqueue data directly to force
        # full capacity, then enable the offer path with a dummy sentinel.
        player.writer = object()
        for _ in range(player.queue.maxsize):
            player.queue.put_nowait(bytes(768))
        started = time.monotonic()
        player.offer(bytes(768))
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertGreaterEqual(player.stats()["dropped_chunks"], 1)
        player.writer = None


if __name__ == "__main__":
    unittest.main()
