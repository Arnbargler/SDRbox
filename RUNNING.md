# SDRbox v0.4 — Python-managed GMRS scanning (experimental)

**User verified:** v0.3 legacy rtl_fm multi-frequency scan works, with squelch 15 currently best for the existing GMRS test setup. **New v0.4 managed scanner awaits testing.**

The new **Managed scan 1–7** setting runs a Python channel scheduler with one single-frequency `rtl_fm` receiver per channel. Audio remains local on rackio, played by a persistent `aplay` process. Python reads the squelched PCM to identify candidate transmissions, updates the real tuned frequency, and logs genuine (but uncalibrated) squelch-open events. HOLD locks the current frequency; SKIP advances the scan. This is an early implementation, not yet optimized for fast revisits.

## Run on rackio

Stop previous Uvicorn with Ctrl+C and close GQRX. Then over SSH:

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open `http://rackio.local:8080` in Chrome, hard-refresh to reload JS, then open INFO. Select **Managed scan 1–7** and squelch **15**, close INFO, press SCAN. The active channel and **actual requested tuned MHz** should advance, not just show a generic range. Transmit on walkie-talkie Channel 1: when detection is successful it should pause, play voice on rackio, show SQUELCH OPEN and add a hit to Recent Activity. Release PTT; scanning resumes after roughly 0.9 seconds of silence. Try HOLD to remain on current channel and SKIP to advance. STOP releases USB receiver and audio subprocess.

## Known constraints

- This first Python scheduler **restarts rtl_fm on each channel**, so channel dwell and scan speed may be sluggish; radio acquisition/settling is not measured yet. Fast short transmissions may be missed. Upgrade later to a persistent SDR device with direct retuning.
- Squelch-open events are inferred from nonzero decoded PCM; a hit represents probable activity and may include false positives or miss silent carrier events. Signal meter remains an activity indicator, not a measured dBm/RSSI value.
- Only seven 462 MHz GMRS/FRS shared channels are currently scanned. No browser audio, no recording.
- **Legacy scan 1–7** is the tested fast fallback. **Fixed GMRS 1** preserves unsquelched fixed-frequency reception.
- The server should run as **one Uvicorn worker** without auto-reload. Browser windows don't own the receiver.
- Keep on trusted home LAN; no authentication or Internet exposure.

If audio, scan cadence, detection or HOLD/SKIP behaves oddly, report the specific symptoms before changing thresholds. This version is deliberately a field-test candidate.

## v0.4 field test and squelch-resume fix (2026-11-11)

User verified Python-owned scanner advances at approximately **one GMRS channel per second**, correctly stops on a Channel 1 walkie-talkie transmission and demodulates voice. **Bug observed:** after PTT release it remained on Channel 1 until SKIP. Fix committed: evaluate the activity hang timer on **every scan-loop iteration**, even when `rtl_fm` stops delivering PCM entirely after squelch closes. Expected resumption after ~1.1 s without meaningful decoded audio. This fix still requires rackio field verification. Squelch 15 remains the starting setting. If continual decoded noise keeps refreshing the timer, additional RF/squelch discrimination will be required.
