# Running SDRbox v0.2 — GMRS Channel 1 live receiver

**Status:** Live receiver integration committed, awaiting user's first test on rackio. It is not an automatic scanner yet. In live mode, SCAN starts the previously validated `rtl_fm` → `aplay` pipeline at **462.5625 MHz** and audio plays **on rackio**, not in remote Chrome. Stop releases both subprocesses. HOLD retains the frequency and continues playback (there is no channel-hopping to pause yet). SKIP and other live banks are intentionally disabled. No trustworthy signal strength or hit history is available yet. WebSocket synchronizes browser control/status across the LAN.

## Update/install on rackio (SSH is fine)

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m pip install -r requirements.txt
which rtl_fm aplay
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Important: stop the previous server (Ctrl+C) and close GQRX and standalone `rtl_fm` tests **before** launching. Use a single Uvicorn process; don't enable `--reload` or multiple workers while controlling the sole SDR. The known-good external command is:

```bash
rtl_fm -d 0 -f 462562500 -M fm -s 24000 -r 24000 -g 30 -l 0 | aplay -r 24000 -f S16_LE -c 1
```

Open **http://localhost:8080** in the rack's full Chrome browser or **http://rackio.local:8080** on other home-LAN devices. The actual local audio plays on rackio even if the browser is remote. Click SCAN and test the walkie-talkie on GMRS/FRS channel 1. With squelch disabled, expect noise between transmissions. Click STOP, verify audio ends, then start it again. With two browsers open, both should reflect the same radio state. Exit with Ctrl+C; the server should stop its subprocesses.

If a receiver is busy, audio device is unavailable or processes exit, the API/UI should report an error. For debugging inspect `/api/v1/health` and the state API. If the old server is already running on port 8080, stop it first.

## Simulated fallback

```bash
SDRBOX_RECEIVER=sim python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

This does **not** open the NESDR or play sound. GMRS demo channels advance and hits are labelled as simulated.

## Boundaries

Trusted home LAN only; no authentication is implemented. Do not expose/port-forward this service to the public Internet. No remote-browser audio, digital demodulation, automatic channel scanning, real signal detection, recorded hits, calibrated strength meter, service autostart or kiosk requirement. Only one receiver and one Uvicorn worker. Keep real-world RX tests on permitted frequencies and comply with local radio rules.
