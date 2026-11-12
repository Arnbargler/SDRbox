# SDRbox handoff — verified S4 baseline (2026-11-11)

**Project:** https://github.com/Arnbargler/SDRbox

**Hardware:** `rackio.local`, Dell OptiPlex 5060 Micro (8 GB), Linux Mint, NESDR Smart RTL2832U/R820T. One HDMI-2 1280×400 touchscreen; Chrome on rackio or trusted LAN. Python venv `~/.venv`; `pyrtlsdr==0.2.91` uses system `librtlsdr.so.2` (do not casually upgrade this wrapper). Start with `RUNNING.md`.

## Working code

- One SDR capture centered **462.650 MHz**, **1.536 MS/s**, 131072-sample (~85.33 ms) USB blocks; 1.3 MHz plot spanning **462.000–463.300 MHz**.
- Four dedicated workers: USB reader, demod/PCM producer, FFT candidate/selector, buffered `aplay` PCM writer. Preserve this separation.
- `sdrbox/spectrum.py`: radio lifecycle/worker ownership; `detector.py`: peaks; `selector.py`: stable lock; `audio.py`: NFM; `playback.py`: PCM writer; `main.py`: HTTP/WebSocket; `static/`: UI.
- Candidate sensitivity slider **8–30 dB**, default **15 dB**. Only GMRS 1–7 are eligible for S3 selection/audio; other FFT peaks may still display. S3 HANG is **1.2 seconds**.
- Local 24 kHz mono NFM audio. No browser audio, no frequency hopping, no activity logging, no confirmed voice identification.

## Actual field evidence

S2 detected the strongest GMRS transmitter peak with no idle false positives observed in the initial test. S3 lock/hang/release worked on hardware. S4 originally had periodic one-second audio silences despite stable SELECTED/Gate OPEN; *not* solved by squelch tweaks or extra PCM buffering. Separating USB capture from FFT and NFM DSP and moving to 1.536 MS/s solved the audible pauses. User then transmitted for **two minutes continuously with no audio pauses**, reporting: IQ supply **0.973×**, USB read **87.6 ms** per ~85.33 ms block, audio DSP cumulative P from 3.2 to 7 ms, **lost IQ blocks 0**. P is an **average since capture started** and naturally rises as transmissions replace cheap idle silence. The sub-1× capture ratio deserves observation, but no current audible failure.

## Useful next work

Run `python -m unittest discover -s tests` on rackio after changes; then test start/stop, idle, CH1 and CH7 selection/audio, continuous 2-minute reception and FFT updates. Treat current source/worker design as the working baseline. Next product features could be multi-window scheduling, airband AM, or actual hit logging **only after discussing design priorities**. Do not resurrect old `receiver.py`, `scanner.py` or `persistent.py` from Git history.

No authentication: trusted home LAN only.
