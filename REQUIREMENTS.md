# SDRbox requirements — single display and web-server scanner

**Updated 2026-11-08. Specification only, not implemented.**

## Goal

Provide a **scanner appliance first**, driven by a NooElec NESDR Smart on **Linux Mint / rackio**, with **one 1280×400 local touchscreen** and a responsive LAN web interface. The removed 1U status monitor is **not part of the project**.

## Functional acceptance criteria

| ID | Requirement | Acceptance |
| --- | --- | --- |
| R01 | Python **FastAPI** server starts on rackio, independent of browser windows | Health/status API and local/remote web pages accessible |
| R02 | **One Chromium fullscreen kiosk/app window** fits the **1280×400** panel | All primary controls/info visible; no Home screen vertical scroll |
| R03 | One screen contains status, current tune/mode, signal, recent hits and large buttons | No dependency on a separate `/status` display |
| R04 | Independent CB/GMRS/AIR/AMB/FIRE bank toggles | Several can be on simultaneously; survive restart |
| R05 | SCAN/HOLD/SKIP/SETTINGS operate reliably | Distinguish manual HOLD from automatic pause |
| R06 | Prioritize AIR 118.000–136.975 MHz | Known channels and measured window plan available |
| R07 | AIR AM receiver automatically stops for plausible activity | Intelligible AM audio heard through **rackio's local sound output** |
| R08 | Detection has threshold/hysteresis, confirmation, squelch and hang time | Avoid repeated false pauses/chatter; resume after silence |
| R09 | Scan can use known channels, with FFT chunk discovery later | Performance measured, not guessed |
| R10 | AM/NFM configuration per channel/window | Known airband and simple NFM tests succeed |
| R11 | Real recent-hit log with time, frequency/bank, duration | No simulated hit entries displayed as real |
| R12 | Browser controls work from other devices on home LAN | One shared scanner state; rack view updates when remote toggles |
| R13 | Status propagates via WebSocket + snapshot/reconnect | Clients recover consistently after reload/disconnect |
| R14 | Browser close/disconnect does **not** stop scan/audio | Scanner runs until controller/server intentionally stops |
| R15 | Graceful receiver-busy/missing/audio errors | Local and remote browsers show meaningful state |
| R16 | Single receiver hardware ownership, validated serialized commands | No race between remote and local browser controls |
| R17 | Single-screen touch accurate after upper display removal | Verify four corners and current XRandR output |
| R18 | LAN-only by default | No public port forwarding; validate mutating requests/origins |

## UX requirements

- Target native **1280×400**. One compact scanner page should accommodate title/status, **five wide toggle tiles**, frequency+meter, recent hits, and SCAN/HOLD/SKIP/SETTINGS buttons without scrolling.
- Use the **approved photorealistic option #2** (see [UI.md](UI.md)) for styling: dark premium industrial, bright green active states, high-contrast readable text.
- Implement in **HTML/CSS/JavaScript**, served by FastAPI. No PySide6 or second local monitor.
- Remote `/` page adapts to desktop/tablet/mobile while remaining one shared application.
- Confirm actual browser viewport and touch mapping on the live rack before setting fixed font/target sizes.

## Hardware / radio requirements

- One **NESDR** is the receiver for v1; adapter contract permits **future RSP1A**.
- Nominal ~2.4MS/s span must be measured; overlap FFT windows. One hardware tuner cannot listen to separated bands simultaneously.
- AIR initial scope is analogue AM voice. GMRS NFM and CB/AMB/FIRE banks come after proven airband scanning.
- No claims that local FIRE/AMB agencies are analogue or monitorable without research and testing.
- Local audio must work without a browser connection. Browser audio streaming is **phase 2**, not v1.
- Persist user-selected bank switches and scanner settings (YAML/JSON), with SQLite for hit history when needed.

## Deferred features

Browser audio streaming, automatic recordings/replay, favourites/lockouts, advanced FFT waterfall, physical knob, dedicated speaker, improved antenna placement, digital/trunked decoding, RSP1A migration, and polished boot-to-appliance. Encrypted traffic is not a target. No transmission functionality.

## Test philosophy

Validate both simulated frontend behaviours and real RF behaviour separately. Avoid fabricated scan times, dBm, hit entries or local service frequencies; document measurements on the actual Dell.
