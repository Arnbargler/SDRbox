"""Supervised local rtl_fm -> aplay pipeline for fixed GMRS 1 or GMRS 1–7 scan.

No browser audio, IQ streaming or externally reported channel/activity detection.
"""
import os
import shutil
import signal
import subprocess
import tempfile

GMRS_FREQUENCIES_HZ = (462562500, 462587500, 462612500, 462637500,
                       462662500, 462687500, 462712500)


class LocalGMRSReceiver:
    def __init__(self):
        self.receiver = None
        self.player = None
        self.radio_log = None
        self.audio_log = None

    @property
    def running(self):
        return (self.receiver is not None and self.player is not None
                and self.receiver.poll() is None and self.player.poll() is None)

    def start(self, scan=False, squelch=30):
        if self.running:
            return
        self.stop()
        for binary in ("rtl_fm", "aplay"):
            if shutil.which(binary) is None:
                raise RuntimeError(f"Missing executable: {binary}")
        self.radio_log = tempfile.TemporaryFile(mode="w+t")
        self.audio_log = tempfile.TemporaryFile(mode="w+t")
        if scan and not 1 <= squelch <= 100:
            raise ValueError("Scanning requires squelch 1–100")
        frequencies = GMRS_FREQUENCIES_HZ if scan else GMRS_FREQUENCIES_HZ[:1]
        args = ["rtl_fm", "-d", "0"]
        for frequency in frequencies:
            args.extend(["-f", str(frequency)])
        args.extend(["-M", "fm", "-s", "24000", "-r", "24000",
                     "-g", "30", "-l", str(squelch if scan else 0)])
        if scan:
            args.extend(["-t", "5"])
        try:
            self.receiver = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=self.radio_log,
                start_new_session=True,
            )
            self.player = subprocess.Popen(
                ["aplay", "-r", "24000", "-f", "S16_LE", "-c", "1"],
                stdin=self.receiver.stdout,
                stdout=subprocess.DEVNULL,
                stderr=self.audio_log,
                start_new_session=True,
            )
            # Close parent's copy so aplay sees EOF if rtl_fm exits.
            self.receiver.stdout.close()
        except Exception:
            self.stop()
            raise

    def failure(self):
        if self.running:
            return None
        if self.receiver is None:
            return "Receiver not running"
        codes = (self.receiver.poll(), self.player.poll() if self.player else None)
        messages = []
        for fh in (self.radio_log, self.audio_log):
            if fh is not None:
                fh.flush()
                fh.seek(0)
                messages.append(fh.read()[-600:].strip())
        text = " | ".join(m for m in messages if m)
        return f"Radio/audio process exited {codes}: {text}"[:450]

    def stop(self):
        for process in (self.receiver, self.player):
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for process in (self.receiver, self.player):
            if process is not None:
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=1.0)
                if process.stdout:
                    process.stdout.close()
        self.receiver = None
        self.player = None
        for fh in (self.radio_log, self.audio_log):
            if fh is not None:
                fh.close()
        self.radio_log = None
        self.audio_log = None
