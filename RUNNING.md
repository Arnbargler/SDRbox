# SDRbox v1.0 — spectrum, sensitivity and rackio-local NFM audio

**Only one mode:** fixed-window FFT capture, spectral candidates, S3 selected GMRS signal, and **experimental S4 local speaker audio**. No tuner retuning. No traditional scanner profiles, squelch slider, HOLD/SKIP, audio, or activity logs.

Stop any old Uvicorn server with Ctrl+C, and close GQRX or other radio apps. Then on rackio:

```bash
cd ~/SDRbox
git pull
source ~/.venv/bin/activate
python -m pip install -r requirements.txt
python -m compileall -q sdrbox
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open http://rackio.local:8080 in Chrome, hard-refresh (Ctrl+Shift+R), press **START CAPTURE**. The large plot should update ~2–3 times per second. Toggle FULL WINDOW / GMRS 1–7 to change the *displayed* range, without retuning the SDR. Talkie CH1 (462.5625) and CH7 (462.7125) should create distinct peaks. Press STOP CAPTURE and verify restart works.

## What the visualization means

- Tuner center **462.650 MHz**; 2.048 MS/s IQ. FFT plot is an approximately 1.70 MHz center crop.
- Green = uncalibrated relative FFT power; amber = local 25th-percentile estimated noise.
- Dashed markers denote GMRS 1–7 frequency centers.
- Right-hand panel strongest-bin readout is **unqualified**. It can be a spur/noise, not necessarily voice or an actual channel.
- No signals are automatically selected; no audio or real activity hits.

## Python compatibility

Keep rackio's system librtlsdr.so.2. `requirements.txt` pins `pyrtlsdr==0.2.91` and `setuptools<82`; newer wrapper triggered `undefined symbol: rtlsdr_set_dithering` on this machine.

Trusted LAN only. Do not port-forward this unauthenticated service.

## Test S2 candidates

Before starting the server or with the venv active, run `python -m unittest discover -s tests` for offline synthetic-spectrum detector checks. With the live FFT running, the diagnostics column shows **S2 SPECTRAL CANDIDATES**, listing up to two persistent peaks. Amber solid markers on the graph indicate persistent peaks; dim dashed markers indicate provisional detections. Try idle antenna (look for spurious peaks), then PTT on CH1 and CH7 for at least one second each. Compare displayed estimates to 462.5625 and 462.7125 MHz. Notice how quickly each candidate appears after PTT and disappears after release.

These are **experimental candidates**, not voice/GMRS classification. The detector uses a 10 dB peak-to-local-noise threshold and 2-of-3 FFT-frame persistence, excluding a +/-12 kHz center DC region. A constant interference spur can pass that filter; idle false positives are expected to guide refinement. No audio, squelch or automatic selection yet. If the update rate drops below the previously observed ~2–3 frames/s, report it.

## Test S3 signal selection

Run offline tests: `python -m unittest discover -s tests`. In Chrome use Ctrl+Shift+R and START CAPTURE. The formerly raw strongest-bin readout is now **S3 SELECTED SIGNAL**: `SEARCHING` when no stable candidate, `SELECTED` with a cyan marker after two matched S2 frames, and `HANG` with a countdown after matching peak disappears. Transmit on GMRS CH1 (~462.5625 MHz), release PTT, then test CH7 (~462.7125 MHz). Selection should not jump among nearby spur peaks while an existing candidate remains present. Release time is 1.2 seconds measured from last match in *real time*, checked on incoming FFT frames; with 2–3 FPS it may appear to take slightly longer on screen. At two feet, multiple apparent candidates can reflect front-end overload, so also test at a greater distance. The cyan marker does **not** mean demodulation or audio; this is only RF peak selection.

## S4 test: speaker audio and detection sensitivity

The footer includes **MIN RF CONTRAST +15 dB**. This is not the former rtl_fm squelch and does not alter receiver gain: it is the minimum FFT spectral contrast above local noise that can become a candidate. **Increase dB to reject weaker peaks; decrease to receive weaker signals.** Range 8–30 dB. A threshold change resets short-lived candidate and selected-signal history and takes effect during capture. Setting is in-memory for the current server run.

To test: press START CAPTURE, confirm it still draws a live FFT. With the walkie-talkie at a reasonable distance from the antenna (avoid front-end overload), PTT on **GMRS CH1 462.5625 MHz**, then **CH7 462.7125 MHz**. Each should enter SELECTED and show **S4 LOCAL AUDIO: RECEIVING**, with intelligible speech from the **rackio speaker only**. During idle, audio should be muted; after PTT release, HANG is muted and selection releases in approximately 1.2 seconds. Try increasing sensitivity threshold from +15 to +18 if unwanted candidates recur, or reducing to +12 if real transmissions are missed. Do not change the Linux RTL-SDR shared library.

FFT candidates across the 1.7 MHz capture can still be displayed, but **only peaks within +/-9 kHz of GMRS 1–7 center frequencies may be selected for audio**; anything else is ignored by the selector at this stage. `spectrum.audio_frequency_mhz` reports the exact nominal GMRS channel selected for demod (distinct from FFT-estimated selected frequency). `spectrum.audio`/health shows ALSA error if present. Strong nearby PTT signals may overload an NESDR, generating spurious candidates and distorted audio. For debugging, test at several feet or behind a wall; compare to old rtl_fm test if needed.

Run all offline tests first: `python -m unittest discover -s tests`. New synthetic DSP test covers 2.048 MHz IQ downmix/64 kHz FM/24 kHz PCM. **S4 has not yet been validated on rackio hardware**. Any audio glitches, selection problems, or change in the established 2–3 FFT updates/s should be treated as field-test feedback rather than a guaranteed behavior.

## Periodic audio dropout retest
After pulling latest changes, run python -m unittest discover -s tests, then launch Uvicorn and hold CH1 PTT while speaking for ~10 seconds. New logic keeps existing lock during weaker RF evidence and keeps audio gate OPEN during 1.2-second HANG. Watch S3 status and S4 Gate OPEN/CLOSED. If silence occurs while selection remains SELECTED and Gate OPEN, investigate local ALSA/PCM pacing; if status becomes SEARCHING and gate closes, investigate detector. HANG may now produce up to 1.2 seconds of noise after genuine PTT release; this is the intentional tradeoff for debugging brief fades.


## S4 audio continuity test — queued playback, 2026-11-11

User verified S4 locks and demodulates, FFT unchanged, but reported repeated approximately 1 s voice / 1 s silence. After prior selector/HANG fix, UI remains **SELECTED / Gate OPEN during silence**, so further lowering RF threshold is not justified. Reworked local PCM: `sdrbox/playback.py` buffers 24 kHz PCM into a bounded queue and sends it to aplay on a dedicated thread with an explicit ALSA period/buffer. The main SDR thread no longer waits for writes to the speaker. This is an **untested field fix**; not guaranteed until rackio verification.

Pull, run `python -m unittest discover -s tests`, start Uvicorn and Ctrl+Shift+R. Test 10–15 seconds of continuous CH1 PTT and read S4 LOCAL AUDIO diagnostic line: `Gate OPEN · IQ Nms · Q Nms · drop N`. `IQ` is maximum inter-read interval, typical IQ chunk 16 ms at 2.048 MS/s. `Q` is buffered PCM time waiting to be written, `drop` counts blocks discarded if writer queue fills. Hover audio detail for maximal DSP time, ALSA writer gap and slow write count. If pulse persists, report whether gate remains OPEN and the IQ/Q/drop values. Large IQ gaps indicate SDR/CPU scheduling interruptions; queue drops indicate playback cannot keep up; persistent silence with both healthy points to ALSA device/routing. Buffering adds some audio latency compared to v1.0. No browser audio.
