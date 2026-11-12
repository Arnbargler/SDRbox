# SDRbox — next AI/developer handoff

**As of 2026-11-11 — READ THIS FIRST.**

## One-sentence objective

Build a **spectrum-first receive-only scanner** that captures overlapping approximately 2 MHz SDR spectrum windows, detects qualified peaks above the **local noise floor**, selects a signal (initially strongest qualified), and demodulates it. **Do not keep treating conventional sequential channel hopping as the final product.**

## Do not code yet

The user subsequently authorized **S1 spectrum visibility**. A spectrum-only v0.6 implementation has now been committed and is **awaiting the first rackio test**. Do not start S2 candidate selection until S1 IQ/FFT output is validated.

## Current machine, proven behaviour

- `rackio.local`: Dell OptiPlex 5060 Micro, **8 GB RAM**, **Linux Mint**, one NooElec NESDR Smart (RTL2832U, R820T).
- One working **HDMI-2 1280×400 +0+0 touchscreen**; upper 1U monitor and its old XInput setup removed.
- Normal Chrome browser locally or over LAN at `http://rackio.local:8080`; FastAPI + WebSocket backend; audio **only on rackio**. No mandatory kiosk or remote browser audio.
- `MANAGED_1_7` Python/`rtl_fm` scanner field-tested: CH1/3/7 frequency display correct, live GMRS NFM reception, automatically resumes after PTT; ~**1 channel/s**.
- `SCAN_1_7` native `rtl_fm` scan also field-tested; squelch **15** useful under current conditions.
- `FIXED_1` radio and `SDRBOX_RECEIVER=sim` simulator retained.
- `PERSISTENT_1_7` (`sdrbox/persistent.py`, `pyrtlsdr`) starts and retunes at ~**3 channels/s** after resolving Python library mismatch. **No explicit separate validation yet of persistent NFM voice quality/detection.** It still retunes one channel at a time, not chunk-based.
- Current backend defaults to `PERSISTENT_1_7` and scans GMRS 1–7; live signal meter is not calibrated RF signal strength.

## Version/API and dependencies

- `sdrbox/main.py`: FastAPI v0.5, REST/WS commands and scanner state.
- `sdrbox/persistent.py`: single-open RTL-SDR + basic in-process NFM/FFT RF contrast, sequential 1–7 hops.
- `sdrbox/scanner.py`: working Python-managed `rtl_fm` fallback, per-frequency subprocess.
- `sdrbox/receiver.py`: fixed CH1 and native multi-frequency `rtl_fm` fallback.
- `sdrbox/static/`: current single-screen dark charcoal/green UI. Visual reference `assets/scanner-mockup-option-2.webp`.
- Python venv: `~/.venv` on rackio (NOT necessarily `~/SDRbox/.venv`).
- `requirements-persistent.txt` pins **`pyrtlsdr==0.2.91`** and **`setuptools<82`**, compatible with distro `librtlsdr.so.2` after initially seeing missing `rtlsdr_set_dithering`. Keep system library intact.
- Single Uvicorn worker; close GQRX/other SDR processes before running.

## New architecture decisions

- Target **single capture showing all GMRS 1–7 channels concurrently** (462.5625–462.7125 MHz) before broader coverage.
- Estimate noise floor **locally by frequency**; filter DC spikes, edge artifacts, stable interferers; group bins into signal candidates; confirm persistence.
- **Strongest qualifying candidate first**; future policies selectable.
- Keep in-window FFT observation going while demodulating, where feasible; no promise to observe different 462 and 467 MHz windows simultaneously on one receiver.
- Distinguish FFT window/tuner center, candidate center, selected audio channel, and measured signal contrast in state/UI.
- Actual clean usable MHz/passband and optimal sample rate require field measurement; plan overlapping windows, not assumed perfect 2 MHz.
- First audio output is **rackio-local**, not browser stream.
- Do not invent dBm, frequencies or real hits from demo/UI values.

## What next

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) and [DEVELOPMENT.md](DEVELOPMENT.md). These are the authoritative plan and milestones.
2. When user says to implement S1, add **one-window 462 MHz FFT diagnostics** using single-open device, preserving the existing functional profiles. Prefer a small test that exposes true spectrum/noise/peaks before adding automatic selection.
3. Test on real rackio hardware, observe CPU/spectrum/false peaks, then advance to S2 candidate detector and S3 demod/audio.
4. Keep project small and clear: user likes brief steps and verified incremental changes. Don't automatically add frameworks, Docker, kiosk, network audio or multiple SDRs.

**Repository:** https://github.com/Arnbargler/SDRbox. **Security:** trusted LAN prototype only, unauthenticated controls; do not expose to WAN.

## v0.6 S1 ready for hardware test

`sdrbox/spectrum.py` owns a single RTL device centered on 462.650 MHz at 2.048 MS/s and emits FFT/noise arrays for a nominal 461.800–463.500 MHz center crop. Right UI pane offers full-window and GMRS zoom. INFO profile `SPECTRUM_462` is only a diagnostic FFT visualization: **no audio, hits, carrier qualification or scanning other windows**. Prior `PERSISTENT_1_7`, `MANAGED_1_7`, `SCAN_1_7` and `FIXED_1` preserved. Next test: silent baseline, CH1 and CH7 walkie-talkie peaks, CPU update responsiveness, STOP cleanup. See RUNNING.md.

## Spectrum FFT first field test and fix — 2026-11-11

User saw real CH1 peak when transmitting, confirming FFT RF capture/tuning, but graph appeared frozen after initial snapshot. Identified watchdog bug in main.py: legacy rtl_fm check incorrectly marked spectrum mode ERROR after ~1 second. Fix constrains rtl_fm watchdog to old receiver profiles and monitors spectrum thread separately. **Awaiting field re-test for automatic live refresh**; no new DSP/selection code added.
