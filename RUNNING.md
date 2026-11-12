# SDRbox v0.5 — current build and tested fallbacks

**Updated 2026-11-11.** This document describes the **current sequential GMRS scanner implementations**, not the planned future spectrum-first FFT engine.

## Run on rackio

Stop any previous Uvicorn server with Ctrl+C. Ensure GQRX and standalone `rtl_fm` processes are closed.

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m pip install -r requirements-persistent.txt
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open `http://rackio.local:8080` from a home LAN browser or `http://localhost:8080` on rackio. Hard-refresh Chrome after JS/UI updates. Audio plays on **rackio's speakers only**. One server process and **one Uvicorn worker**; no competing GQRX or `--reload` multi-process setup.

## Receiver profiles in INFO

| Profile | Implementation | Verified |
| --- | --- | --- |
| Persistent RTL-SDR (`PERSISTENT_1_7`) | One `pyrtlsdr` open handle; sequential channel tuning, in-process FFT contrast/NFM DSP | **Starts, retunes ~3 channels/s** on rackio; separate audio/detection validation pending |
| Python/rtl_fm (`MANAGED_1_7`) | Python cycles one `rtl_fm` child per frequency, squelch-aware activity and local audio | **Tested**: ~1 ch/s; CH1/3/7 frequency display, demod, auto resume |
| Legacy scan (`SCAN_1_7`) | Native `rtl_fm` internally hops 1–7 | **Tested**: audio/squelch work, active frequency not available |
| Fixed GMRS 1 (`FIXED_1`) | `rtl_fm` fixed 462.5625 MHz, squelch off | **Tested**: local audio |
| Simulator | Launch with `SDRBOX_RECEIVER=sim` | UI demo without real RF/audio |

The legacy `rtl_fm` squelch setting **15** was effective with the current radio/antenna, **not a calibrated sensitivity**. The persistent backend's **5 dB open / 3 dB stay contrast thresholds** are independent; its UI squelch slider does **not** control them. Don't adjust that slider expecting persistent-mode changes.

## Library compatibility — resolved

Initial persistent-mode startup failed with `undefined symbol: rtlsdr_set_dithering` against system `/lib/x86_64-linux-gnu/librtlsdr.so.2`. Optional dependencies were pinned to **`pyrtlsdr==0.2.91`** and **`setuptools<82`**. The user subsequently reported persistent mode **working and retuning ~3 channels/s**. No replacement of Linux's system RTL-SDR library was needed.

## What to observe when field-testing

1. Profile selection, SCAN/STOP, HOLD/RESUME and SKIP; note any device-busy or ALSA errors.
2. Actual CH1/3/7 signal detection and intelligible audio in persistent mode, **if not yet verified**.
3. Correct activity log and automatic resumption after PTT.
4. Compare startup, scan cadence and latency against tested `MANAGED_1_7` mode.

No wideband FFT chunk scanning is implemented. The [ARCHITECTURE.md](ARCHITECTURE.md) and [DEVELOPMENT.md](DEVELOPMENT.md) describe **planned next work**, not features in this build.

## Safety

The API runs on the trusted home LAN without authentication. **Do not port-forward or expose it to the Internet.** SDRbox is receive-only. Stop the server normally with Ctrl+C so child processes and USB handles are released.
