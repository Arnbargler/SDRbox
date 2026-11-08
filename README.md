# SDRbox

SDRbox is a **receive-only, scanner-first radio appliance** built around a Dell OptiPlex running **Linux Mint** and a **NooElec NESDR Smart (RTL-SDR)**.

**2026-11-08 hardware decision:** the upper 1U display has been **removed**. There is now **one local 2U touchscreen, 1280×400 pixels**, for both information and controls. The web-server architecture remains unchanged.

> **Status:** GQRX has received FM broadcast and activity around 118.800 MHz. No custom SDRbox scanner, FastAPI server, Chromium kiosk, or live web UI has yet been implemented. Mockup values are fictional demonstration data.

## Selected design: photo option #2

The user approved the **second single-display mockup** from the three 2026-11-08 options, with polished dark industrial styling, five green/grey bank switches, frequency/meter, recent hits and large SCAN/HOLD/SKIP/SETTINGS controls.

![Approved SDRbox option 2 preview](assets/scanner-mockup-option-2.webp)

The photo is a design reference, **not a screenshot of running SDRbox software**. See [UI.md](UI.md).

## Intended operation

- **Rackio** runs one Python scanner backend plus a **FastAPI** HTTP/WebSocket server.
- **One local Chromium browser** occupies the 1280×400 touchscreen, using `/control` or `/`.
- Other computers/phones/tablets on the **home LAN** use the same server through a responsive `/` page; every browser shares one scanner state and tuner.
- **Local speaker audio on rackio first**. Optional audio through remote browsers **later**.
- Independently enable scanning **CB, GMRS, AIR, AMB, FIRE** banks. Each bank contains known channels and/or RF windows, not necessarily one contiguous frequency span.
- **Airband first** (118.000–136.975 MHz). Validate conventional known-channel AM scanning, then FFT-based discovery across overlapping windows.
- Proposed server address `http://rackio.local:8080` is **not yet running**. LAN-only initially; no public Internet exposure.

## Project documents

| Document | Purpose |
| --- | --- |
| [HANDOFF.md](HANDOFF.md) | **Start here** for next AI/developer |
| [HARDWARE.md](HARDWARE.md) | Known hardware and checks |
| [TOUCHSCREEN.md](TOUCHSCREEN.md) | Single-screen touch setup and retired dual-screen config |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Modular Python scanner and web server |
| [WEB_API.md](WEB_API.md) | Proposed REST/WebSocket commands and shared state |
| [UI.md](UI.md) | Approved **option #2** and 1280×400 single-screen layout |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Acceptance tests |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Incremental milestones |

## Principles

1. Scanner appliance first, advanced SDR laboratory second.
2. **One physical touchscreen**, not two. No separate status-monitor browser.
3. **One receiver/controller**, regardless of connected browsers; browser closing must not stop scanning.
4. Keep GQRX as diagnostic baseline (but never compete for the NESDR simultaneously).
5. Reuse established SDR/DSP libraries and keep a future RSP1A adapter possible.
6. Do not confuse illustrations or performance estimates with measured results.
7. Short, testable milestones; user guides UI decisions and field tests.

<https://github.com/Arnbargler/SDRbox>
