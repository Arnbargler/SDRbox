# SDRbox v0.8 — spectrum + candidate visualization

**Only one mode:** live fixed-window FFT capture with experimental spectral candidates. No traditional scanner profiles, squelch slider, HOLD/SKIP, audio, or activity logs.

Stop any old Uvicorn server with Ctrl+C, and close GQRX or other radio apps. Then on rackio:

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m pip install -r requirements.txt
python -m compileall -q sdrbox
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open http://rackio.local:8080 in Chrome, hard-refresh (Ctrl+Shift+R), press **START CAPTURE**. The large plot should update ~2–3 times per second. Toggle FULL WINDOW / GMRS 1–7 to change the *displayed* range, without retuning the SDR. Talkie CH1 (462.5625) and CH7 (462.7125) should create distinct peaks. Press STOP CAPTURE and verify restart works.

## What the visualization means

- Tuner center **462.650 MHz**; 2.048 MS/s IQ. FFT plot is an approximately 1.70 MHz center crop.
- Green = uncalibrated relative FFT power; amber = local 25th-percentile estimated noise.
- Dashed markers denote GMRS 1–7 frequency centers.
- Right-hand panel strongest-bin readout is **unqualified**. It can be a spur/noise, not necessarily voice or an actual channel.
- No signals are automatically selected; no audio or real activity hits.

## Python compatibility

Keep rackio's system librtlsdr.so.2. `requirements.txt` pins `pyrtlsdr==0.2.91` and `setuptools<82`; newer wrapper triggered `undefined symbol: rtlsdr_set_dithering` on this machine.

Trusted LAN only. Do not port-forward this unauthenticated service.

## Test S2 candidates

Before starting the server or with the venv active, run `python -m unittest discover -s tests` for offline synthetic-spectrum detector checks. With the live FFT running, the diagnostics column shows **S2 SPECTRAL CANDIDATES**, listing up to two persistent peaks. Amber solid markers on the graph indicate persistent peaks; dim dashed markers indicate provisional detections. Try idle antenna (look for spurious peaks), then PTT on CH1 and CH7 for at least one second each. Compare displayed estimates to 462.5625 and 462.7125 MHz. Notice how quickly each candidate appears after PTT and disappears after release.

These are **experimental candidates**, not voice/GMRS classification. The detector uses a 10 dB peak-to-local-noise threshold and 2-of-3 FFT-frame persistence, excluding a +/-12 kHz center DC region. A constant interference spur can pass that filter; idle false positives are expected to guide refinement. No audio, squelch or automatic selection yet. If the update rate drops below the previously observed ~2–3 frames/s, report it.
