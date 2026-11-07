# SDRbox architecture proposal

_Proposed design, not existing code. Date: 2026-11-07._

## Stack

```text
Linux Mint / Dell OptiPlex
   ├── upper 1U status window       (PySide6, borderless)
   ├── middle 2U control window     (PySide6, borderless, touch-first)
   └── scanner controller / event bus
          ├── scan scheduler + state machine
          ├── configuration, bank/window/channel definitions
          ├── signal detection (FFT / power relative to noise floor)
          ├── AM and NFM demodulation + audio + squelch
          ├── recent-hit event log
          └── SDR adapter (RTL-SDR now, RSP1A later)
```

Keep Qt UI threads separate from IQ capture/DSP. Never block the UI waiting for a tuning operation, FFT or device read. Initially a single process plus worker thread/process is fine; microservices aren't required.

## Two complementary modes of scanning

**A. Known-channel scan (minimum practical baseline):** use configured aviation channel frequencies, tune/demodulate, test squelch and resume. Fastest route to a working scanner; use as reference implementation.

**B. Wide-window FFT discovery (desired differentiator):** center hardware tuner on a sample window, obtain complex IQ, estimate noise level, detect spectral candidates, map to plausible voice-channel centers, inspect/demodulate candidate, and only then move to another window. Avoid hardware retune for a signal well inside current IQ passband. CPU feasibility and false-positive behaviour must be measured.

Don't confuse a strong FFT peak with valid **AM voice**. Spur rejection, short persistence, channel raster/spacing (including **8.33 kHz aviation spacing** where relevant), adjacent-channel energy, center-frequency DC spike, AGC, and source gain all matter. Squelch should operate on filtered-channel signal, not only global FFT power.

## Airband coverage planning

- Nominal civilian aviation VHF communications band **118.000–136.975 MHz** (~19 MHz).
- At a nominal **2.4 MHz** per RTL-SDR IQ window, **8 windows is a mathematical lower bound** (19 / 2.4 ≈ 7.92), leaving no edge margin.
- Plan around **10 overlapping, approximately 2 MHz useful windows** as an initial *design estimate*, not a measured optimal number. Compute precise centers/overlap based on the dongle's tested clean usable bandwidth and frequency edges.
- All AIR windows use **AM**. AIR channels may be 25 kHz or 8.33 kHz spaced by location and service; don't hard-code 25 kHz as the universal detection step.
- Retuning/settling and detection dwell make whole-band revisits slower than `windows × dwell`; benchmark on the machine.
- Useful alternative: prefer a local **known-frequency list** first, then roam unassigned/unknown windows between visits to busy channels.

## Config model (illustrative)

```yaml
version: 1
receiver: rtl-sdr
scan:
  mode: window-discovery # or known-channels
  detection_db_over_noise: 10  # starting experiment, not guaranteed
  confirm_ms: 150              # experiment
  hang_ms: 700                 # experiment
banks:
  AIR:
    enabled: true
    modulation: AM
    range_mhz: [118.0, 136.975]
    windows: auto              # dynamically generated using measured usable span
  CB:
    enabled: false
    modulation: AM
    channels_file: channels/cb.yaml
  GMRS:
    enabled: false
    modulation: NFM
    channels_file: channels/gmrs.yaml
  AMB:
    enabled: false
    channels_file: channels/local-ambulance.yaml  # unverified until researched
  FIRE:
    enabled: false
    channels_file: channels/local-fire.yaml       # unverified until researched
```

**Important:** Do not turn illustrative emergency-service frequencies from concept art into factual coverage; local analogue/digital/trunked availability is TBD.

## Suggested state machine

```text
STOPPED → SCANNING → CANDIDATE → RECEIVING → RESUME_DELAY → SCANNING
              ↕ HOLD                         ↗
           ERROR/NO_DEVICE
```

- **SCANNING**: run scheduler across enabled windows/channels.
- **CANDIDATE**: confirm above-threshold activity, suppress known spurs, choose one voice channel.
- **RECEIVING**: demodulate to speaker, update status/log.
- **RESUME_DELAY**: let brief exchanges continue, then restart scheduling.
- **HOLD**: manual lock; scanner stays on requested channel even if silent.
- **SKIP**: advance away from hit, with limited re-trigger cooldown.
- **NO_DEVICE / ERROR**: user-visible, recoverable.

One dongle means **one tuned RF window at a time**. Multiple bank toggles choose the schedule, not simultaneous independent receivers.

## Tooling to evaluate

- GNU Radio, SoapySDR, librtlsdr / pyrtlsdr, and custom NumPy/scipy FFT for a measured proof of concept.
- `rtl_fm` / `rtl_power` can be useful small isolated experiments, not necessarily adequate for fast FFT-window discovery plus in-window multi-channel reception.
- [RTLSDR-Airband](https://github.com/rtl-airband/RTLSDR-Airband) implements aviation audio monitoring/channelization and is worth evaluating **before writing radio DSP**. Confirm features and exact scanning model against current code, not marketing claims.
- GQRX remains a diagnostics tool; do not build core production logic around screen scraping or mouse automation.

## Future hardware abstraction

Expose `open(), configure(sample_rate, gain), tune(center_hz), read_iq(), close()` (exact API TBD). Receiver-specific frequency support, rate, gain behavior, device busy state and tune settling should be capabilities, not constants.
