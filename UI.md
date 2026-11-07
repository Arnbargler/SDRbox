# UI design and approved mockup

_Last reviewed: 2026-11-07._

## Design decision

The user **approved the first mockup**, then specifically requested the same first mockup **with the external antenna and visible SDR equipment removed**. It shows a polished dark, green-accented scanner appliance mounted in the real-style rack, not a general-purpose SDR workstation.

![Editable SVG representation of approved mockup](assets/scanner-ui-concept.svg)

**Image provenance:** This SVG is a simplified repository-native layout representation. The approved high-resolution photorealistic concept is a generated PNG from the conversation, **not yet committed here as a binary image**. Add the exported image to `assets/scanner-appliance-mockup.png` when available and change the image reference if preferred. Don't claim this vector is the exact approved PNG.

## Confirmed physical display geometry

| Panel | Native resolution | Approximate aspect ratio | UI responsibility |
| --- | --- | --- | --- |
| **Upper 1U** | **1424 × 280 px** | **5.09:1** | Permanent, read-only scanning status |
| **Lower 2U** | **1280 × 400 px** | **3.20:1** | Touch-first home controls, banks, recent hits |

These pixel dimensions are **user-confirmed**. Actual Linux Mint display IDs, placement, scaling, touch device mapping, and whether the touch panel is correctly calibrated still need testing with `xrandr` and input tools. The reference concept art is *not* pixel-accurate; implement to these real window sizes.

## Physical display split

### Top: 1U / status window

Persistent, glanceable and read-only in normal use:
- SDR Scanner identity / compact icon
- SCAN / RECEIVING / HOLD / ERROR
- current **frequency** displayed prominently
- relative signal meter and (if genuinely calibrated) dBm; otherwise show relative units
- active bank and modulation if space permits

No system menus or Linux desktop widgets in appliance view.

### Middle: 2U / touch controls

**First screen (primary):**

- Header: SDR Scanner — Home Scan.
- Large toggle tiles: **CB**, **GMRS**, **AIR**, **AMB**, **FIRE**; green indicates included in scan rotation, grey indicates disabled. These are **independent toggles**, not a one-at-a-time radio-group selector.
- Center: current frequency, bank, modulation, signal indication.
- Right: recent hits (time, frequency, bank, duration).
- Bottom: **SCAN**, **HOLD**, **SKIP**, **SETTINGS**.

**Secondary screens (not all at once):** bank editor, per-bank chunk list, channel inclusion/exclusion, threshold/dwell/resume settings, audio, and eventual advanced spectrum view.

## Interaction semantics

- Toggle a bank on/off even while scanning; scheduler rebuilds safely at next boundary.
- SCAN starts/resumes. If no banks are selected, show a clear instruction.
- HOLD freezes listening; distinguish manually held from a voice-triggered auto pause.
- SKIP advances from a live hit. Use a short cooldown before revisiting the same signal.
- Recent-hit tap selects/holds that frequency as a future enhancement; in v1 it's okay to display only.
- The display must still be usable if a physical antenna rod momentarily obscures it during bench testing, but the permanent plan is a remote antenna.

## Theme and implementation

Use **PySide6** native two-window design on Linux Mint, sized for **1424×280** (upper) and **1280×400** (middle). Dark charcoal, readable off-white typography, selective vivid green for active toggle/scan state. Build a compact **single-screen Home layout** at 1280×400: a shallow header, one row of five large on/off bank tiles, a current-frequency/signal-and-recent-hits row, and bottom SCAN/HOLD/SKIP/SETTINGS controls. Do not rely on vertical scrolling on the Home screen. Use separate views for advanced settings. The narrow top panel should use large status typography across its ~5.09:1 span. Verify display coordinate placement and touchscreen mapping, not pixel dimensions. Keep status aligned with real scanner events, not fabricated signal strength or random hit entries.

## Mockup asset handling

An exact high-resolution, antenna-free PNG was generated in the conversation. The user can save it locally and add to this repo as `assets/scanner-appliance-mockup.png`:

```bash
mkdir -p assets
cp /path/to/downloaded/polished_rack_mounted_sdr_scanner.png assets/scanner-appliance-mockup.png
git add assets/scanner-appliance-mockup.png
git commit -m "docs: add approved scanner-appliance mockup"
git push
```

The PNG is **concept art** with illustrative frequencies, UI values, date, and recent-hit rows; these are not measured scan results, nor validated local CB/FIRE/AMB band assignments.
