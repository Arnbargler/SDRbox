# SDRbox current milestone — 2026-11-11

**M0 completed:** legacy dual-display startup references removed; reboot and accurate 1280×400 HDMI-2 +0+0 touch confirmed. Dell OptiPlex 5060 Micro, 8 GB; Python 3.12.3.

**M1 implemented in repo, not yet tested on rackio:** FastAPI, state API, WebSocket, responsive UI, GMRS-default simulation. See [RUNNING.md](RUNNING.md). No live SDR or audio. Test in full Chrome/Chromium browser locally and remotely, no forced kiosk/headless mode.

**M2 next:** establish true GMRS NFM reception using walkie-talkie to stimulate a known channel, with local rackio audio, then squelch/hold/resume/channel scanning. Airband AM work follows GMRS. No network audio yet.

---

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


## Rackio bring-up verified — 2026-11-11

- User successfully cloned SDRbox, installed Python dependencies in a virtual environment, and launched the FastAPI simulator. The web UI **looks and functions well** in a real browser; this is a user-observed acceptance test, not an automated test. Shared state across *two simultaneous browsers* has not been explicitly confirmed yet.
- `rtl_test` and `rtl_fm` available under `/usr/bin`. `rtl_test -t` found one Realtek RTL2838UHIDIR device (SN 00000001), Rafael Micro R820T tuner and 29 manual gain options (0–49.6 dB); selected test sampling rate 2.048 MS/s. See [HARDWARE.md](HARDWARE.md) for complete output and interpretation. “No E4000 tuner found” is expected for this R820T; PLL warning remains to be checked during real tuning if persistent.
- **Next milestone:** prove a live GMRS walkie-talkie signal using `rtl_fm`/existing tools, confirm rackio-local audio and then connect NFM reception to SDRbox; keep the working simulator intact. No network audio.


## Live GMRS proof of reception — 2026-11-11

**Passed on actual rackio hardware:** `rtl_fm -d 0 -f 462562500 -M fm -s 24000 -r 24000 -g 30 -l 0 | aplay -r 24000 -f S16_LE -c 1` produced intelligible walkie-talkie audio from GMRS Channel 1 (462.5625 MHz) on rackio's speakers. Slight delay observed; defer latency tuning until integrated. Next engineering task: supervised subprocess adapter for rtl_fm + local playback; expose real receiver status to existing FastAPI/web UI; retain simulator fallback, then implement channel scanning and squelch. No remote browser audio.

## v0.2 initial integration — 2026-11-11

Committed live GMRS Channel 1 fixed-frequency receiver using supervised `rtl_fm` → `aplay` child processes, invoked by existing API SCAN/STOP and heard through rackio-local audio only. HOLD retains live reception; SKIP and other banks disabled until multi-channel support. WebSocket state is shared across local and remote browsers. No RF-derived meter, squelch or real activity logging yet; simulated backend remains selectable with `SDRBOX_RECEIVER=sim`. **Awaiting first rackio field test**, not yet verified running in user hardware. See [RUNNING.md](RUNNING.md).

## v0.3 candidate — 2026-11-11

Implemented native `rtl_fm` multi-frequency GMRS 1–7 squelch/hopping (`-l` configurable 1–100, `-t 5`) with browser INFO settings and retained fixed Channel 1 fallback. No active-channel attribution, RF signal meter or hit log; HOLD/SKIP disabled for scanning because rtl_fm provides no reliable active-frequency reporting. **Committed but not yet tested on rackio.** See [RUNNING.md](RUNNING.md).

## v0.3 field result — 2026-11-11

User verified real GMRS 1–7 scanner works with walkie-talkie. Squelch ~15 was the current sweet spot, updated as runtime/UI default. Next priority: accurate activity-channel reporting and meaningful hit log, avoiding fictitious RSSI/readouts; consider moving scan scheduling/detection into application if rtl_fm lacks structured channel events.

## v0.4 candidate — Python-owned channel scheduling

Added a dedicated Python-managed GMRS 1–7 scan profile, with single-frequency rtl_fm per channel, squelched PCM activity estimation, live requested-frequency display, real hit events, HOLD and SKIP. Existing rtl_fm multi-frequency scan remains a field-tested fallback. **v0.4 is committed, not yet verified on rackio.** Restart-per-channel retuning will likely be slower than legacy scan; benchmark dwell, activity false positives, audio and cleanup. See RUNNING.md.

## v0.4 field result and fix candidate — 2026-11-11

Real managed scanning runs ~1 channel/second and detects/demodulates a GMRS CH1 walkie-talkie transmission, but failed to resume after the transmission ended without manually pressing SKIP. Root cause suspected: hang-time logic only previously ran when a new PCM chunk was read, so it could not expire if `rtl_fm` closed squelch by not delivering any further chunks. Updated `scanner.py` to expire activity by wall-clock time on every loop tick, even with no new PCM. **Fix untested on rackio**; test CH1 PTT release and automatic scan resume. Keep SKIP fallback.

## v0.4 auto-resume verified — 2026-11-11

User confirmed the revised silence timeout is working better after the earlier stuck-on-channel bug. Managed scanning was observed at approximately 1 channel/second, and Channel 1 detection and audio already worked. Next recommended test: transmit on several GMRS channels, confirm accurate displayed frequency/hits, HOLD/SKIP, and correct resumption before replacing per-channel rtl_fm subprocesses with persistent tuner control. No measured scan latency or RSSI yet.
