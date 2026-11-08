# Rackio touchscreen — single 1280×400 panel

**Updated 2026-11-08. The upper 1U monitor is gone.**

## Current goal

Maintain **one accurately working local touchscreen**: the **2U 1280×400** panel. No separate status display, no two-monitor coordinate offset and no need to disable the upper touchscreen.

The user was previously instructed to remove the dual-screen startup config and reboot:

```bash
rm -f ~/.config/autostart/rackio-touch.desktop
rm -f ~/.local/bin/rackio-touch.sh
sudo reboot
```

**Not yet confirmed:** whether the above was executed, whether a clean reboot happened, and whether the lower screen is accurate when used alone. Do not state that touch is proven after the hardware change.

## Verify the current single monitor

After desktop login, via SSH:

```bash
DISPLAY=:0 xrandr --listmonitors
DISPLAY=:0 xinput list
```

Expect **one** active monitor, 1280×400. The new output name and desktop origin still need to be observed; `HDMI-2` and `+0+0` are plausible but should **not** be invented.

Test four corners and center. If accurate, **leave Linux Mint's default touch mapping alone**. Only if inaccurate, identify the lower touchscreen using touch events and map to the one *currently reported* XRandR output:

```bash
DISPLAY=:0 xinput test-xi2 --root
# Identify current ID from physical touches, then:
DISPLAY=:0 xinput map-to-output CURRENT_TOUCH_ID CURRENT_OUTPUT
```

Do not run the second line literally; replace the placeholders after inspection.

## Historic dual-screen correction — obsolete

Previously Linux Mint reported:

| Physical screen | Old monitor output/position | USB physical path |
| --- | --- | --- |
| Upper 1U, removed | HDMI-1, 1424×280 +0+0 | `...usb-0:7:1.0` touch and `...:1.2` mouse |
| Lower 2U, retained | HDMI-2, 1280×400 +59+280 | `...usb-0:6:1.0` touch and `...:1.2` mouse |

Both presented identically named `wch.cn TouchScreen` interfaces (USB vendor/product `27C0:0859`, identical serial number), so we previously used USB physical paths instead of numeric IDs. The earlier script disabled the upper interface and mapped the lower to HDMI-2; it **worked on the former dual-monitor setup** but is **retired**.

Do **not** restore `scripts/rackio-touch.sh` from older Git commits. XInput device IDs and `/dev/input/eventN` are not stable across boots.

## Web browser appliance

With one screen, configure **one local Chromium kiosk/fullscreen window** for SDRbox's control page once the web server exists. Touch handling is native Linux Mint + browser behaviour, not PySide6. Remote browsers on the LAN do not require any local touch device.

**Pending field test:** reboot, verify one XRandR monitor and accurate touch, then update this doc with actual output name/coordinates and whether any mapping script remains necessary.
