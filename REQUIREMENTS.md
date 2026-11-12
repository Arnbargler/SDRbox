# SDRbox requirements — spectrum-first radio appliance

**Current specification, updated 2026-11-11.** Status separates completed baseline from future acceptance criteria.

## Product goal

A receive-only scanner running on rackio that surveys broad, overlapping RF spectrum **windows** rather than repeatedly checking one pre-programmed frequency. Detect multiple signals from an IQ capture, reject noise/artifacts, select and demodulate the strongest *qualified* candidate initially, and automatically resume. Normal local/remote browser controls, rackio-local audio.

## Acceptance criteria

| ID | Feature | Acceptance | Status |
| --- | --- | --- | --- |
| B01 | One 1280×400 rack touchscreen with unified controls | HDMI-2 +0+0 and touch usable | **Verified** |
| B02 | FastAPI/Chrome LAN interface | Rackio browser control works | **Verified** |
| B03 | Live NFM GMRS and local audio | CH1 walkie-talkie intelligible, scan/resume | **Verified in rtl_fm modes** |
| B04 | Accurate displayed sequential scan channel | GMRS 1/3/7 frequencies identified | **Verified v0.4** |
| B05 | One open RTL device across retunes | Python persistent tuner remains open; ~3 ch/s observed | **Startup/retune verified v0.5** |
| S01 | One usable wide IQ window at 462 MHz | FFT includes GMRS 1–7 simultaneously with measured CPU/sample rate | **Future** |
| S02 | Adaptive, local noise floor | Baseline follows changes; spurs/edge bins excluded | **Basic implementation, calibration pending** |
| S03 | Candidate extraction | Estimated center, occupied bandwidth and contrast; sensible duplicate grouping | **Experimental implementation, field test pending** |
| S04 | Robust qualification | Persistence/hysteresis rejects idle noise and transient spurs | **Two-frame persistence added; spurious rejection unverified** |
| S05 | Signal selection | Highest-ranked qualified candidate chosen, not just largest raw FFT bin | **Future** |
| S06 | In-window NFM listening | Voice audio on rackio; accurate candidate/channel identification | **Future** |
| S07 | End-of-activity logic | Correct hang/resume, HOLD, SKIP and no stuck receiver | **Future** |
| S08 | Truthful logs/status | Real confirmed events distinct from candidate peaks/simulation; no invented dBm | **Future** |
| S09 | Multiple windows | Add 467 MHz, then measured overlapping windows and revisit times | **Future** |
| S10 | Airband AM discovery | AM decode on tested civil airband signals/windows | **Future** |
| S11 | Multiple configured banks | CB/GMRS/AIR/AMB/FIRE only active when supported/configured; persist selections | **Future** |
| S12 | Device/audio robustness | Errors surfaced, no USB/audio process leaks, start/stop repeatable | **Partially verified** |
| S13 | Shared browser state | Two LAN clients synchronized and recover after reconnect | **Design implemented; dedicated test pending** |
| S14 | LAN security | Do not expose unauthenticated controls publicly; harden before less-trusted access | **Constraint** |

## Spectrum design constraints

- Nominal RTL-SDR sample rate and usable *clean* bandwidth differ; allow overlap and guard bands.
- One RTL tuner cannot simultaneously capture disjoint 462 and 467 MHz chunks. A scan schedule has measured revisit gaps.
- With multiple signals active in one chunk, initial policy chooses **strongest qualified** with configurable policies later.
- A raw spectral peak can be a spurious, nonvoice or unrelated signal. Log *candidate*, *confirmed activity* and *selected audio* as different concepts.
- FM (GMRS/FRS) first, AM (AIR) later. No assumption that local AMB/FIRE traffic is analogue/decryptable.
- Keep local audio independent of browsers. No transmission.

## Interface constraints

One dark charcoal/green responsive HTML/CSS/JS interface on the 1280×400 rack screen; normal Chrome (no enforced kiosk); remote LAN control of the same scanner. Show actual **window coverage**, **detected signal frequency**, **selected audio frequency**, signal strength **relative to local noise floor**, and recent verified hits as capabilities come online. Avoid fake signal meters.

## Deferred

Browser audio, broad recording/waterfall, digital/trunked decoders, RSP1A adapter, optional automatic kiosk, rotary controls, hardened remote access.

Test one milestone on real rackio hardware before moving to the next.
