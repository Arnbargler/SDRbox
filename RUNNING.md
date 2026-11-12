# SDRbox v0.5 — persistent RTL-SDR experimental receiver

**Status:** v0.4 Python-controlled GMRS 1–7 scan was **field-verified** on rackio: ~1 channel/s, correct displayed frequencies and activity detection, local audio, automatic resumption. v0.5 adds an **experimental persistent SDR receiver**. No on-rack validation of v0.5 yet.

## Install and launch over SSH

Stop the previous Uvicorn server with Ctrl+C, close GQRX and any standalone RTL-SDR tools, then:

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m pip install -r requirements-persistent.txt
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

The new dependencies are `numpy`, `scipy`, `pyrtlsdr`. System `librtlsdr` is needed by pyrtlsdr; rackio already has rtl_test and rtl_fm, so the library is likely installed. To verify: `python -c "from rtlsdr import RtlSdr; print('RTL-SDR Python import OK')"`. The live app imports these only when the persistent profile starts, so failure doesn't prevent using the existing profile.

Open `http://rackio.local:8080` from remote Chrome, refresh with Ctrl+Shift+R. In **INFO**, choose **Persistent RTL-SDR scan**, then press SCAN. Watch GMRS channel/frequency change without restarting rtl_fm. Local ALSA speaker audio should play transmissions from your walkie-talkie. Release PTT and check that it resumes; test STOP, HOLD/RESUME and SKIP.

## Architecture and limitations

- Opens exactly one `RtlSdr` USB handle, configures 1.024 MS/s with 30 dB requested gain, tunes `channel + 100 kHz` to avoid center DC, then digitally shifts the channel back to baseband.
- SDR sampled in 32768-sample (~32 ms) chunks. NumPy/SciPy implement FFT relative channel power contrast, FM phase discrimination, audio filtering and rate conversion to 24 kHz. Local `aplay` remains the **only** audio output; no browser audio.
- 0.38-second initial channel dwell plus tune/read overhead; 1.0-second activity hang. These are experimental defaults, not measured throughput. Absolute RSSI/dBm is **not** reported.
- Detector currently uses fixed 5 dB start / 3 dB stay relative RF contrast thresholds. **The old squelch setting 15 has no equivalent meaning here** and adjusting the UI slider does not change persistent detection. We will calibrate the new threshold from actual observed reception before making it adjustable.
- Real hits require RF contrast detection; false positives and misses are possible. The frequency displayed is the commanded channel, not a measured locked frequency. Scans only GMRS 1–7 for now.
- No automatic kiosk/headless requirement. The server and scanner run while the SSH-launched Uvicorn process runs, independently of browsers. One worker only; never share hardware with GQRX.

## Fallback (important)

In INFO select **Python / rtl_fm scan** (`MANAGED_1_7`) after STOP. This is the existing **field-tested working v0.4 implementation**; it restarts rtl_fm each channel. **Legacy rtl_fm scan** (`SCAN_1_7`) and **Fixed GMRS 1** (`FIXED_1`) are also retained.

If persistent scan fails to start or the audio sounds wrong, stop, select the proven Python/rtl_fm scan and report the server error. Do not change ten different settings at once.

Trusted home LAN only; no authentication yet, never expose publicly.
