# SDRbox development plan

**Updated 2026-11-08.** Planning phase: no custom server/scanner code is deployed yet.

## Agreed design

- One **1280×400 2U touchscreen** on Linux Mint/rackio; **1U top display removed**. A single Chromium app/fullscreen page shows status and controls.
- Python **FastAPI web server** on rackio with **one authoritative radio scanner engine**, REST commands and WebSocket status.
- Remote LAN browser uses the same application. No PySide6 and no second Chromium kiosk.
- **Local rackio audio first**, browser audio streaming later.
- Approved visual reference: **single-display mockup option #2**, see [UI.md](UI.md).
- Software organized as a modular monolith: core scheduler/state, radio adapter/DSP/audio, web API/UI and config/history.

## Current verified baseline

- Linux Mint and GQRX function with NESDR.
- Broadcast FM and signal activity around 118.800 MHz reported.
- Lower 2U monitor is 1280×400, and touch was accurate when properly mapped in the **former two-display configuration**.
- Upper 1U screen has now been **physically removed**.
- **Unverified after removal:** current XRandR display origin/output, touch accuracy, removal of custom autostart and persistence after reboot.
- No server, scanner engine, custom audio code, or kiosk UI yet exists.

## Milestones

### M0 — Inventory / clean single-screen setup

- Check that obsolete `~/.config/autostart/rackio-touch.desktop` and `~/.local/bin/rackio-touch.sh` are no longer running/installed; user received deletion/reboot steps but completion isn't verified.
- Run `DISPLAY=:0 xrandr --listmonitors`, confirm **one 1280×400** output and touchscreen accuracy at all corners; note actual output/coordinates, do not assume old HDMI-2 offset.
- Inventory CPU/RAM, OS/browser, USB NESDR, audio output, working GQRX AM audio, sample-rate stability.
- Confirm no second kiosk or autostart app tries to use the removed 1U display.

### M1 — First web page and simulated scanner

- Create minimal FastAPI server and **one local 1280×400** touchscreen dashboard; add a responsive remote `/` browser view from same shared frontend.
- Implement approved option #2 styling with five independent bank toggles, frequency/meter, recent hits and SCAN/HOLD/SKIP/SETTINGS.
- Implement authoritative in-memory state, validated commands, WebSocket updates and automatic reconnection/full snapshot.
- Test from rackio and N100 simultaneously; mark simulated data clearly.
- Prove closing the local or remote browser does not stop the backend.

### M2 — First live airband scanner with local audio

- Close GQRX before the scanner opens NESDR. Use an established RTL-SDR receiver/DSP approach.
- Start with confirmed active airband channels, AM decoding, gain, squelch, hang/resume logic, and **rackio speaker output**.
- Integrate real receiver state into web UI, replacing simulated readings in live mode.
- Test the scanner headlessly via SSH; it should work without any browser open.
- Measure retune overhead, signal latency, false squelch events and revisit time.

### M3 — FFT-based wide-window airband discovery

- Benchmark usable NESDR passband at stable capture rate (nominal ~2.4 MS/s, perhaps ~2MHz clean).
- Generate overlapping windows for AIR 118.000–136.975 MHz; ~10 is an initial estimate only.
- Measure noise floor, detect candidate signals, exclude DC/spurs, verify intelligible AM voice and auto pause/resume.
- Compare discovery against known-channel baseline; avoid unnecessary tuner retunes when channel fits existing IQ window.

### M4 — Multiple bank scanning, config and history

- Enable configurable CB / GMRS / AIR / AMB / FIRE definitions and per-channel mode; maintain independent toggles.
- Use YAML/JSON config and SQLite for real hit history; restore enabled banks across restart.
- Show meaningful scan round-trip/revisit delays; do not assume digital/trunked/encrypted emergency traffic can be decoded.

### M5 — Appliance integration

- Auto-start server/engine and **one** Chromium kiosk on the 1280×400 panel. Validate window geometry, touch mapping and graceful power/restart handling on Linux Mint.
- Confirm rackio-local audio works with all browsers closed, with multiple LAN controllers and after client reconnection.
- Handle missing/busy SDR, network errors and audio failure; secure to LAN only.

### M6 — Later improvements

- Browser audio streaming, recordings/favourites, waterfall advanced view.
- RSP1A adapter, remote antenna, rotary control and dedicated speaker.

## Workflow rules

- User directs design decisions and tests on actual rack; work in small, testable commits.
- Prefer standard RTL-SDR/DSP libraries, no reinvention of known radio processing.
- Preserve GQRX as a known-good diagnostic tool, but do not let it compete for the NESDR.
- Do not invent frequencies, signal readings or throughput from concept art.
- Confirm actual XRandR output and touch after physical removal before writing kiosk autostart.
- Proposed `http://rackio.local:8080` is not deployed. Start LAN-only; do not expose public control endpoints.
- Local browser and remote browser are clients of one shared scanner. Local audio v1 does not depend on either browser being open.

## Pending decisions/measurements

Dell specs; active XRandR monitor identity after removal; single-panel touch; actual output speaker; chosen SDR libraries; receiver performance; local frequency channel lists; exact web port and service startup method; browser audio format (later).
