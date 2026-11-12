# SDRbox handoff — updated 2026-11-11

**Live code exists now:** FastAPI server, REST/WebSocket API and shared-state simulated scanner with a browser UI. See [RUNNING.md](RUNNING.md). **No real SDR or audio integration yet.** This supersedes older planning-only status statements below.

**Confirmed hardware:** Dell OptiPlex 5060 Micro, 8 GB RAM, Linux Mint, NooElec NESDR Smart. One HDMI-2 1280×400 screen at +0+0 and touch working following reboot. Old dual-screen startup files removed.

**Priority change:** GMRS-first using user's walkie-talkie, then AIR. **Normal Chrome/Chromium locally and remotely** on the home LAN; no obligation to run headless or configure kiosk yet. Local radio audio when real demodulation is integrated; no network/browser audio for now.

**Immediate next test:** install environment, `python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080`, verify touch layout and two synced browser sessions. Then implement a live single-frequency GMRS NFM receiver and rackio-local audio before automatic scan/squelch.

---

# SDRbox — next AI / developer handoff

**Updated 2026-11-08. Read this before making changes.** Then review README, UI, HARDWARE, TOUCHSCREEN, ARCHITECTURE, WEB_API, REQUIREMENTS and DEVELOPMENT.

## The current design in one paragraph

Build **SDRbox**, a web-based, scanner-first radio appliance running **Linux Mint on rackio.local** (Dell OptiPlex, NooElec NESDR Smart). The local appliance now has **ONLY ONE 2U touchscreen at 1280×400 pixels**. The **upper 1U display was physically removed** on 2026-11-08. One Chromium window shows a compact FastAPI-served control/status dashboard; remote browsers on the home LAN use the same server. **Local speaker audio first**, optional browser streaming later. The user chose **single-screen visual mockup option #2**, a premium charcoal/green interface.

## Decisions already made

1. **Linux Mint** stays. Not Xubuntu.
2. **Web server style, NOT PySide6**: FastAPI/Python backend, REST + WebSocket state, HTML/CSS/vanilla JS frontend.
3. **One local display at 1280×400** combining status and controls. No second display, no mandatory `/status` window, no two-window Chromium setup.
4. **Chosen design is photo mockup #2** from the latest one-screen set. See [UI.md](UI.md) and `assets/scanner-mockup-option-2.webp`. The old two-screen SVG is obsolete.
5. **One physical NESDR / single authoritative scanner engine**, independent of how many web clients attach. Closing browser windows must not stop RF scanning.
6. **Audio v1 local to rackio**, browser audio streaming afterward.
7. Five independently enabled scan banks: **CB / GMRS / AIR / AMB / FIRE**. One bank can contain many channels / ~2MHz RF windows; these toggles are not mutually exclusive.
8. **AIR first**. GQRX previously received activity near **118.800 MHz**; GMRS quiet. Start with known-channel AM scanner baseline, then desired FFT-wide-window signal search.
9. User wants small testable steps, remains in charge of design and testing.
10. Future **RSP1A**, remote antenna, physical tuning/volume knob and communications speaker are approved eventual upgrades but are **not v1 prerequisites**.

## What is actually verified?

- Linux Mint rackio host running GQRX; broadcast FM and airband activity around 118.800 MHz.
- Dell OptiPlex mounted in a small rack, with **one remaining 1280×400 touchscreen**.
- Previously two-monitor setup: upper HDMI-1 1424×280 +0+0 and lower HDMI-2 1280×400 +59+280.
- Previously lower touch accurately mapped after XInput correction. **This was proven BEFORE upper screen removal**, not after.
- User was given commands to remove dual-touch autostart and reboot. **Do not assume those commands were executed or that single-panel touch accuracy was reverified**.
- No FastAPI web service, custom scanner engine, UI, RF discovery or audio pipeline has been implemented yet. Photo shows illustration only.
- Proposed server URL `http://rackio.local:8080` is NOT an existing running service.

## First actions next session

1. Inspect the current repository, including selected image in [UI.md](UI.md). Do not create the retired two-display design.
2. Ask for/measure current **single-monitor XRandR geometry and touchscreen accuracy**. Check old `rackio-touch.desktop` / `rackio-touch.sh` have been removed; see [TOUCHSCREEN.md](TOUCHSCREEN.md). Do not blindly map to old offset.
3. Inventory actual Dell model/CPU/RAM, audio output, NESDR driver/sample rate. Keep GQRX working for diagnostic comparison.
4. Build simple **FastAPI skeleton** and **one 1280×400 local webpage** plus responsive remote page; test across rackio and N100 using visibly labeled simulated scanner events.
5. Implement known-frequency **AM airband receiver/scanner** using NESDR and **local rackio audio**; confirm squelch/hold/resume and status synchronization.
6. Benchmark FFT wide-window discovery, then add other banks and persistent history. Remote browser audio only after local scanner works.

## Radio and security constraints

- Nominal ~2.4 MS/s / 2.4MHz IQ span is not all clean usable passband; ~10 overlapping windows for 118–136.975 MHz is a preliminary estimate, not measured.
- One NESDR can tune only one distant band/window at a time; enabling more banks extends revisit delay.
- Avoid SDR center spikes/spurious peaks/false voice detection; check AM audio against threshold.
- FIRE/AMB frequency illustrations are not authoritative lists; many actual systems are digital/trunked/encrypted.
- Keep RF I/O/DSP off FastAPI event loop and serialize control commands.
- LAN-only at first. Never expose an unauthenticated hardware-control server to public Internet.
- No SDR transmission functionality planned.

## Key documents

- [README.md](README.md): orientation.
- [UI.md](UI.md): one-screen option #2.
- [HARDWARE.md](HARDWARE.md), [TOUCHSCREEN.md](TOUCHSCREEN.md): current rack and retired dual-panel touch setup.
- [ARCHITECTURE.md](ARCHITECTURE.md), [WEB_API.md](WEB_API.md): web server/scanner and shared state.
- [REQUIREMENTS.md](REQUIREMENTS.md), [DEVELOPMENT.md](DEVELOPMENT.md): tests and implementation sequence.

Repo: <https://github.com/Arnbargler/SDRbox>


## 2026-11-11 live test update

The user reports the cloned SDRbox v0.1 simulator starts and that the normal browser UI looks and functions well. The server/API/UI are running on rackio; live RTL-SDR reception and audio are **not** implemented. Local + remote browsers are the target; a simultaneous two-browser synchronization test is still worth checking.

`rtl_test -t` on rackio detected one Realtek RTL2838UHIDIR (SN 00000001) with Rafael Micro R820T, 29 gain options (0–49.6 dB), sample rate selected 2048000 S/s. It also logged `[R82XX] PLL not locked!` and `No E4000 tuner found, aborting.` The latter is expected for non-E4000 tuners and does not invalidate identification; the former alone does not establish hardware failure. See [HARDWARE.md](HARDWARE.md). Next: real GMRS NFM walkie-talkie reception and **local** rackio audio, then scanner integration; no remote audio yet.


## Confirmed live GMRS NFM test — 2026-11-11

Walkie-talkie Channel 1 (462.5625 MHz) successfully received using standalone `rtl_fm` piped into local `aplay` at 24 kHz, 30 dB requested tuner gain, software squelch disabled. Intelligible audio with slight latency. This is a verified **standalone RF/audio test**, not yet integrated into SDRbox. Next: incorporate rtl_fm/ALSA as the first radio backend, preserve simulation option; prioritize stable start/stop, shared status, cleanup on exit, and explicit AUDIO LOCAL indicator.

## v0.2 integration added — 2026-11-11

The GitHub repository now includes `sdrbox/receiver.py` running the previously proven GMRS 1 `rtl_fm | aplay` pipeline under supervised subprocesses; `sdrbox/main.py` exposes real start/stop/status via API and WebSocket. `SDRBOX_RECEIVER=sim` retains simulator. UI labels live mode accurately; no fake signal meter or hits. **Code committed but not yet run on rackio**: first action is `cd ~/SDRbox && git pull`, restart Uvicorn and test SCAN/STOP with the walkie-talkie. Single worker only, no competing GQRX, no network audio. See [RUNNING.md](RUNNING.md).

## v0.3 GMRS scanning candidate

Native rtl_fm scan of GMRS 1–7 added, using multiple `-f`, configurable `-l` threshold and `-t 5`, plus working fixed CH1 fallback. Local rackio audio only; settings in INFO require STOP first. No active channel reporting in scan, no actual signal meter/hits; HOLD/SKIP disabled for scan. **Awaiting field test; don't call it proven yet.** See RUNNING.md.

## v0.3 field verification — 2026-11-11

**Confirmed operational on rackio:** GMRS channels 1–7 scan works, with walkie-talkie transmissions received and squelch suppressing idle noise. User reports **15** is current best squelch, now the default. Don't assume this is calibrated or universal. Next step is accurate channel ID/event handling. No browser audio desired yet.

## v0.4 candidate (awaiting rackio field test)

Python managed scan module `sdrbox/scanner.py` coordinates GMRS 1–7 single-frequency rtl_fm children, reading squelched PCM to infer activity and broadcasting actual commanded tune, hit events and HOLD/SKIP. UI INFO profile `MANAGED_1_7` is default. Legacy native rtl_fm hopping remains selectable (`SCAN_1_7`) and already field-proven; fixed Channel 1 also retained. Python scheduler restarts rtl_fm per channel, potentially high latency; improve only after actual testing. No browser audio.

## Managed scanner known issue (2026-11-11)

v0.4 Python scanner advances at ~1 channel/s, and activity detection/audio on CH1 confirmed. It initially stuck receiving after PTT release until SKIP. Follow-up fix changes `scanner.py` to evaluate 1.1-second hang timeout even when no new PCM arrives (closed rtl_fm squelch might produce no chunks). **Not yet verified after fix.** Test auto resume first; if still stuck, inspect idle PCM/noise before altering squelch sensitivity.

## v0.5 persistent receiver candidate

GitHub now includes experimental `sdrbox/persistent.py` backed by `pyrtlsdr` and NumPy/SciPy (one device handle across GMRS 1–7 tune changes, local software NFM demod, RF contrast detection). It is selected by default as `PERSISTENT_1_7` but **has not been tested on rackio yet**. Install `requirements-persistent.txt`. Field-proven fallback remains `MANAGED_1_7` (Python channel control using rtl_fm, ~1 ch/sec, voice and auto-resume working). Persistent RF detector uses contrast thresholds 5/3 dB, not the old slider squelch 15. No remote audio. Review [RUNNING.md](RUNNING.md).
