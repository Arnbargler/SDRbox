# SDRbox architecture — current S4 implementation

## Signal/data flow

```text
One RTL-SDR (fixed at 462.650 MHz, 1.536 MS/s)
  └── sdrbox-usb: exclusive device owner; 131072 complex IQ/read (~85.33 ms)
       ├── bounded, ordered IQ queue (12 blocks)
       │    └── sdrbox-demod: selected GMRS channel -> NFM -> 24kHz mono PCM
       │         └── bounded PCM queue -> rackio-pcm -> local aplay / ALSA
       └── latest-IQ queue (capacity 1, stale FFT frames may be skipped)
            └── spectrum-fft: FFT -> local floor -> peaks -> selection
                 └── FastAPI WebSocket -> shared browser UI
```

Only the USB worker calls `RtlSdr`; audio, FFT and ALSA playback never retune it. Audio IQ queue overflow is counted as lost blocks. FFT display frames may be skipped to avoid stalling capture. The audio worker picks up the latest selected frequency from the FFT worker.

## Actual implementation

| Module | Responsibility |
| --- | --- |
| `sdrbox/spectrum.py` | SDR lifecycle, USB capture, FFT worker, demod worker, candidate/selection wiring and minimal throughput metrics |
| `sdrbox/detector.py` | FFT contrast peak grouping and 2-of-3-frame persistence |
| `sdrbox/selector.py` | Strongest persistent GMRS candidate; lower threshold only to **hold** an existing selection; 1.2s release timer |
| `sdrbox/audio.py` | Digital channel mixing, decimation (1.536 MHz -> 48 kHz), NFM discriminator/filter, mono 24 kHz PCM |
| `sdrbox/playback.py` | Separate bounded PCM writer to local `aplay` |
| `sdrbox/main.py` | FastAPI, capture/sensitivity commands and WebSocket snapshots |
| `sdrbox/static/` | Single-panel local/LAN Chrome UI |

A qualified FFT peak is **not necessarily intelligible speech**; contrast is relative, uncalibrated dB, not dBm. Selection is restricted to GMRS 1–7 nominal centers (within 9 kHz). Other peaks may appear on the plot but are not auto-demodulated. An active lock keeps audio open through short HANG fades; some hiss after releasing PTT is possible.

## Constraints and next steps

The spectrum is cropped to 462.000–463.300 MHz. One tuner cannot simultaneously capture the separate 467 MHz window. Adding other banks will require measured retuning/revisit gaps; airband needs AM demodulation. Browser streaming audio, logging confirmed hits, priority modes and multiple tuners are deferred.

**Preserve the field-tested parallel pipeline:** previous single-threaded synchronous FFT/DSP/PCM approaches caused repeated audio starvation. The code should not be simplified back to those designs. Current source supply averages ~0.973× during the recorded test; monitor under longer runs.
