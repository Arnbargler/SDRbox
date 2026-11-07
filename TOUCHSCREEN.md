# Rackio dual-screen touchscreen configuration

**Status: working interactively on 2026-11-07; autostart/reboot persistence not yet confirmed.**

SDRbox runs on Linux Mint on `rackio.local`. The user wanted the **upper 1U display to be informational only** and the **lower 2U display to provide accurate touch control**. A manually tested XInput configuration now achieves exactly that.

## Confirmed monitor layout

| Physical monitor | XRandR output | Resolution | Position in combined desktop | Intended behavior |
| --- | --- | --- | --- | --- |
| Upper 1U | `HDMI-1` | **1424×280** | `+0+0` | **No touch input** |
| Lower 2U | `HDMI-2` | **1280×400** | `+59+280` | **Touch enabled and accurate** |

Output IDs and positions were verified with `DISPLAY=:0 xrandr --listmonitors`. The offset of the lower display means touch coordinates must map to **HDMI-2** rather than the full desktop.

## Touch devices (as observed before reboot)

All devices report **`wch.cn TouchScreen`** and USB vendor/product **`27C0:0859`** (decimal `10176:2137`). Both physical screens report the *same* `ID_SERIAL=wch.cn_TouchScreen_9LQ0172005164`; therefore **serial number is NOT unique** and device names/IDs are not suitable for permanent mapping.

| Physical panel | XInput ID at test time | Input event node | udev `ID_PATH` | Type |
| --- | --- | --- | --- | --- |
| Upper 1U | 9 | `/dev/input/event5` | `pci-0000:00:14.0-usb-0:7:1.0` | Touchscreen |
| Upper 1U | 10 | `/dev/input/event6` | `pci-0000:00:14.0-usb-0:7:1.2` | Mouse emulation |
| Lower 2U | 22 | `/dev/input/event19` | `pci-0000:00:14.0-usb-0:6:1.0` | Touchscreen |
| Lower 2U | 21 | `/dev/input/event20` | `pci-0000:00:14.0-usb-0:6:1.2` | Mouse emulation |

**Crucial:** XInput IDs and `eventN` names can change after reboot. The tested script uses **physical USB paths**; these are stable as long as the same cables stay on the same ports. Mapping by serial would inadvertently match *both* screens.

## Verified test

The user manually applied:

```bash
DISPLAY=:0 xinput disable 9
DISPLAY=:0 xinput map-to-output 22 HDMI-2
```

They confirmed the lower touchscreen was accurate at all corners and the upper screen no longer responded to touches.

Next, the user created/tested the more durable `~/.local/bin/rackio-touch.sh` script, which identifies device IDs from `udevadm ID_PATH`, disables **both upper interfaces** (`1.0` and `1.2`), and enables/maps the **lower touch interface** (`1.0`) to `HDMI-2`. The user reported this test **“looks good.”**

The tested script is backed up in this repository at [scripts/rackio-touch.sh](scripts/rackio-touch.sh). It **does not** disable the lower mouse-emulation interface (USB `0:6:1.2`).

## Enable at Linux Mint desktop login

The following autostart entry was **provided to the user**, but no post-reboot confirmation has been received:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/rackio-touch.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Rackio Touchscreen Configuration
Comment=Disable upper touch and map lower touch
Exec=/home/arn/.local/bin/rackio-touch.sh
Terminal=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=3
EOF
```

Before relying on it, confirm `~/.local/bin/rackio-touch.sh` is executable (e.g., `chmod +x ~/.local/bin/rackio-touch.sh`), log out/in or reboot, then verify lower touch accuracy and upper touch disabled. This is **desktop-login autostart**, not a pre-login service; desktop automatic login is a separate future appliance decision.

## Troubleshooting and rollback

```bash
DISPLAY=:0 xinput list
DISPLAY=:0 xrandr --listmonitors
```

Manual correction on the **tested** assignment only, while those IDs remain valid:

```bash
DISPLAY=:0 xinput disable 9
DISPLAY=:0 xinput map-to-output 22 HDMI-2
```

To disable the autostart behavior:

```bash
mv ~/.config/autostart/rackio-touch.desktop ~/.config/autostart/rackio-touch.desktop.disabled
```

For **current-session** re-enabling, dynamically identify the upper touch/mouse devices and run `DISPLAY=:0 xinput enable <CURRENT_ID>` for each one. Do not blindly enable an ID remembered from a previous boot.

If either touch USB cable changes ports, update the port selectors in the script. If the monitor HDMI layout changes, review the `HDMI-2` target.

No persistent `xorg.conf` changes or `udev` rules were required.

## Web appliance integration (planned)

The SDRbox application will **not** use PySide6. A future **rackio-hosted FastAPI web server** will serve Chromium `/status` on HDMI-1 (read-only) and `/control` on HDMI-2 (touch); remote LAN browsers will use `/`. Keep this tested touchscreen mapping independent of the future Chromium kiosk autostart. **Browser window positioning, kiosk autostart and web server deployment are not yet tested or installed.** See [ARCHITECTURE.md](ARCHITECTURE.md) and [UI.md](UI.md).
