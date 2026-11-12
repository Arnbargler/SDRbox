# SDRbox API — current spectrum-only server

## Implemented

| Route | Function |
| --- | --- |
| GET /, GET /control | Same real FFT monitor browser UI |
| GET /api/v1/health | Server state, receiver running, no audio ready |
| GET /api/v1/state | Complete current snapshot |
| POST /api/v1/commands | Only `{"command":"scan_start"}` and `{"command":"scan_stop"}` |
| WS /api/v1/events | Full state on connect and subsequent FFT snapshots |

Commands keep legacy names for compatibility with the browser, but semantics are **start/stop a single 462 MHz spectrum capture**. All old scan profiles, bank controls, squelch/hold/skip commands, hit and bank endpoints are gone.

Snapshot fields: `revision`, `status` (STOPPED/SCANNING/ERROR), `mode=LIVE_SPECTRUM`, `window`, `message`, `audio`, and `spectrum` (null or an object with `center_mhz`, `low_mhz`, `high_mhz`, `sample_rate_hz`, `fft_size`, `power_db`, `noise_db`, `units`, `captured_at`). 512 plotted bins, relative uncalibrated dB, no claimed dBm.

Future S2 candidate reporting is NOT implemented. Avoid sending raw IQ over ordinary WebSocket. Current LAN prototype is unauthenticated, and mutating commands lack production HTTP-origin/CSRF protection.

## S2 additional spectrum fields (v0.8)

`spectrum.candidates` contains up to eight experimental candidate objects sorted by FFT contrast: `frequency_mhz` (estimated peak-bin center), `width_khz` (coarse grouped-bin width), `contrast_db` (relative to estimated local percentile floor), `seen_frames` and `provisional` (false after at least two recent detections). Other new fields: `candidate_threshold_db` and `candidate_method`. These are **not confirmed transmissions**, do not trigger local audio, and are not persisted as hits. There is no user-adjustable threshold in this first test iteration.
