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


## RTL-SDR detection test — 2026-11-11

From rackio with GQRX not using the dongle, `which rtl_test rtl_fm` returned `/usr/bin/rtl_test` and `/usr/bin/rtl_fm`. Command: `rtl_test -t`.

Observed output:

```text
Found 1 device(s):
  0: Realtek, RTL2838UHIDIR, SN: 00000001
Using device 0: Generic RTL2832U OEM
Detached kernel driver
Found Rafael Micro R820T tuner
Supported gain values (29): 0.0 0.9 1.4 2.7 3.7 7.7 8.7 12.5 14.4 15.7 16.6 19.7 20.7 22.9 25.4 28.0 29.7 32.8 33.8 36.4 37.2 38.6 40.2 42.1 43.4 43.9 44.5 48.0 49.6
[R82XX] PLL not locked!
Sampling at 2048000 S/s.
No E4000 tuner found, aborting.
Reattached kernel driver
```

**Interpretation:** USB device and R820T tuner were successfully enumerated; 29 gain values from 0–49.6 dB were reported. The selected test sample rate was 2.048 MS/s; this line alone is **not** proof of sustained clean IQ capture. The `-t` option runs an E4000-specific test, so the “No E4000 tuner found” message is expected for an R820T device. A one-off PLL warning is not conclusive; investigate only if repeated when tuning real frequencies. Device released/re-attached the kernel driver on exit. Earlier working GQRX reception is useful independent evidence; live GMRS/NFM reception from SDRbox itself is not yet implemented.


## Live GMRS audio received — 2026-11-11

**User verified** intelligible walkie-talkie speech on GMRS Channel 1 (462.5625 MHz) with rackio's local audio output using:

```bash
rtl_fm -d 0 -f 462562500 -M fm -s 24000 -r 24000 -g 30 -l 0 | \
  aplay -r 24000 -f S16_LE -c 1
```

This established RTL-SDR USB access, NFM reception and local ALSA playback, independently of SDRbox. User observed slight latency; earlier GQRX experiments showed it could be reduced with different sampling settings. In this pipeline audio rate is 24 kHz; latency also depends on command buffers and demodulation settings. **Do not confuse this standalone test with an implemented SDRbox live backend.**
