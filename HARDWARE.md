# SDRbox hardware and field evidence

**Updated 2026-11-11. Verified statements only; future ideas separated.**

## Current installation

| Component | Verified |
| --- | --- |
| Host | `rackio.local`, Dell OptiPlex **5060 Micro**, **8 GB** RAM |
| OS/Python | Linux Mint, Python **3.12.3**, venv at `~/.venv` |
| Display | One **HDMI-2 1280×400 +0+0**, accurate touch after reboot |
| SDR | Older **NooElec NESDR Smart**, RTL2832U / R820T, USB device serial `00000001` |
| Radio tools | `/usr/bin/rtl_test`, `/usr/bin/rtl_fm`; GQRX also works |
| Audio | `rtl_fm | aplay` locally on rackio works |
| Physical status | Upper 1U display removed; single 2U screen retained |

The app is a FastAPI server with ordinary local and LAN-browser control. It is **not** a compulsory kiosk and does **not** stream browser audio. A future SDRplay RSP1A receiver is optional, not needed for FFT exploration on the NESDR.

## Real test evidence

- GQRX received FM and airband around **118.800 MHz**; selecting the Realtek source corrected an apparent frequency offset.
- Standalone Channel 1 **462.5625 MHz** NFM received intelligible walkie-talkie audio on rackio using:

```bash
rtl_fm -d 0 -f 462562500 -M fm -s 24000 -r 24000 -g 30 -l 0 | \
  aplay -r 24000 -f S16_LE -c 1
```

- `rtl_fm` GMRS channels 1–7 scan works; **squelch 15** was a good field setting, not an RF power calibration.
- Python-managed `rtl_fm` scanner ~**1 channel/second**; Channel 1/3/7 frequency display, reception and auto-resume verified.
- Persistent `pyrtlsdr` scanner ~**3 channels/second**, startup/retuning confirmed after compatibility fix. Separate in-process audio and detector field performance still unconfirmed.
- Existing persistent IQ sample rate in code is **1.024 MS/s**: this is **not yet a ~2 MHz window**. It is a starting code setting, not proof of optimal USB passband.

## RTL tuner enumeration

`rtl_test -t` found one `Realtek RTL2838UHIDIR`, `Rafael Micro R820T`, and 29 reported tuner gain values from **0.0 to 49.6 dB**; selected sampling at **2.048 MS/s**. It also printed:

```text
[R82XX] PLL not locked!
No E4000 tuner found, aborting.
```

The E4000 message is expected from the E4000-specific `-t` test on an R820T. A one-off PLL warning does not by itself establish failure; actual reception has worked. The 2.048 MS/s message alone does not establish reliable sustained usable bandwidth.

## Python library compatibility

Newer `pyrtlsdr` initially failed on system `librtlsdr.so.2` with missing `rtlsdr_set_dithering`. The venv now uses **`pyrtlsdr==0.2.91`** and **`setuptools<82`** in `requirements-persistent.txt`; user confirmed persistent receiver starts. **Do not replace system `librtlsdr` unnecessarily**—that could break working GQRX and `rtl_fm`.

## Next hardware/spectrum measurements

Before deciding on 2 MHz chunk dimensions: measure sustained **2.048 vs 2.4 MS/s** (if stable), actual clean passband, DC spur position, tuner settle time, dropped samples, power/noise stability and CPU on the Dell. Allow overlap and guard bands. A single SDR cannot view physically separate 462/467 MHz windows continuously. Short test antenna and future CB (~27 MHz) reception may need other antenna/hardware considerations.

To recheck devices with competing applications closed:

```bash
which rtl_test rtl_fm
rtl_test -t
DISPLAY=:0 xrandr --listmonitors
```

Full legacy display configuration is in [TOUCHSCREEN.md](TOUCHSCREEN.md).
