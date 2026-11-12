# SDRbox roadmap — spectrum-first

## Status (2026-11-11)

S1 spectrum capture was field-tested in v0.6: **real CH1 peak and 2–3 FFT updates per second**. v0.7 rewrites the control interface and removes traditional scanner code; **not field-tested yet**.

## Development sequence

| Milestone | Status | Verification |
| --- | --- | --- |
| S1 wideband IQ/FFT | Measured, previously verified | 462.650 MHz, 2.048 MS/s, visible CH1 peak, 2–3 updates/s |
| S1 interface redesign | Committed | Large FFT display, GMRS zoom and real diagnostics; test 1280×400 |
| S2 signal candidates | Future | Group peaks above adaptive local noise, reject DC/edge spurs and short impulses |
| S3 selection | Future | Strongest qualified signal first, hysteresis/priorities |
| S4 demod/audio | Future | Selected in-window NFM channel, rackio-local speakers, hang/resume |
| S5 windows/banks | Future | 467 MHz GMRS then AM airband, overlapping spans, measured revisit delays |
| S6 appliance | Future | Config, hit persistence, hardening and optional kiosk |

## Critical design principles

- One SDR worker, persistent USB handle, bounded IQ buffers; FFT and USB work off the FastAPI event loop.
- The displayed 1.70 MHz center crop is **provisional**, not a proven clean passband.
- Relative FFT dB and local noise floor are **uncalibrated**, not dBm.
- An unqualified strongest bin is NOT a transmission or a confirmed hit.
- Keep the UI concise for the verified 1280×400 panel, use Chrome locally or on trusted LAN.
- Old sequential scanner backends were retired as requested; retained in Git history only.
- Avoid coding automatic selection/audio until validating the new UI and measurements.

## Historical results retained in Git history

RTL_fm worked with walkie-talkie audio and squelch; Python/rtl_fm scanner ran ~1 channel/s, persistent frequency retunes ~3/s. Those prototypes were stepping stones rather than the product. An older spectrum view froze because a legacy watchdog was checking for nonexistent rtl_fm; the fix resulted in continuous 2–3 Hz FFT updates. The persistent pyrtlsdr wrapper was pinned to 0.2.91 to match rackio system librtlsdr.
