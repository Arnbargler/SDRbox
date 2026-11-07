# SDRbox architecture proposal

_Proposed design, not existing code. Date: 2026-11-07._

## Agreed architecture: local web server + LAN clients

**Decision (2026-11-07):** SDRbox is a **web-server-style scanner appliance**, not a PySide6 desktop application. **Linux Mint** stays on `rackio.local`. One Python scanner engine controls the NooElec NESDR and produces **local audio on rackio**. A **FastAPI** web application serves HTML/CSS/JavaScript and provides commands/status to any browser on the home LAN.

```text
rackio.local — Linux Mint / Dell OptiPlex
  NooElec NESDR (one owner; GQRX must be closed)
            │
  Python radio backend (IQ, tuning, AM/NFM, FFT, squelch)
            │
  Scanner state machine + scheduler + event bus
            ├── Local audio output on rackio (v1)
            ├── Bank/channel config + hit history (YAML/JSON, SQLite)
            └── FastAPI server: REST commands + WebSocket state events
                      │
             HTTP/WebSocket over home LAN
               ├── rackio Chromium /status  → 1U 1424×280 (read-only)
               ├── rackio Chromium /control → 2U 1280×400 (touch)
               └── any home browser /        → responsive full scanner UI
```

**One application/backend, many browser views**: the two local display pages are served by the same web application as remote pages. There is **no separate local application** to maintain and browsers do not own the SDR hardware. Disconnecting a browser must **not** stop scanning. All browser commands go to the authoritative shared scanner controller; state is broadcast to every connected UI. A server restart may stop scanning; eventual appliance startup/recovery policy is separate.

## Component boundaries (proposed, not yet created)

```text
sdrbox/
  main.py                 # compose receiver, scanner, audio and FastAPI app
  core/
    models.py             # shared scanner / bank / channel / window contracts
    scanner.py            # scan state machine, errors, lifecycle
    scheduler.py          # channel and window selection
    events.py             # state snapshots and events
  radio/
    base.py               # hardware adapter protocol/capabilities
    rtl.py                # NESDR adapter
    detector.py           # FFT / noise floor / signal candidate detection
    demod.py              # AM/NFM DSP, or wrapper of proven receiver engine
    audio.py              # rackio local PCM audio output, squelch/mute
  web/
    api.py                # validated commands, health and status endpoints
    websocket.py          # live state/event fanout, snapshot on connect
    static/
      status.html         # upper 1U read-only display
      control.html        # lower 2U touch control
      index.html          # responsive LAN browser interface
      css/                # layout, styles, CSS Grid/Flexbox
      js/                 # ES modules for controls, state and API client
  storage/
    config.py             # bank definitions and persistence
    history.py            # activity log (SQLite)
config/
  banks.yaml              # bank and frequencies (example)
tests/                    # fake backend, recorded IQ, scanner/UI tests
assets/                   # reference mockups
```

This is a **modular monolith**, not microservices. Use a worker thread/process or existing native DSP tooling for continuous IQ/audio so blocking RF reads never stall FastAPI's event loop or web updates. The radio controller must serialize device changes. Keep UI-independent headless operation for debugging.

### Recommended technologies, subject to local validation

- Backend: **Python + FastAPI** (ASGI, Uvicorn for development/serving).
- Live state: **WebSocket** events; send a complete snapshot on connection/reconnection; REST GET for basic status and POST for commands.
- Frontend: **plain HTML5, modern CSS and vanilla JavaScript ES modules** first. No frontend bundler/framework unless complexity actually requires one. Serve static assets from rackio.
- Local UI: two **Chromium kiosk/app-style windows**, one per monitor. Proper window geometry, hiding browser chrome, startup ordering and screen placement must be verified on Linux Mint.
- Data: human-readable YAML/JSON configuration; **SQLite** for recent hit history.
- RF: proven RTL-SDR/Linux libraries or existing DSP engines; adapter keeps future SDRplay RSP1A possible.
- **Audio phase 1:** decoded audio plays through rackio's own speaker/audio output. **Browser audio streaming is future work**, not an initial requirement; design audio output as a separate sink so it can later be duplicated/streamed without restructuring radio logic.

### State, concurrency and security

- The **server is authoritative**. The UI must never invent signal readings or show optimistic changes as confirmed receiver state. Return command acknowledgment/errors, then broadcast actual state.
- Multiple local/remote clients see the same selected banks, frequency, scan state, volume and recent hits. Handle concurrent commands deterministically (server-side serialized queue/state machine); no one browser owns the session.
- A client connecting late receives a full snapshot, then deltas/events. A disconnected page reconnects; the radio keeps operating.
- Provide health/error status when SDR missing/busy, audio failing or radio stopping.
- Initial access is **home LAN only** (proposed address such as `http://rackio.local:8080` is **illustrative, not deployed**). Do not expose this unauthenticated control interface to the public Internet or forward router ports. Add authentication/access controls before widening network access; validate WebSocket origins and mutating requests as part of implementation.
- Start with local rackio audio only, then evaluate latency, encoding and browser playback constraints for remote streaming.

See [WEB_API.md](WEB_API.md) for provisional endpoints, events and multi-client rules, and [UI.md](UI.md) for the display-specific browser layout.

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
