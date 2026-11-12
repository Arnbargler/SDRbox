# SDRbox interface — approved single-screen design

**Status 2026-11-11:** The real FastAPI/HTML/CSS/JS page exists and operates in normal Chrome. The approved photo is an inspiration image, **not** a screenshot or measured signal display.

![Approved option #2 design reference](assets/scanner-mockup-option-2.webp)

## Hardware and style

One HDMI-2 **1280×400** 2U touchscreen, dark charcoal/green industrial styling, large touch-friendly buttons. No upper 1U display, no second kiosk/window, no mandatory headless configuration.

Same browser page served as `/` and `/control` locally on rackio and remotely from trusted home LAN. One backend owns the receiver; browser disconnect does not intentionally stop it. Audio on rackio, not browser.

## Existing interface

- Five bank toggle tiles: CB / GMRS / AIR / AMB / FIRE (only GMRS genuinely implemented for live reception).
- Large channel/frequency readout, modulation, activity state, hit list, SCAN / STOP / HOLD / RESUME / SKIP / INFO.
- INFO contains current receiver profile and squelch adjustment; persistent profile uses its own hardcoded RF thresholds unrelated to the old rtl_fm slider.
- WebSocket updates state and connection. Simulated activity is visibly marked.

## Next UI requirements for spectrum-first mode

The primary display should distinguish **(a) scanned window span/center**, **(b) candidate signal frequency**, and **(c) selected audio frequency**. These are not interchangeable. Show actual FFT-derived activity/relative noise contrast, not decorative percentages. A compact candidate list or mini-spectrum can replace/reorganize the current signal meter and recent activity if necessary, but do not redesign the 1280×400 interface before discussing mockups with the user.

- Indicate window scanning, candidate confirmation, audio listening, manual HOLD, scan resume and errors clearly.
- Show strongest qualified candidate first; a list can expose other concurrent peaks.
- Display true, timestamped confirmed hits separately from transient peaks and simulation.
- Retain large controls and readability at 1280×400. Keep advanced spectral diagnostics behind INFO or another secondary panel if the main layout becomes crowded.

## Deferred

Kiosk/autostart, remote-browser audio, full waterfall/spectrum lab UI, additional displays, recording UI and physical knobs.
