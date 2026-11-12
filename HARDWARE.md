# SDRbox hardware and observed performance

## Present installation (verified 2026-11-11)

| Component | Detail |
| --- | --- |
| Host | `rackio.local`, Dell OptiPlex 5060 Micro, 8 GB |
| OS | Linux Mint; Python 3.12; venv `~/.venv` |
| Screen | One HDMI-2 **1280×400** touchscreen at +0+0; no custom XInput mapping |
| SDR | NooElec NESDR Smart, RTL2832U / R820T |
| Speaker | rackio local ALSA / `aplay` |
| Web | `http://rackio.local:8080` (trusted LAN only) |

Single active monitor; retired 1U upper display and dual-screen mapping are **not** part of the installation. See [TOUCHSCREEN.md](TOUCHSCREEN.md).

## Current verified receiver

- Fixed center 462.650 MHz, **1.536 MS/s**, 131072 complex samples per read (~85.33 ms).
- Local 24 kHz NFM audio from selectable GMRS 1–7 peak, with real FFT and spectrum noise estimate.
- **Two-minute sustained walkie-talkie test:** audio remained continuous, no IQ audio-queue drops; reported `rate=0.973×`, USB mean `R=87.6 ms`, cumulative audio-DSP mean `P≈7 ms` at end.
- Values are observations, not a guarantee of indefinite glitch-free throughput. The capture rate is slightly below real time.

## Prior hardware findings

GQRX received airband at approximately 118.800 MHz; choosing the Realtek input corrected apparent frequency offset. `rtl_fm` demodulated GMRS Channel 1 voice and sequential prototypes worked (~1 or ~3 channel visits per second), but **those backends were deleted from the current application**. An `rtl_test -t` run identified the R820T tuner and gain values; an E4000-specific failure message is expected on an R820T.

The Python wrapper is pinned to **`pyrtlsdr==0.2.91`** and **`setuptools<82`** to work with installed `librtlsdr.so.2`; do not replace the system library without a separate compatibility test.

Optional future SDRplay RSP1A, 467 MHz GMRS coverage, AM airband and CB require new work, not just enabling currently disabled UI tabs.
