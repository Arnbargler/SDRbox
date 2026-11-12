# Rackio — single 1280×400 touchscreen (verified)

**Verified 2026-11-11.** The former 1U 1424×280 upper display was physically removed. One 2U 1280×400 screen remains and provides both scanner status and touch controls.

After removing the legacy dual-monitor startup script and rebooting, rackio reported:

```text
Monitors: 1
0: +*HDMI-2 1280/597x400/336+0+0 HDMI-2
```

Touch accuracy was confirmed; **no custom XInput mapping required**. Retired files were `~/.config/autostart/rackio-touch.desktop` and `~/.local/bin/rackio-touch.sh`. They were removed and checked for leftover startup references. Do not restore the old scripts from Git history.

If display/touch configuration changes, check:

```bash
DISPLAY=:0 xrandr --listmonitors
DISPLAY=:0 xinput list
```

The previous two-panel mapping (`HDMI-1 1424×280 +0+0`, `HDMI-2 1280×400 +59+280`) is **obsolete**. XInput device IDs and `/dev/input/eventN` are unstable across boots.

Use an ordinary Chrome/Chromium browser at `http://localhost:8080` for now. One optional fullscreen/kiosk window may be configured later; neither a second monitor nor a second page is required. Browser audio is not part of this phase.
