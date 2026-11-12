# Running SDRbox v0.3 — GMRS channels 1–7

The working v0.2 Channel 1 local-audio pipeline is retained as **Fixed GMRS 1** mode. This v0.3 change adds **scan GMRS 1–7** using native `rtl_fm` multi-`-f` scanning, `-l` squelch, and `-t 5` squelch delay. **Awaiting rackio field validation.**

## Start

From SSH into rackio, close GQRX and stop any previous server with Ctrl+C:

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open `http://rackio.local:8080` in Chrome on your desktop, or `http://localhost:8080` on rackio. Audio plays **only on rackio**.

## Test

1. Open **INFO**, choose **Scan GMRS 1–7**, set squelch (initial value **30**), then close INFO.
2. Press **SCAN**. The backend opens one rtl_fm instance with seven frequencies, and sends its decoded audio to rackio's local aplay process.
3. Transmit briefly on GMRS 1 with your walkie-talkie; it should open squelch and be audible. Release PTT, and check that noise is muted and the receiver returns to hopping.
4. Press **STOP** to release the device. If the receiver misses a strong transmission, reduce squelch (e.g. 15), then press SCAN again. If noise holds it open, increase squelch (e.g. 45). These are **starting experiments**, not calibrated RF levels.
5. To compare against the known-good v0.2 baseline, stop, select **Fixed GMRS 1**, then SCAN. Fixed mode has `-l 0` (no squelch).
6. Verify start/stop multiple times and in a second browser if desired.

Only the **GMRS 1–7 simplex/interstitial 462 MHz frequencies** are included at this stage. More channels follow after empirical testing. In scan mode **no exact active frequency is reported by rtl_fm**, so UI displays channel range and no specific MHz number. No false activity hits or signal meter. HOLD and SKIP are disabled in scan mode; fixed mode HOLD maintains reception. No remote audio.

Use **one** Uvicorn worker; no `--reload`, no kiosk requirement. To revert to simulation: `SDRBOX_RECEIVER=sim python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080`.

This is an unauthenticated trusted-home-LAN prototype. Never port-forward. Squelch and hop speed are dependent on signal strength/noise and actual rtl_fm version; capture field observations before tuning further.
