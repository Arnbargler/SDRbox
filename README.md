# SDRbox

**SDRbox** is a compact, Linux-based **radio scanner appliance first**, with SDR exploration as a secondary/advanced mode. The project uses a Dell OptiPlex in a small rack with a narrow **1U status display** above a larger **2U control display**. It currently runs **Linux Mint** and receives with a **NooElec NESDR Smart (RTL-SDR)**. An **SDRplay RSP1A** may replace the dongle later; v1 must not depend on that upgrade.

> **Status — 2026-11-07:** Hardware and GQRX reception proven; **no custom scanner software exists yet**. A live signal was observed around **118.800 MHz** in the aviation band. The screenshots below are **design concepts**, not screenshots of functioning SDRbox software.

![Approved scanner appliance UI concept](assets/scanner-ui-concept.svg)

The user-approved photorealistic concept shows the same layout without the temporary external antenna/dongle. The SVG above is a repo-hosted, simplified, editable representation; the original high-resolution PNG should be added to `assets/` when available (see [UI.md](UI.md)).

## Intended operation

- Switch band **banks** on/off using large touchscreen toggles: **CB**, **GMRS**, **AIR**, **AMB**, **FIRE** (and HAM later).
- A bank contains configured frequency **windows/chunks** or known channels. Selecting more than one bank includes their windows in the scan rotation. **Banks are not necessarily one contiguous RF span.**
- Scan approximately **2 MHz usable portions** of spectrum per RTL-SDR retune, detect likely activity using FFT energy relative to the noise floor, stop and demodulate the candidate (AM/NFM as configured), then resume after silence.
- Keep the upper 1U display on persistent high-contrast **frequency / mode / signal / scanning-or-hold state**.
- Keep the middle 2U screen touch-first: bank toggles, current tune, signal meter, recent hits, and **SCAN / HOLD / SKIP / SETTINGS**.
- Prioritize real reception and stable scanner behaviour over an elaborate spectrum laboratory UI.

## Documentation map

| File | Read it for |
| --- | --- |
| [HANDOFF.md](HANDOFF.md) | **Start here next session** — verified status, decisions, immediate next steps |
| [HARDWARE.md](HARDWARE.md) | Physical rack, PC, displays, SDR, radio tests, unknowns |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Functional requirements and acceptance tests |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Proposed receiving/scanning pipeline, band model, constraints |
| [UI.md](UI.md) | Approved design, layout and controls |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Staged build/test workflow and technical investigation |

## Principles

1. Scanner appliance, not generic desktop SDR UI.
2. Keep existing Linux Mint and GQRX usable as a known-good diagnostic baseline.
3. Do **not** confuse concept art, expected frequencies, or estimated performance with field-verified results.
4. Use established SDR/DSP libraries instead of reinventing AM demodulation and device drivers.
5. Keep NESDR and future RSP1A behind a replaceable hardware interface.
6. Work in **small, testable increments**; verify one milestone before piling on more.
7. Receive only; no transmission functionality planned.

## Repository

<https://github.com/Arnbargler/SDRbox>
