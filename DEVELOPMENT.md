# SDRbox development plan

**Updated 2026-11-07. Planning phase; nothing from the custom scanner/web-server code has been deployed yet.** Do not mark milestones done without tests on rackio.

## Decided implementation approach

- **Linux Mint on rackio**, known-good **NooElec NESDR Smart** with GQRX for diagnostics.
- **Python scanner engine + FastAPI web server**, single authoritative receiver/controller.
- **HTML/CSS/JavaScript** views served from rackio: `/status` upper 1U **1424×280**, `/control` lower 2U **1280×400**, `/` responsive LAN browser UI.
- Chromium on rackio supplies the two local fullscreen/browser app windows; any home-network browser connects to the same service.
- WebSocket broadcast of scanner state, REST for commands/snapshots; one server controls one SDR. Browser closure does **not** shut the scanner down.
- **Decoded audio plays locally through rackio first**. Browser audio streaming is postponed.
- **Not** PySide6. Modular monolith with separate core, radio, web and storage modules (see [ARCHITECTURE.md](ARCHITECTURE.md)).
- No docker/microservices/frontend framework required for first version. Add complexity only after measurements.

## Verified baseline

- GQRX under Linux Mint receives FM broadcast and activity around **118.800 MHz** aviation. It is not yet an automatic scanner.
- An earlier apparent GQRX frequency shift improved after selecting the **Realtek** RTL device.
- XRandR: **HDMI-1 = 1424×280 at +0+0**, **HDMI-2 = 1280×400 at +59+280**.
- Touch test: top touch disabled; lower touch accurate with `map-to-output ... HDMI-2`. USB-path-based script is tested; login autostart and post-reboot persistence still await verification. See [TOUCHSCREEN.md](TOUCHSCREEN.md).
- SDRplay RSP1A, remote antenna, knob and speaker are future options/approved upgrades, **not installed as part of this software milestone**.

## Build milestones

### M0 — Inventory and local integration baseline
- Gather actual Dell CPU/RAM/OS version, ALSA/PulseAudio/PipeWire sound output, SDR driver/device and reliable sample rate.
- Verify airband audio through rackio's local audio output in GQRX, then measure with chosen DSP tools; close GQRX before opening NESDR in another process.
- Reboot test the touch-autostart script; verify display output IDs, Chromium kiosk/window placement mechanics and audio routing.
- Avoid treating an unverified `http://rackio.local:8080` URL as a running server.

### M1 — Web shell and simulated scanner events
- Build minimal FastAPI server with basic health endpoint, authoritative in-memory scanner state, command validation, WebSocket fanout and simulated receiver events.
- Serve **three pages from one app**: status strip (1424×280), control panel (1280×400), responsive home interface.
- Test from rackio and another LAN computer: bank toggle and scan state update all clients; reload/reconnect restores state.
- Label fake hits/signal values as simulation, not actual receptions.
- No hardware DSP integration required yet; prove screen layout/communications without needing aircraft traffic.

### M2 — First real airband receiver and local audio
- Prove AM tune/demodulation/audio from the NESDR with the selected Python/library/receiver toolchain.
- Create headless scanner with known **verified airband channels**, gain, squelch, pause, hang and resume.
- Feed state/events from real scanner into API and browser UI; remove simulated values in live mode.
- Verify local rackio speaker sound works even with browsers closed.
- Measure retuning, audio latency and revisit time.

### M3 — FFT wide-window airband discovery
- Measure usable instantaneous bandwidth (nominal 2.4 MS/s, not necessarily 2.4 MHz clean edges).
- Build overlapping windows across 118.000–136.975 MHz; **~10** is an initial estimate.
- Detect candidate voice channels above local noise floor, reject spur/DC artifacts, and demodulate AM.
- Benchmark false positives and missed short transmissions against the known-channel scanner; avoid unnecessary retunes when an active channel fits in current IQ window.

### M4 — Multi-bank scheduler and activity data
- Add editable **CB / GMRS / AIR / AMB / FIRE** toggles and bank definitions, per-bank channel lists/windows and modes.
- Preserve fair scan scheduling while tracking revisit latency with multiple banks enabled.
- Add recent hits in **SQLite** and settings/channel bank config in YAML or JSON.
- Do not assume local emergency services are receivable analogue voice; trunked/digital/encrypted services need separate assessment.

### M5 — Appliance integration and reliability
- Browser app/kiosk views autostart on correct monitors after login; start scanner web server reliably independently of browser lifecycle.
- Restore selected banks/settings; report SDR/driver/audio/network faults and reconnect clients cleanly.
- Confirm one control action from a remote LAN browser changes the same shared scanner state on the rack screens.
- Consider recording, skip/lockouts, priority handling, advanced waterfall view and boot polish only after baseline works.

### M6 — Later (not a v1 blocker)
- **Browser audio streaming** (select codec/transport, account for browser autoplay, network latency and multiple clients); leave rackio local audio working.
- RSP1A adapter, remote antenna, encoder knob, dedicated speaker.
- Optional access control for less-trusted networks; never expose unauthenticated control endpoint directly to the public Internet.

## Development workflow

- User controls the interface design and field testing; use small tested commits.
- First inspect current repo/host state instead of relying only on old handoff text.
- Keep simulated UI testing separate from live RF testing; no invented signal strength or hit logs.
- Prefer established DSP/RTL-SDR components; don't implement radio algorithms unless needed.
- A **single process/app with separate modules and a worker thread/process** is preferred over microservices.
- Check ability to place two Chromium windows correctly before creating desktop autostart units.
- Browser-facing address/port, service process, firewall binding and session autologin remain deployment choices.
- Keep **local audio** the success criterion before introducing browser audio.

## Open decisions

- Actual Dell specification, NESDR sample rates, chosen radio DSP library and rackio audio device.
- Exact port and server deployment command/service type; proposed `rackio.local:8080` only.
- Detection threshold/gain/AM bandwidth/hang time and measured scan rate.
- Verified local frequency banks and long-term recording storage/retention.
- Exact remote-audio streaming protocol (later).
