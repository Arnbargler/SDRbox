> **Implementation update 2026-11-11:** FastAPI + shared simulator + browser UI now exist; [RUNNING.md](RUNNING.md) is the current usage guide. GMRS/NFM with a walkie-talkie is the first planned live test, not AIR. Use ordinary local/remote Chrome browsers; kiosk/headless startup is optional later. No network audio. Some planning text below predates this decision.

# SDRbox — architecture

**Revised 2026-11-08. Planning document; no implementation exists yet.**

## Decisions

- **Modular monolith** on Linux Mint, hostname `rackio.local`: one Python scanner controller, one FastAPI HTTP/WebSocket server and a browser frontend.
- **Only one local 2U touchscreen (1280×400)**. A single Chromium kiosk/app page displays **both scanner information and controls**. Former upper 1U display and second Chromium window were removed from the plan.
- Remote computers/tablets/phones on the home LAN use the **same** web server and state through a responsive page.
- One NESDR owns the RF hardware, with a future interchangeable RSP1A adapter. No tuner per browser session.
- **Local rackio audio first**; optional remote browser audio later.
- No PySide6, Docker, microservice architecture or frontend framework required to start. FastAPI + vanilla HTML/CSS/JS ES modules is preferred.

## Component boundaries

```text
rackio (Linux Mint, Dell OptiPlex)
  NooElec NESDR / future RSP1A
        │ (one owner)
  radio/              driver, IQ, DSP, AM/NFM, squelch, audio
        │
  core/               scanner state machine, scheduler, bank/channel/window models
        │
  web/ FastAPI        validated REST commands, WebSocket events, HTML/CSS/JS
        ├── local Chromium: /control or / at 1280×400
        └── LAN browser: / (responsive)
  storage/            config, channel banks, hit history
        │
  local audio sink    rackio speaker/headphones, independent of browser lifespan
```

**One server is authoritative**. Browsers receive a complete state snapshot on initial connection/reconnect and live changes over WebSocket. Browser commands are validated and serialized by the scanner engine; changing a toggle on the rack or remotely updates all clients. Closing any browser does **not** stop scanning.

Suggested directory layout (not a requirement to create empty files prematurely):

```text
sdrbox/
  main.py
  core/
    scanner.py
    scheduler.py
    models.py
    events.py
  radio/
    base.py
    rtl.py
    detector.py
    demod.py
    audio.py
  web/
    api.py
    websocket.py
    static/
      control.html
      index.html
      css/
      js/
  storage/
    config.py
    history.py
config/
  banks.yaml
tests/
assets/
```

Implement headless scanner logic separately from browser pages so the radio is testable over SSH. Avoid blocking the FastAPI async loop with USB reads, FFT processing or audio; a dedicated worker thread/process and thread-safe command/event queue can handle it. Use a replaceable receiver protocol with open/configure/tune/read/close and runtime capabilities.

## Scan model: banks, chunks and channels

- **Bank** is a user-facing category such as CB, GMRS, AIR, AMB, FIRE.
- A bank contains configured **known channels** and/or sampled spectrum **windows**, with AM or NFM demodulation per relevant entry.
- Each toggle independently includes/excludes its bank from the schedule. Deduplicate overlapping windows/channels.
- A single NESDR cannot simultaneously monitor geographically/ spectrally separated windows. More banks imply longer revisit delay.
- **Known-channel airband scanning first** to demonstrate real AM audio, squelch, pause, hold and resume.
- Then prototype **wide-window FFT discovery**: tune center, collect IQ, estimate noise floor, detect signal candidates, reject DC/LO spur and interference, confirm likely AM voice before stopping/listening.
- Prefer demodulating within the current IQ window rather than retuning when possible. Benchmark on the Dell rather than assuming speed.

## Airband planning

- Civilian VHF voice: **118.000–136.975 MHz**, approximately **19 MHz**.
- Nominal NESDR complex sampling ~**2.4 MS/s**, which does NOT imply full 2.4 MHz perfectly usable passband.
- Eight windows is a mathematical floor at 2.4 MHz with no overlap; **around ten overlapping ~2MHz useful windows** is an initial design hypothesis.
- Confirm channel raster/spacing appropriate to actual region and services (25 kHz and 8.33 kHz where used), center spur, usable edges and tuning/settling latency.
- Use relative **noise-floor thresholds**, signal persistence, hysteresis and voice confirmation; do not assume every FFT peak is useful audio.
- Local emergency services may be digital, trunked and/or encrypted; demo mockup labels are not authoritative frequency lists.

## State machine

```text
STOPPED → SCANNING → CANDIDATE → RECEIVING → RESUME_DELAY → SCANNING
             ↕ HOLD                    ↗
          ERROR / NO_DEVICE
```

- **SCANNING:** schedule enabled banks/windows.
- **CANDIDATE:** short confirmation; suppress false peaks.
- **RECEIVING:** AM/NFM decode to local audio, log confirmed hit.
- **RESUME_DELAY:** let channel fall silent with configurable hang time.
- **HOLD:** intentional user lock (not squelch pause).
- **SKIP:** move on and optionally temporarily ignore same channel.
- **ERROR/NO_DEVICE:** visible in all local and remote browser clients.

## Sound and networking

**Phase 1 sound:** PCM audio decoded from SDR and played on rackio's local audio output (through existing Linux sound system). Playback must not depend on a browser remaining connected.

**Later sound:** add separate streaming sink and browser player. Codec/protocol and autoplay/latency handling are future design work, not blockers.

**LAN only initially**. Proposed `http://rackio.local:8080` is not deployed. Keep control commands validated, restrict untrusted origins, and do not expose to public Internet without deliberate authentication/security work. See [WEB_API.md](WEB_API.md).

## Evaluate before building DSP from scratch

GQRX remains known-good comparison. Consider librtlsdr / pyrtlsdr, GNU Radio, SoapySDR, `rtl_fm` / `rtl_power`, and [RTLSDR-Airband](https://github.com/rtl-airband/RTLSDR-Airband) as sources of existing functionality; verify suitability on Linux Mint and desired FFT detection. Never run GQRX and SDRbox against one NESDR simultaneously.
