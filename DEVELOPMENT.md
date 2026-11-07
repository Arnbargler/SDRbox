# Development plan

_2026-11-07 — planning phase; do not mark any milestone completed without running it on the Dell._

## Current known-good baseline

- Linux Mint boots the rack computer.
- GQRX receives FM broadcasting.
- GQRX was seen responding around **118.800 MHz**, demonstrating airband activity/reception.
- An earlier GQRX frequency-offset issue was corrected by selecting the **Realtek** SDR device, rather than the generic RTL entry.
- No autonomous scanner or custom two-screen Qt application has been implemented.

## Build milestones (incremental)

### M0 — Inventory and reliable GQRX baseline
- Capture hardware/OS/display/USB/audio details from [HARDWARE.md](HARDWARE.md).
- Verify 118.800 MHz audio in AM, antenna/cable and gain.
- Record known sample-rate(s) that stream without dropped samples, tunable gain and frequency correction (PPM if needed).
- Native resolutions, XRandR outputs and layout are confirmed: **upper 1U 1424×280 on HDMI-1 at +0+0**, **lower 2U 1280×400 on HDMI-2 at +59+280**. Touch mapping was tested successfully (upper disabled, lower accurate). See [TOUCHSCREEN.md](TOUCHSCREEN.md). Check DPI scaling if needed and verify auto-configuration after reboot.

### M1 — Headless airband scanner (first **coding** goal)
- Start with a known-frequency list of a few Ottawa airband stations that are **verified**, plus manual override.
- Prove AM decode, signal threshold/squelch, sound output, scan pause, hang and resume.
- Expose a status line/event log. No GUI needed to verify DSP.
- Prefer proven SDR libraries/tools. Benchmark retune/settle and channel revisit time.

### M2 — FFT chunk-scanning proof of concept
- Measure actual useful passband at ~2.4 MS/s or a stable supported rate.
- Generate overlapping windows covering 118–136.975 MHz (expect ~10 as an initial planning estimate).
- Detect peaks above per-window noise floor; reject DC and persistent spur artifacts.
- Validate whether peak detection confirms actual AM traffic versus spurious energy.
- Stay within current IQ window to demodulate if possible; avoid unnecessary hardware retune.
- Compare against M1 known-channel scanner and report measured false hit/missed traffic rates.

### M3 — PySide6 dual-screen prototype
- Display top **1424×280** (1U) status window and middle **1280×400** (2U) Home Scan view per [UI.md](UI.md); verify that five bank toggles, readout, hits and four actions fit at native resolution without vertical scrolling.
- Implement working AIR bank toggle, SCAN / HOLD / SKIP, current freq and recent hits.
- Connect real scanner events, not simulated radio readouts.
- Persist config in YAML or JSON; include basic error handling.

### M4 — Multi-bank scheduler
- Add CB, GMRS, AMB and FIRE as **editable bank definitions**, with only confirmed and monitorable frequencies enabled.
- Add priority/fairness, mode per channel/window, on/off while scanning.
- Measure latency added by each enabled bank and show user-friendly estimates/status.
- Avoid treating encrypted/digital/trunked systems as analogue FM.

### M5 — Appliance polish
- Autostart after login, kiosk/borderless panels on correct screens, recover on SDR disconnect.
- Optional recording, favourites/lockouts, spectrum view.
- Later hardware upgrades and RSP1A adapter.

## Workflow agreement

- User controls design decisions and field testing.
- Prefer small commits and tests over one giant speculative implementation.
- When working via an AI/Codex assistant, inspect the repo and current device state before changing code. Do not overwrite docs based on an outdated handoff.
- Do not start simultaneous GQRX and scanner processes against one RTL-SDR.
- Keep a changelog of successful/failed tests with real frequencies, mode, observations and dates.
- Any local services/autostart are **future options**, not assumed to exist.

## Open decisions

- **Display resolutions, IDs/arrangement and touch mapping are confirmed**; touchscreen login-autostart still needs reboot validation. Receiver type/model details and sample rate require probes.
- Initial DSP library and scanner mechanism: known-channel baseline vs FFT-first. Recommendation: **M1 then M2**, so FFT complexity does not block a working scanner.
- Detection thresholds, gain control strategy, bandwidth and hang time (measure rather than prescribe).
- Which local CB / GMRS / AMB / FIRE channels are legal, active, receivable with analogue AM/NFM.
- Audio output device, long-running recording/storage policy and whether trunking is ever desired.
