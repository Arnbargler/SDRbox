# SDRbox — handoff (2026-11-11)

**Direction: spectrum-first SDR monitor only.** User explicitly asked to remove all old sequential scanning modes and associated code and redesign the interface around real FFT data. v0.8 S2 candidate detection is now committed, **not yet field-tested on rackio**. The user already approved the v0.7 redesigned spectrum-first interface.

## Proven hardware & latest test

- rackio.local = Dell OptiPlex 5060 Micro, 8 GB, Linux Mint, NESDR Smart (RTL2832U/R820T), single HDMI-2 1280×400 touchscreen.
- Browser at http://rackio.local:8080. One FastAPI process/one receiver worker.
- Python 3.12, venv ~/.venv; `pyrtlsdr==0.2.91` and `setuptools<82` needed with distro librtlsdr.so.2.
- Previous v0.6 spectrum FFT **was user verified**: actual Channel 1 walkie-talkie RF spike, 2–3 automatic updates/s after removing an obsolete watchdog check.
- v0.7 preserved `sdrbox/spectrum.py` capture/DSP unchanged but rebuilt server and frontend. Field testing is needed.

## Active files

- `sdrbox/spectrum.py` — single persistent RtlSdr; center 462.650 MHz; 2.048 MS/s; 32768 complex samples/read; eight 4096-point FFTs averaged; local percentile floor; 512-point plotted central 1.70 MHz; includes candidates in snapshots.
- `sdrbox/detector.py` — experimental spectral blob and temporal persistence logic, testable independently of SDR; `tests/test_detector.py` provides offline checks.
- `sdrbox/main.py` — FastAPI, WebSocket FFT snapshots, START/STOP command, health/state endpoints.
- `sdrbox/static/index.html`, `app.js`, `style.css` — one-screen large spectrum canvas, zoom and diagnostics.
- `requirements.txt` — all app/SDR dependencies.

Old `receiver.py`, `scanner.py`, `persistent.py`, `requirements-persistent.txt` removed from current tree. They remain in Git history; do not resurrect them without user direction. No simulation, radio audio or scan banks now.

## Next test

Pull on rackio, activate venv, install requirements, launch Uvicorn. Check Chrome display fits 1280×400, continuous FFT updates, FULL/GMRS zoom, CH1 and CH7 spike location, STOP/restart device cleanup. No automatic candidate detection yet.

## Planned steps

S2 grouping elevated FFT bins into qualified signal candidates above a local noise floor, rejecting artifacts. S3 strongest qualified selection; S4 demodulate selected NFM in same IQ window with rackio local audio; S5 overlapping windows (GMRS 467, AIR AM). Do not infer signal identity from raw maximum bin; no calibrated dBm.

LAN-only, unauthenticated controls; do not expose publicly.

## Current S2 test objective

Run the unit tests and v0.8 spectrum app. Idle spectrum should normally display **zero persistent candidates**, although static spurs may generate false positives. Key GMRS CH1, then CH7; look for amber candidate markers and ~462.5625 / ~462.7125 MHz labels after at least two FFT frames. Detection threshold fixed 10 dB above local percentile baseline; minimum 3 adjacent bins; skips +/-12 kHz center DC and 35 kHz near crop edges. No signal is yet selected, heard or logged as a confirmed hit. Do not confuse a persistent spectral peak with confirmed radio traffic. Preserve 2–3 Hz capture while adding the detector; monitor for slowdown.
