# SDRbox — handoff for the next AI/developer

**Updated 2026-11-07. Read this first, then README, ARCHITECTURE, WEB_API, UI, DEVELOPMENT, HARDWARE and TOUCHSCREEN.**

## One-sentence brief

Build a **web-based, local-audio-first radio scanner appliance** on Linux Mint (`rackio.local`): a single Python scanner/SDR backend + **FastAPI web server**, with Chromium on the rack displaying **read-only 1424×280 `/status`** above **touch-controlled 1280×400 `/control`**, while other home browsers access the same shared application at `/`.

## Decisions not to reopen without user request

1. **Linux Mint**, not Xubuntu. The Dell OptiPlex runs the radio and serves the UI.
2. **Web server architecture replaces the earlier PySide6 proposal.** No separate native local app. Use a modular monolith: radio, scanner/controller, web API, static frontend and storage.
3. **FastAPI + REST/WebSocket** planned; frontend **HTML/CSS/vanilla JavaScript (ES modules)**, modern CSS Grid/Flexbox. No need for React/Vue, Docker or multiple daemons initially.
4. **Rack audio first**: demodulated voice plays through the local rackio speaker/audio output. **Browser audio streaming comes later**, not a v1 dependency.
5. All browsers use **one authoritative scanner engine and one NESDR**, not independent tuner sessions; controls update every display. Closing browser windows must not stop scanning.
6. Start **airband** because GMRS is quiet near user. GQRX has shown reception around **118.800 MHz**; no custom scanner currently exists.
7. Main UI has independent **CB / GMRS / AIR / AMB / FIRE** enable/disable toggles for scan banks. One bank may contain many frequency chunks or channels, not necessarily one 2.4 MHz window.
8. Desired scanning method: FFT search over overlapping ~2 MHz useful windows for candidates above local noise floor, auto pause/listen/resume. **Known-channel airband scanner first** as reliable comparison/baseline. 118.000–136.975 MHz is ~19 MHz; ~10 overlapping chunks is an **unmeasured starting estimate** (8 mathematical minimum at ideal 2.4 MHz).
9. Upper screen is **status only; touch disabled**. Lower screen is touch-enabled. The first dark green/charcoal scanner dashboard mockup, edited to remove antenna/SDR clutter, was approved. See UI.md; SVG in repo is a simplified rendering, not the exact photorealistic PNG.
10. Future upgrades accepted: **SDRplay RSP1A**, better antenna placement, USB rotary knob, communications speaker. No current dependency.
11. User likes incremental, testable changes, not lengthy instructions detached from live feedback.

## Physical rack and touch (tested)

| Display | Output | Geometry | Input |
| --- | --- | --- | --- |
| Upper 1U | HDMI-1 | **1424×280 +0+0** | upper touch disabled |
| Lower 2U | HDMI-2 | **1280×400 +59+280** | mapped, accurate touch |

Both touchscreens identify as identical `wch.cn TouchScreen`; distinguish **USB paths** instead. Physical port 0:7 is upper, 0:6 is lower; working script at `scripts/rackio-touch.sh` and details in TOUCHSCREEN.md. User tested script and said “looks good”; **after-reboot autostart persistence has not yet been confirmed**. Do not confuse this proven touch mapping with *untested* Chromium kiosk geometry/autostart.

## Verified vs proposed

**Verified:** Linux Mint running GQRX; broadcast FM and 118.800 MHz airband reception result; XRandR monitor placement; corrected touchscreen mapping; tested path-based touch configuration script.

**Not yet implemented:** FastAPI server, web pages, WebSockets, scanner engine, local decoded audio pipeline outside GQRX, FFT signal discovery, saved bank settings, remote browser controls, kiosk autostart, browser audio.

**Important:** `http://rackio.local:8080` is a **proposed URL**, not verified as running. Any screenshot frequency/recent hits are **illustrative mock data**. A lower-case `rackio.local` host exists; its exact IP/port is not needed for architecture.

## First steps for the next instance

1. Inspect actual current repo; use the docs here, not earlier chat suggestions about Qt.
2. Validate Linux Mint/RF/audio baseline and touchscreen reboot behavior, with GQRX still available for comparison. Ask user for one manageable test at a time.
3. Make a **FastAPI skeleton**: `/status`, `/control`, `/`, basic REST status/command endpoints, WebSocket broadcast. Start with **labelled simulated state** and prove upper/lower/remote views stay synchronized.
4. Bring the NooElec under sole scanner ownership (close GQRX), prove known-channel **AM airband** detection and **local speaker audio** independent of browser connections.
5. Add FFT-window discovery after baseline, then other toggle banks, persistence, appliance startup and remote browser audio last. See DEVELOPMENT.md for milestone order.

## Important constraints

- One NESDR cannot monitor separated chunks at the same instant; additional banks raise revisit latency.
- 2.4 MS/s nominal sample rate does **not** guarantee a 2.4 MHz clean usable band; leave window margins/overlap.
- Don't mistake FFT peaks for spoken voice; reject DC spikes, interference and spurs.
- AIR voice AM; analogue GMRS narrow FM; fire/ambulance may be trunked/digital/encrypted. Do **not** invent monitorable local emergency-service frequencies.
- Keep Python SDR/USB/DSP reads off the web server's async loop; one controller must serialize radio commands.
- Serve clients on the home LAN only to start, **never expose an unauthenticated remote-control server publicly**. Mutating commands and WebSocket origins need suitable validation.
- Browser audio is **not** part of first local-audio milestone.
- Remote UI is a controller of shared hardware, **not** a distinct receiver. Ensure reconnecting browser obtains correct status snapshot.
- No transmission feature is planned.

## Documentation map

- `README.md`: overview.
- `ARCHITECTURE.md`: modular monolith + RF and web architecture.
- `WEB_API.md`: planned routes, commands, events, browser concurrency and local-first audio.
- `UI.md`: approved UI and HTML/CSS 1U/2U/responsive screen specifications.
- `REQUIREMENTS.md`: acceptance tests.
- `DEVELOPMENT.md`: revised milestone plan M0–M6.
- `HARDWARE.md`: known host hardware, unknowns.
- `TOUCHSCREEN.md` and `scripts/rackio-touch.sh`: tested input mapping, unverified post-reboot autostart.
- `assets/scanner-ui-concept.svg`: simplified design asset, **not actual implemented UI**.

User may call this the **overpowered SDR rack**; the GitHub project is **SDRbox** (<https://github.com/Arnbargler/SDRbox>).
