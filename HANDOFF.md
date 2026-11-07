# SDRbox — next AI/developer handoff

**Updated 2026-11-07. Read this before coding.**

## The one-sentence brief

Build a **Linux Mint / Dell OptiPlex / NooElec NESDR Smart** **scanner appliance** with **1424×280 upper 1U glanceable status** and **1280×400 lower 2U touchscreen control interface**, independent category bank toggles and **airband-first** automatic scan/stop/listen/resume.

## Known decisions

1. **Linux Mint**, **not Xubuntu**. Do not re-propose reinstallation.
2. **Scanner first**; full SDR spectrum lab, if any, is an advanced mode.
3. Hardware is working with **GQRX**. 118.800 MHz airband produced reception results; broadcast FM also works.
4. Main touch UI has **CB / GMRS / AIR / AMB / FIRE** independent on/off toggle tiles. User wants to scan selected **bands/chunks**, not just switch one preset at a time.
5. **AIR first**, because GMRS is relatively quiet in the user's area.
6. User wants **FFT-wide-window discovery** where practical, with threshold relative to noise floor, pause on detected activity, AM demodulation, and resume. Technical feasibility and dwell time are still unmeasured.
7. Nominal NESDR usable span discussion is **~2.4 MHz instantaneous**; expect around **10 overlapping windows** to cover 118–136.975 MHz as a *starting estimate*. 8 is only the mathematical minimum with no guard bands.
8. Future SDRplay RSP1A, remote antenna, rotary encoder and communications speaker were accepted, but **not required now**.
9. The **first scanner dashboard mockup** was the favourite; it was regenerated **without the visible external SDR/antenna**. Dark, large green/grey bank tiles, top status strip, recent hits and SCAN/HOLD/SKIP/SETTINGS. See [UI.md](UI.md).
10. User prefers pragmatic, staged work and testing on the actual hardware before running ahead.
11. **Confirmed display geometry:** upper **1U = 1424×280 on HDMI-1 at +0+0**, lower **2U = 1280×400 on HDMI-2 at +59+280**. Touch accuracy is now verified: top disabled, bottom mapped correctly to HDMI-2. Use [TOUCHSCREEN.md](TOUCHSCREEN.md) for device paths, working commands and login autostart setup. **Autostart has not yet been reboot-tested.**

## What is actually implemented?

**Nothing from the custom SDRbox software yet.** The new repository was initially empty. These docs and the SVG UI schematic establish a handoff baseline. GQRX is a working external application, not an SDRbox frontend. Any frequencies, signal levels and entries shown in concept images are fabricated UI illustration, not logged results.

## First actions next session

1. Inspect repo and read README/HARDWARE/REQUIREMENTS/ARCHITECTURE/UI/DEVELOPMENT.
2. Get remaining Linux Mint / SDR / audio specs from actual Dell (`lsusb`, `rtl_test -t`, `pactl` or PipeWire equivalents). **Display output mapping, offsets and touchscreen behavior are already confirmed** in TOUCHSCREEN.md; verify after reboot that Mint autostart runs the mapping script. Close GQRX when using `rtl_test`.
3. Choose an initial **headless AIR test** at 118.800 MHz or other locally verified voice channels. Prove AM audio, squelch and retuning.
4. Implement and measure **known-channel scanner** (minimum viable), then prototype FFT window discovery; don't claim unmeasured 1-second whole-band scans.
5. Build GUI only once radio backend produces reliable state changes.

## Risks and critical distinctions

- **2.4 MHz IQ capture is not 2.4 MHz of pristine independent coverage** at all rates/gains. Leave overlap.
- Need to detect **voice**, not any arbitrary strong carrier. False peaks, local noise and tuner center spur need handling.
- **One NESDR** cannot continuously monitor different windows at once; extra bank toggles increase revisit latency.
- AIR uses **AM**; GMRS and many analogue land-mobile channels **NFM**, while many emergency services may be digital/trunked/encrypted. Never invent reliable local emergency frequencies from design art.
- Dell model still unverified. Display geometry and working touch mapping **have been confirmed** (top 1424×280, HDMI-1 with touch disabled; bottom 1280×400, HDMI-2 with correctly mapped touch). **Persistence after reboot not yet proven**.
- **No SDR transmit** features are planned.
- The approved photorealistic PNG is not yet a repo binary. The checked-in SVG is a simplified editable visual placeholder; user can upload full PNG.

## Relevant repo paths

- `README.md`: orientation and index
- `HARDWARE.md`: equipment and actual probe commands
- `TOUCHSCREEN.md`: verified touchscreen USB-port mapping and autostart instructions
- `REQUIREMENTS.md`: acceptance criteria
- `ARCHITECTURE.md`: DSP/scheduler/state-machine proposal
- `UI.md`: approved UI contract and image status
- `DEVELOPMENT.md`: milestones M0–M5
- `assets/scanner-ui-concept.svg`: a repo-hosted dashboard layout reference

**Remember:** User may call this the “overpowered SDR rack.” The proper project repo name is **SDRbox**.
