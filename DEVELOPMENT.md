# SDRbox development — current decisions and field results

**Updated 2026-11-11. Next objective: spectrum-first FFT window detection. Do not implement until requested.**

## Verified state on rackio

| Milestone | Verified result |
| --- | --- |
| M0 physical rack | One HDMI-2 1280×400 +0+0 touchscreen, touch accurate after reboot; legacy dual-screen scripts removed |
| M1 control UI | FastAPI normal Chrome interface starts and functions; one server/device shared by design |
| M2 live single GMRS | CH1 462.5625 MHz `rtl_fm | aplay` intelligible audio on rackio |
| M3 native rtl_fm scan | GMRS 1–7 scans and opens squelch; **15** was the user's sweet spot for this setup |
| M4 Python/rtl_fm scan | Frequency/CH1, CH3, CH7 shown correctly; ~**1 channel/s**, receives and automatically resumes after transmission. Earlier resume bug corrected |
| M5 persistent SDR | `pyrtlsdr` now imports, opens and retunes; ~**3 channels/s** user-observed. Separate confirmation of DSP audio/detection accuracy still pending |

**Compatibility lesson:** an initially installed newer `pyrtlsdr` expected missing symbol `rtlsdr_set_dithering` in system `librtlsdr.so.2`. Pinning `pyrtlsdr==0.2.91` plus `setuptools<82` in optional requirements resolved the startup blocker on rackio **without replacing system radio libraries**.

## Why development direction changed

Sequential per-frequency scanner mode is useful for validation but not the target. The desired appliance inspects **~2 MHz usable spectrum windows**, detects **multiple candidate peaks** relative to a locally estimated noise floor, selects a **strongest qualified signal** initially, demodulates and resumes automatically. GMRS 1–7 all fit in one window, so per-channel hopping there is unnecessary. Broader bands use overlapping windows and one single-owner tuner.

## Next milestones (in order)

### S1 — Spectrum visibility, one GMRS window

Reuse persistent SDR access to capture a broad 462 MHz IQ window. Measure stable sample rates, IQ buffer timing and CPU budget. Produce FFT/averaged spectrum and a local noise estimate; mask DC/LO spur and edges. **Display genuinely measured bin data**, identify test-transmitter peaks, and distinguish window center from signal center. Initially **no automatic audio selection** required.

**Gate:** On/Off CH1 and CH7 can be distinguished visually and numerically above real background noise; low false-peak rate when idle. A second walkie-talkie, if available, can validate simultaneous signals, but is not required.

### S2 — Candidate detection and confirmation

Group adjacent elevated FFT bins into signals, estimate occupied width and center, qualify against configurable band/modulation constraints. Use temporal averaging, persistence, hysteresis, cooldown and ranked candidate list. Store raw/relative RF metrics without pretending to know absolute dBm. Strongest *qualified* signal first; later round-robin/first-detected.

**Gate:** CH1/CH3/CH7 accurately recognized across multiple PTT cycles; no constant false hits when idle; check weak-vs-strong discrimination.

### S3 — In-window NFM audio and resume

Demodulate chosen subchannel from the **same captured IQ window**; rackio local speaker only. Maintain correct center/selected frequency, state, audio, activity, hang, manual HOLD and SKIP. Continue FFT monitoring of current window during listening where feasible.

**Gate:** intelligible CH1/CH3/CH7 audio, correct hit attribution, auto resume, no stuck PTT, and stable start/stop. Compare CPU, latency and responsiveness against v0.4/v0.5 baseline.

### S4 — Multiple overlapping chunks, multiple banks

Add 467 MHz GMRS group then AM airband windows. Schedule separated windows with measured revisit times. Add AM decoder, realistic configuration, service limitations. Keep CB/AMB/FIRE disabled until valid hardware/channel plans exist.

### S5 — Appliance hardening

Persistent user config/history, diagnostic traces, truthful signal/radio-state indicators, robust USB/audio cleanup, tested multi-browser synchronization, optional auto-start/kiosk, security for broader access. Remote/browser audio only by future explicit choice.

## Test and workflow policy

- User directs product design and verifies RF behaviour on rackio; make **small, reversible commits**.
- **Keep the working `MANAGED_1_7` profile** and native `rtl_fm` as regression controls.
- Only one tuner-owner at a time; close GQRX before testing.
- Record observed rates separately from nominal USB sample-rate/FFT estimates.
- Do not relabel fixed 5/3 dB persistent contrast thresholds as legacy squelch=15.
- No code/UI changes for S1 yet; this documentation cleanup is **planning only**.

## Prior history

The incremental v0.1–v0.5 command/debugging narrative has been consolidated into the table above. All original details and intermediate commits remain in Git history. Notable preserved issues: PLL warning during `rtl_test -t` (not proven persistent failure), old v0.4 no-resume bug (fixed), and optional Python wrapper symbol mismatch (fixed).

## S1 code candidate — 2026-11-11

Implemented **`sdrbox/spectrum.py`**, an isolated FFT-only worker using one open `pyrtlsdr` receiver at 462.650 MHz / 2.048 MS/s. Reads 32768 IQ samples, computes eight 4096-point Hann-window FFTs, averages power, estimates a local 25th-percentile baseline over 201 FFT bins, and down-samples into 512 bins for browser display. Uses a ~1.70 MHz center crop (needs empirical passband validation), refreshes around 2–3 Hz, shares UI via state/WebSocket. No audio/hits/auto-selection. Added SPECTRUM_462 profile and live/GMRS-zoom canvas. **Not yet field-tested on rackio.** All pre-existing radio backend profiles preserved.

## S1 live-refresh regression, fix candidate — 2026-11-11

Field test: S1 FFT graph rendered and showed a genuine CH1 PTT peak at the correct frequency, but stopped refreshing after its first snapshot. Root cause: generic `cycle()` watchdog mistakenly checked whether legacy `rtl_fm` was alive during `SPECTRUM_462` sessions; because there is intentionally no rtl_fm subprocess in S1, it set ERROR after ~1 s and subsequent FFT events were ignored. Updated watchdog to apply only to `SCAN_1_7` and `FIXED_1`, and added separate spectrum-worker liveness reporting. **Code committed, live-refresh fix awaiting rackio retest.**
