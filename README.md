# SDRbox

Receive-only, **spectrum-first** radio appliance on `rackio.local`. One continuously tuned RTL-SDR captures a GMRS window, detects RF peaks, selects a qualifying channel and demodulates NFM audio through rackio's speakers. Browsers control the same receiver over the trusted LAN.

## Current hardware-verified baseline — S4

- Dell OptiPlex 5060 Micro, 8 GB, Linux Mint, NooElec NESDR Smart, one 1280×400 HDMI-2 touchscreen.
- Fixed tuner **462.650 MHz**, capture **1.536 MS/s**; plotted central **1.3 MHz** (462.000–463.300 MHz).
- Real FFT and local noise-floor estimate with adjustable **8–30 dB minimum contrast** (default +15); GMRS channels 1–7 are eligible for selection.
- Persistent candidate confirmation; strongest qualified GMRS channel selected, held through brief fades and released after 1.2 seconds without RF evidence.
- NFM demodulation from the *same IQ stream*, local 24 kHz PCM audio through ALSA. No RF retuning while selecting.
- **Field result, 2026-11-11:** continuous audible speech verified during two minutes of PTT after separating capture, demodulation, FFT and playback workers. IQ sample supply ~0.973×, average USB read 87.6 ms per 85.33 ms block, audio DSP cumulative average reaching ~7 ms, no counted IQ-queue drops. Working under this test, not guaranteed indefinitely.
- One START/STOP control and sensitivity slider in a 1280×400 browser UI; no browser audio, multi-window scanner, activity history or confirmed modulation classification.

Start here: [RUNNING.md](RUNNING.md). Architecture: [ARCHITECTURE.md](ARCHITECTURE.md). Handoff: [HANDOFF.md](HANDOFF.md). Roadmap: [DEVELOPMENT.md](DEVELOPMENT.md). Hardware: [HARDWARE.md](HARDWARE.md).

**Security:** no authentication; expose only on a trusted LAN, never port-forward. Historical sequential scanner code remains only in Git history.
