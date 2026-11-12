# SDRbox v0.7 — spectrum-only app

**Only one mode:** live fixed-window FFT capture. No traditional scanner profiles, squelch slider, HOLD/SKIP, audio, or activity logs.

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
