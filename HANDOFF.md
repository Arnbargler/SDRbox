# SDRbox — handoff (2026-11-11)

**Direction: spectrum-first SDR monitor only.** User explicitly asked to remove all old sequential scanning modes and associated code and redesign the interface around real FFT data. S3 selection is **field verified** on rackio (SEARCHING/SELECTED/HANG/resume). v1.0 S4 audio and sensitivity are committed and **not yet tested on the real rack**. S2 was field-tested: no idle false positives observed in that session, multiple peaks with nearby walkie-talkie, correct frequency strongest. The user already approved the v0.7 redesigned spectrum-first interface.

## Proven hardware & latest test

- rackio.local = Dell OptiPlex 5060 Micro, 8 GB, Linux Mint, NESDR Smart (RTL2832U/R820T), single HDMI-2 1280×400 touchscreen.
- Browser at http://rackio.local:8080. One FastAPI process/one receiver worker.
- Python 3.12, venv ~/.venv; `pyrtlsdr==0.2.91` and `setuptools<82` needed with distro librtlsdr.so.2.
- Previous v0.6 spectrum FFT **was user verified**: actual Channel 1 walkie-talkie RF spike, 2–3 automatic updates/s after removing an obsolete watchdog check.
- v0.7 preserved `sdrbox/spectrum.py` capture/DSP unchanged but rebuilt server and frontend. Field testing is needed.

## Active files

- `sdrbox/spectrum.py` — single persistent RtlSdr; center 462.650 MHz; 2.048 MS/s; 32768 complex samples/read; eight 4096-point FFTs averaged; local percentile floor; 512-point plotted central 1.70 MHz; includes candidates in snapshots.
- `sdrbox/detector.py` — spectral blob and temporal persistence logic, testable independently of SDR; `tests/test_detector.py`.
- `sdrbox/selector.py` — S3 stable strongest-qualified-candidate choice, +/-8 kHz frequency matching, hold until 1.2s loss; `tests/test_selector.py`.
- `sdrbox/main.py` — FastAPI, WebSocket FFT snapshots, START/STOP command, health/state endpoints.
- `sdrbox/static/index.html`, `app.js`, `style.css` — one-screen large spectrum canvas, zoom and diagnostics.
- `requirements.txt` — all app/SDR dependencies.

Old `receiver.py`, `scanner.py`, `persistent.py`, `requirements-persistent.txt` removed from current tree. They remain in Git history; do not resurrect them without user direction. No simulation, radio audio or scan banks now.

## Next test

Pull on rackio, activate venv, install requirements, launch Uvicorn. Check Chrome display fits 1280×400, continuous FFT updates, FULL/GMRS zoom, CH1 and CH7 spike location, STOP/restart device cleanup. No automatic candidate detection yet.

## Planned steps

S2 grouping elevated FFT bins into qualified signal candidates above a local noise floor, rejecting artifacts. S3 strongest qualified selection; S4 demodulate selected NFM in same IQ window with rackio local audio; S5 overlapping windows (GMRS 467, AIR AM). Do not infer signal identity from raw maximum bin; no calibrated dBm.

LAN-only, unauthenticated controls; do not expose publicly.

## Current S2 test objective

Run the unit tests and v0.8 spectrum app. Idle spectrum should normally display **zero persistent candidates**, although static spurs may generate false positives. Key GMRS CH1, then CH7; look for amber candidate markers and ~462.5625 / ~462.7125 MHz labels after at least two FFT frames. Detection threshold fixed 10 dB above local percentile baseline; minimum 3 adjacent bins; skips +/-12 kHz center DC and 35 kHz near crop edges. No signal is yet selected, heard or logged as a confirmed hit. Do not confuse a persistent spectral peak with confirmed radio traffic. Preserve 2–3 Hz capture while adding the detector; monitor for slowdown.

## S2 field confirmation / next objective

User observed no idle false positives in current test, and transmitting with talkie ~2 feet from NESDR yielded several candidates; highest-ranked candidate was correct frequency. Extra peaks may result from very strong near-field input. Suggest increase transmitter distance and validate signal ranking again. Next S3 should select/hold strongest qualified candidate and release cleanly before enabling NFM audio. Do not overstate false-positive immunity: observation was one field test.

## S3 test requested 2026-11-11

Run `python -m unittest discover -s tests` and restart Uvicorn. With live IQ capture, transmit CH1: after S2's 2-frame confirmation, one candidate should become SELECTED (cyan marker, frequency near 462.5625), with other spurious candidates amber. Momentary drops should show HANG and a release countdown, then SEARCHING after ~1.2 s without a matching strong candidate. Key CH7 and check re-selection. If a competing stronger peak appears during a current selection, do not preempt; this is intentional to prevent flicker. **No audio**, no retune, no confirmed transmission/GMRS classification. S3 is still experimental and not verified on actual radio hardware yet.

## S4 v1.0 pending hardware test

`sdrbox/audio.py` is the new pure DSP NFM mixer/discriminator for the selected GMRS channel; it demodulates **within the same 2.048 MS/s wide IQ capture**, not a tuner retune. `sdrbox/spectrum.py` starts one `aplay` (24 kHz 16-bit mono), feeds silence while idle, selects nearest GMRS channel for audio only within +/-9 kHz, and mutes on HANG. Audio errors are exposed in `spectrum.audio` and `state.audio`. The user can change `threshold_db` 8–30 in the footer; default 15 dB filters prior 12.9 dB lock and rising number means LESS sensitive. Threshold adjustment is available while running, resets candidate/selection history, and does not retune the USB device. Full-window RF peaks remain visible even outside GMRS, but cannot be selected for NFM playback. Browser audio is not implemented.

Check `python -m unittest discover -s tests` and a rackio test. Test no idle audio, PTT on CH1 and CH7 (prefer transmitter several feet away), correct selected/audio frequency, speech intelligibility, FFT cadence and silence/resume. Try +12,+15,+18 dB sensitivity; if audio clips/stutters, collect actual symptoms before touching DSP. `tests/test_audio.py` contains synthetic NFM recovery test. On-hardware test pending.

## Current S4 troubleshooting
Audio cut out rhythmically during continuous PTT although demod and FFT worked. Hysteresis/audio gate fix committed: lock tracks nominal GMRS channel despite bin movement, weaker provisional peak evidence may maintain but not initiate lock, audio continues through HANG. Await rackio verification. If silence persists while S3 SELECTED and S4 Gate OPEN, suspect PCM/ALSA buffering or IQ delivery rather than selector. Check after pull using 10-second continuous PTT.


## Current diagnostic hypothesis and code

Because speaker audio drops out even while the UI is SELECTED/Gate OPEN, suspect PCM pacing, synchronous aplay pipe writes, USB capture stalls or local ALSA scheduling. Introduced a buffered independent playback worker, finite queue, initial prebuffer, bounded overflow, and explicit ALSA period/buffer. SDR capture loop no longer performs potentially blocking stdin writes. `spectrum.audio_diagnostics` and S4 audio status now expose peak IQ read interval (ms), queue milliseconds and dropped chunks; tooltips also reveal max DSP time, slow writes and writer gaps. Expected IQ block interval is roughly 16ms (32768/2048000). Observe values under a continuous 10–15s PTT test and report; current change has **not** been field verified. Additional unit tests in `tests/test_playback.py` need running on rackio.

## Most recent debugging state

Gate remains OPEN and S3 SELECTED while speaker cuts out. User's diagnostics: IQ max 68.9ms, Q16ms, drop0, unchanged during silent intervals. Root cause not proven; old main SDR loop ran expensive FFT/noise floor during capture/PCM processing. Fix: move FFT+S2+S3 into dedicated `spectrum-fft` thread with one-entry nonblocking queue; keep SDR/PCM path free of FFT workload, retain independent PCM writer. New `spectrum.audio_diagnostics.pcm_supply_ratio` reports cumulative sample time divided by elapsed monotonic time; browser S4 status displays `rate ...x`, Q and drops. Needs hardware test. If samples sustain ~1x during a silent interval but silence persists, investigate ALSA underruns/device route or PCM write pacing. Do not confuse peak IQ gap with average sample supply.

## Current S4 throughput experiment
User supplied new data: 0.74x PCM supply *both idle and transmitting*, repeated speech/silence, selection remains SELECTED/Gate OPEN. This means the sample source is producing significantly below the demanded wall-clock audio rate; changing squelch cannot fix it. New trial: READ_SIZE=131072 (64ms IQ blocks, 4x original) to amortize sync USB reads, adjust PCM buffering for 64ms blocks, and expose avg_iq_read_ms and avg_processing_ms. One 64ms IQ frame should produce exactly 1536 audio PCM samples at 24kHz. Tests in tests/test_audio.py and tests/test_playback.py added. Code committed, needs rackio hardware verification. If supply rate remains <1, compare measured R (USB read) and P (processing) to 64ms; investigate RTL synchronous USB throughput or Python pipeline accordingly. FFT scheduling remains independent, no retuning.

## S4 latest handoff: 0.86x supply from RTL read bottleneck

User verified S3 stable SELECTED and audio Gate OPEN during rhythmic speech/silence. Before new refactor: at 2.048MS/s, IQ blocks of 131072 samples are 64ms; avg synchronous RTL read R=66.6ms; overall supply ~0.86x. This cannot sustain 24kHz speaker output. Latest code commits (not yet field-tested) move RTL reads into a dedicated I/O-only thread; NFM demod into separate bounded sequential IQ consumer; FFT/selection in separate latest-frame thread; ALSA PCM remains separate writer. Reduced SDR sampling to **1.536MS/s** (nominal 85.33ms per 131072-sample block) while keeping 462.650MHz center and GMRS1–7 coverage; visible center crop now 1.3MHz. Audio lowpass and decimation changed to 48k intermediate -> 24k PCM. Diagnostics: `pcm_supply_ratio`, `avg_iq_read_ms`, `avg_processing_ms`, `iq_dropped_blocks`, `iq_audio_queue_ms`. User should test idle and long PTT and provide rate/R/P/lost and audio continuity. If capture rate ~1x and lost stays zero but PCM pulses, investigate ALSA; if lost rises, CPU DSP thread falling behind; if rate still <1x, transport/driver read overhead. Old documentation above may be historical. Do not retune or reintroduce channel hopping.
