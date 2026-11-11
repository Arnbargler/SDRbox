# SDRbox hardware and verified environment

**Updated 2026-11-08.** Separate what the user has confirmed from what still needs testing.

## Current installation

| Item | Current state |
| --- | --- |
| Host | **rackio.local**, Dell OptiPlex 5060 Micro in tec MOJO rack, 8 GB RAM; CPU details not reverified |
| OS | **Linux Mint**, not Xubuntu |
| **Only local display** | **2U touchscreen, 1280×400 pixels** |
| Former upper display | **1U 1424×280 monitor physically removed** on 2026-11-08 |
| SDR | **NooElec NESDR Smart**, older RTL-SDR-family USB device |
| Existing test application | **GQRX**, operational |
| Future app | Python scanner + FastAPI server + **one local Chromium window**, not implemented |
| Audio plan | Decoded audio **through rackio's local sound output first**; browser streaming later |
| Antenna | Temporary telescoping test antenna; remote antenna planned |
| Future hardware | SDRplay RSP1A, physical knob, external speaker — not v1 blockers |

## RF verification

- GQRX received broadcast FM.
- User reported positive airband reception activity at **118.800 MHz**.
- Selecting the Realtek input rather than generic RTL source helped correct apparent tuning offset.
- Earlier GMRS/FRS channel 1 walkie-talkie audio test succeeded after reducing latency.
- **No** headless scanner, airband scan algorithm, custom audio backend or FFT chunk discovery is implemented yet.

## Single-monitor setup: needs post-removal check

Old dual-monitor XRandR mapping (historical only):

```text
HDMI-1 1424x280 +0+0     # upper monitor, NOW REMOVED
HDMI-2 1280x400 +59+280  # lower monitor, physically remains
```

**Do not assume** the remaining monitor still has the same name or position after removing the upper panel. Run:

```bash
DISPLAY=:0 xrandr --listmonitors
DISPLAY=:0 xinput list
```

Then test touchscreen accuracy at all four corners. User was **given** removal/reboot commands for the old touch script, but has **not yet confirmed** completing them. See [TOUCHSCREEN.md](TOUCHSCREEN.md).

The **only local browser screen** should show the scanner's control/information dashboard at 1280×400. LAN browsers use the same backend.

## Baseline inventory commands

```bash
cat /etc/os-release
hostnamectl
lscpu | head -30
free -h
lsusb
DISPLAY=:0 xrandr --listmonitors
which gqrx rtl_test rtl_fm rtl_power
pactl info
```

Close GQRX and any other receiver client before:

```bash
rtl_test -t
```

Capture actual CPU/RAM, audio device, SDR version/stable sample rates, tuner gains, display origin and touch calibration before writing permanent startup configuration.

## RF limitations

- RTL-SDR nominal 2.4 MS/s gives about 2.4 MHz IQ span; actual usable clean window narrower. Overlap windows and benchmark.
- AIR VHF voice 118.000–136.975 MHz: ~10 overlapping ~2MHz windows is a **planning estimate**, not a measured scan speed; initial known-channel AM scan is easier.
- One NESDR cannot continuously monitor widely separated bands simultaneously. Enabled banks share tuner time.
- A short VHF whip may perform poorly on CB frequencies (~27MHz).
- FIRE/AMB may be digital, trunked and/or encrypted locally; do not assume all channels can be demodulated with AM/NFM.
- RSP1A backend is a **future driver adapter** and not required to start.

## Approved eventual physical improvements

Remote antenna/feedline, rotary encoder/volume knob and communications speaker. These are planned for later and do not need to precede the proof of concept.

## Verified 2026-11-11

After reboot: `DISPLAY=:0 xrandr --listmonitors` showed exactly one monitor: `HDMI-2 1280/597x400/336+0+0`; touch was confirmed accurate. Python 3.12.3 at `/usr/bin/python3`. No `pip3` binary in PATH at check time; use a venv and `python -m pip`.
