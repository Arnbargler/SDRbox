# Running SDRbox (S4 baseline)

On `rackio.local`, stop any old Uvicorn process with Ctrl+C; close GQRX and other programs using the RTL-SDR. Then:

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open `http://rackio.local:8080` (or `http://localhost:8080` on rackio). Hard-refresh Chrome with Ctrl+Shift+R after a frontend update. Press **START CAPTURE**; the 462.000–463.300 MHz spectrum and local noise floor should update. FULL WINDOW / GMRS 1–7 are *display zooms*, not tuner changes.

## Controls and what to expect

- **MIN RF CONTRAST:** 8–30 dB, default **+15 dB**. Higher = less sensitive. This is FFT detection threshold, not physical RF gain or classic squelch.
- **GMRS CH1 (462.5625 MHz)** or **CH7 (462.7125 MHz)** PTT: the strongest persistent qualifying signal should become cyan/SELECTED, with local NFM audio on rackio speakers. Audio stays open during the brief HANG interval, then mutes after release.
- **S4 diagnostics:** Gate OPEN/CLOSED, IQ `rate` (captured sample time / elapsed wall time), `R` (mean USB read ms), `P` (cumulative mean NFM processing ms per IQ block), and `lost` (raw audio-IQ blocks rejected because its queue filled). Hover the audio detail for PCM and IQ queue depths and drops.

The receiver runs at **1.536 MS/s**, reads **131072 samples = 85.33 ms** of IQ per block, and produces **2048 signed 16-bit PCM samples = 85.33 ms** at 24 kHz. PCM goes to **local `aplay`**, not browser speakers. The tuner remains fixed at 462.650 MHz.

## Field-tested performance (2026-11-11)

User verified two-minute continuous voice reception **without the earlier rhythmic cuts**. Observed approximately `rate 0.973x`, `R 87.6ms`, `P 7ms` at end of the test, `lost 0`. P rises while transmitting because it is averaged from the beginning of capture; this is **not evidence of a CPU leak**. Rate below 1.00 may still matter in very long sessions.

## Troubleshooting

If sound cuts out again, first inspect SELECTED/HANG and Gate status, IQ rate, R, P, lost blocks, and the audio/IQ queue depths. Do not increase buffers or modify squelch reflexively. Check that ALSA is using the intended speaker, and that `aplay` is installed. Capture errors appear in the UI. STOP then START should release/reopen the USB device.

Keep service on a trusted LAN only. Never port-forward its unauthenticated API.
