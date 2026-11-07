# SDRbox requirements — scanner first

_Status: proposed behaviour, not yet built. 2026-11-07._

## Purpose

Create a simple, dedicated, receive-only desktop/rack scanner that boots into a purpose-built **two-display appliance interface** on Linux Mint.

## Functional v1

| ID | Requirement | Initial acceptance test |
| --- | --- | --- |
| R01 | Start scanner manually from Linux Mint without requiring GQRX | Application opens borderless, independently sized **1424×280 top** and **1280×400 bottom** windows and exits cleanly |
| R02 | Upper 1U window shows frequency, bank, AM/NFM, signal activity, and SCANNING / RECEIVING / HELD / ERROR | Status reflects synthetic state, then live SDR state |
| R03 | Lower 2U window shows large independent **CB / GMRS / AIR / AMB / FIRE** on/off bank toggles | Toggles persist across restart |
| R04 | Start, hold/resume, skip active signal, open settings | State-machine transitions are deterministic |
| R05 | **AIR** initially enables a configurable 118.000–136.975 MHz plan | Correct window list produced with overlap |
| R06 | Scan fixed known airband channels **and/or** FFT-detect candidates across windows | Live AM traffic pauses scanner and produces intelligible audio |
| R07 | Estimate a local noise floor, use tunable detection threshold and hysteresis | Can tune detection without repeated false pauses |
| R08 | Automatic dwell, signal confirmation, squelch close and resume delay | Does not chatter between states at noise boundary |
| R09 | Each bank and channel/window can define demodulation mode | AM aviation and NFM GMRS tests both feasible |
| R10 | Current frequency and recent-hit list with timestamp and duration | Logs genuine detections; not every FFT artifact |
| R11 | Config/state survive restart | Bank selection and settings restore correctly |
| R12 | SDR disconnect, busy device, audio failure and no banks enabled handled visibly | Clear error and recovery paths |

**Top priority:** Demonstrate scanner engine on **airband only** before polishing all five band definitions.

## v1 scanning semantics

- Each large top-level toggle enables/disables a **bank** (category), not necessarily exactly 2.4 MHz.
- A bank references one or more smaller **windows** of sampled spectrum, or a list of channels. Banks may overlap; deduplicate repeated windows/channels in scheduling.
- Scanning rotates through enabled windows, evaluates candidate signal peaks, and listens to an active candidate. When idle/silent after hang time, it resumes the rotation.
- **HOLD** intentionally remains at current channel and disables automatic resumption; a temporary squelch-triggered **PAUSE** is different.
- **SKIP** moves past the current hit; optionally remember a temporary lockout. Permanent blacklist is a separate deliberate action.
- Never auto-enable unavailable categories silently; user can select multiple banks and see an estimated revisit latency.

## Non-functional requirements

- Native target dimensions are **1424×280 (1U status)** and **1280×400 (2U controls)**, as confirmed by the user. Layout should be pixel-aware, legible on these unusually wide/short displays, and avoid tiny stock-GQRX widgets.
- The 1280×400 UI must fit the five bank toggles, a concise current-frequency/signal region, recent hits and primary SCAN/HOLD/SKIP/SETTINGS actions without vertical scrolling on the Home view. Secondary settings may use separate screens.
- Keep minimum practical touch targets generously sized; verify physical touch mapping and DPI scaling on the installed monitor.
- Dark industrial theme, restrained green highlights for enabled banks, strong contrast for state.
- One SDR backend process owns the hardware; no competing simultaneous GQRX access.
- Graceful startup/shutdown; logging, clear status and easy debugging on Linux Mint.
- CPU/resource load should be **measured on the Dell**, not guessed.
- All assumptions about regional frequencies should be verified before shipping predefined banks.
- Config is human-readable and versioned; avoid hard-coded regional frequency lists in the UI.

## Later (out of v1 unless deliberately promoted)

- Airband/other bank priority weighting; optional multi-channel demodulation inside one IQ window.
- Smart channel identification, favourites, discovery mode, temporary/permanent lockouts.
- Activity statistics, audio capture/recording, automatic recordings, replay.
- FFT spectrum/waterfall **Advanced** page.
- Fast boot-to-appliance, hiding Mint desktop.
- Extra hardware: rotary encoder, speaker, remote antennas, SDRplay RSP1A.
- Digital/trunked reception only as a separate feasibility exercise; **encrypted calls are not a target**.

## Test approach

Start with known busy aviation communications and a known GQRX baseline. Validate tuning accuracy, AM clarity, false-positive rate, resume logic and revisit time. Record actual measurements (dwell, retune overhead, missed short transmissions), not claims based on optimistic estimates.
