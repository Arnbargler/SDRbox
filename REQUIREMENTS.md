# SDRbox requirements and acceptance

**Product goal:** Receive-only spectrum-first radio appliance on a single RTL-SDR, with rackio-local audio and LAN-browser controls. No simulated signal events or invented calibrated power measurements.

| Capability | State |
| --- | --- |
| One HDMI-2 1280×400 touchscreen + browser UI | **Verified** |
| Fixed, continuous 462 MHz IQ window and real FFT/noise floor | **Verified** |
| Multi-peak detection and adjustable 8–30 dB contrast | **Implemented; first field tests passed** |
| S3 selection, stronger-candidate lock, 1.2s hang | **Verified** |
| S4 in-window NFM audio through rackio `aplay` | **Verified over a two-minute PTT test** |
| Independent USB, DSP, FFT and PCM playback workers | **Verified to eliminate observed rhythmic audio dropouts** |
| Repeatable start/stop, errors and multi-client LAN state | **Implemented; dedicated robustness tests still useful** |
| Configurable windows (GMRS 467, CB, etc.) | **Future** |
| AM airband receive | **Future** |
| Real activity logging, persisted settings, priorities | **Future** |
| Browser audio, recording, optional kiosk | **Deferred** |

## Constraints

Current capture: 462.650 MHz center at **1.536 MS/s**, plotted **1.3 MHz**. Only GMRS 1–7 (462.5625–462.7125 MHz) can be selected for NFM audio, despite a wider displayed FFT. Signal strength is relative to a local noise baseline, **not dBm**, and cannot by itself prove a transmission is voice. One RTL tuner cannot simultaneously see 462 and 467 MHz windows. Unknown services can be digital, trunked or otherwise incompatible with NFM/AM.

The HTTP/WebSocket controls have **no authentication**. Use on a trusted LAN only; production access/security and durable settings are not yet provided.
