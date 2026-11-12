# SDRbox — handoff (2026-11-11)

**Direction: spectrum-first SDR monitor only.** User explicitly asked to remove all old sequential scanning modes and associated code and redesign the interface around real FFT data. New v0.7 code has been committed but not field-tested on rackio yet.

## Proven hardware & latest test

- rackio.local = Dell OptiPlex 5060 Micro, 8 GB, Linux Mint, NESDR Smart (RTL2832U/R820T), single HDMI-2 1280×400 touchscreen.
- Browser at http://rackio.local:8080. One FastAPI process/one receiver worker.
- Python 3.12, venv ~/.venv; `pyrtlsdr==0.2.91` and `setuptools<82` needed with distro librtlsdr.so.2.
- Previous v0.6 spectrum FFT **was user verified**: actual Channel 1 walkie-talkie RF spike, 2–3 automatic updates/s after removing an obsolete watchdog check.
- v0.7 preserved `sdrbox/spectrum.py` capture/DSP unchanged but rebuilt server and frontend. Field testing is needed.

## Active files

- `sdrbox/spectrum.py` — single persistent RtlSdr; center 462.650 MHz; 2.048 MS/s; 32768 complex samples/read; eight 4096-point FFTs averaged; local percentile floor; 512-point plotted central 1.70 MHz.
- `sdrbox/main.py` — FastAPI, WebSocket FFT snapshots, START/STOP command, health/state endpoints.
- `sdrbox/static/index.html`, `app.js`, `style.css` — one-screen large spectrum canvas, zoom and diagnostics.
- `requirements.txt` — all app/SDR dependencies.

Old `receiver.py`, `scanner.py`, `persistent.py`, `requirements-persistent.txt` removed from current tree. They remain in Git history; do not resurrect them without user direction. No simulation, radio audio or scan banks now.

## Next test

Pull on rackio, activate venv, install requirements, launch Uvicorn. Check Chrome display fits 1280×400, continuous FFT updates, FULL/GMRS zoom, CH1 and CH7 spike location, STOP/restart device cleanup. No automatic candidate detection yet.

## Planned steps

S2 grouping elevated FFT bins into qualified signal candidates above a local noise floor, rejecting artifacts. S3 strongest qualified selection; S4 demodulate selected NFM in same IQ window with rackio local audio; S5 overlapping windows (GMRS 467, AIR AM). Do not infer signal identity from raw maximum bin; no calibrated dBm.

LAN-only, unauthenticated controls; do not expose publicly.
