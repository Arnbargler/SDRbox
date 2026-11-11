> **Implementation update 2026-11-11:** FastAPI + shared simulator + browser UI now exist; [RUNNING.md](RUNNING.md) is the current usage guide. GMRS/NFM with a walkie-talkie is the first planned live test, not AIR. Use ordinary local/remote Chrome browsers; kiosk/headless startup is optional later. No network audio. Some planning text below predates this decision.

# SDRbox UI — approved single-screen design

**Decision date: 2026-11-08.** User physically removed the upper 1U monitor and selected **option #2** from three new single-display photo concepts.

## Approved image

![Approved photo mockup #2](assets/scanner-mockup-option-2.webp)

**The second mockup** is the premium, dark/glossy **one-screen tec MOJO rack** with a Dell OptiPlex below. Original generated image: `neon_green_sdr_scanner_rack_unit.png` (1448×1086 illustration). The repo includes a compressed preview of the actual image. It is **not** a running application screenshot; displayed signal values, dates, service frequencies and recent hits are illustrative.

The old two-screen SVG has been **removed from the current branch**; it survives only in Git history and is not current design guidance.

## Physical display

| Item | Current design |
| --- | --- |
| Only local screen | **2U touchscreen — 1280×400 px** |
| Upper 1U | **Removed**; no informational-only panel |
| Local app | **One** Chromium fullscreen/app window showing web control page |
| Remote interface | Responsive version of same page on any LAN browser |

Previously the retained display was `HDMI-2`, at `+59+280` when paired with the upper monitor. **Current output name, origin, display scaling and touch behaviour after physically removing the other panel need rechecking**. Do not assume the old geometry survived. See [TOUCHSCREEN.md](TOUCHSCREEN.md).

## Browser routes and layout

- Local: `/control`, potentially the same template as `/` with a compact 1280×400 layout.
- Remote: `/` with responsive design.
- **No local `/status` page or second Chromium kiosk window.** If a read-only status web page is later useful remotely, it is optional rather than required by hardware.
- Same authoritative FastAPI scanner engine drives all pages. WebSockets keep state synchronized; reconnect fetches a snapshot. The browser is a client, not the owner of the SDR.
- **Audio v1 comes out of rackio's local speakers**; browser playback is later.

## Home screen at 1280×400

Fit everything below **without vertical scrolling**:

1. **Thin header:** SDR Scanner, current operating/connection state and settings access.
2. **Five large independent toggle tiles:** CB / GMRS / AIR / AMB / FIRE. Green = enabled in scan rotation; grey = excluded. Multiple tiles can be enabled at once.
3. **Main left:** large current frequency, current bank, AM/NFM, signal meter. Use relative signal indication if dBm calibration is unavailable.
4. **Main right:** compact recent activity (time, channel/frequency, bank, duration). Only genuine logged hits in live mode.
5. **Bottom row:** large SCAN, HOLD, SKIP, SETTINGS buttons with generous touch targets. SCAN is most prominent.
6. Secondary pages/panels handle bank editor, channels, squelch, volume, receiver diagnostics and optional FFT spectrum view.

### Interaction requirements

- HOLD differs from pausing automatically on a received signal.
- SKIP temporarily leaves an active channel; optional cooldown/lockout is separate.
- Bank changes made locally or remotely update all clients through the shared server.
- Show scanner errors and stale/disconnected state honestly, rather than inventing levels or hits.
- Simulated frontend test mode must be visibly identified as simulated.

## Frontend technology

Plain **HTML5 / CSS Grid / Flexbox / JavaScript ES modules** is the preferred starting point, served by FastAPI on Linux Mint. Avoid PySide6 and a duplicate local interface. Chromium fullscreen/kiosk geometry must be tested on the physical 1280×400 panel before designing desktop autostart.

Use restrained premium charcoal styling, glossy panels sparingly, vibrant green active toggles, high contrast and large type. The photo is a **visual target** rather than artwork to slice up.

## Image housekeeping

The new option #2 supersedes the old two-monitor SVG. Keep the full-resolution generated PNG as the ultimate photo reference if it is later uploaded in full to the repository; the compressed preview is enough for README visibility now.
