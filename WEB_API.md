# SDRbox HTTP / WebSocket API — current S4

| Route | Meaning |
| --- | --- |
| `GET /`, `GET /control` | Same live browser UI |
| `GET /api/v1/health` | App mode/status, receiver state and local-audio-readiness indicator |
| `GET /api/v1/state` | Current shared snapshot |
| `POST /api/v1/commands` | Start, stop or adjust sensitivity |
| `WS /api/v1/events` | Full state on connect and after spectrum/status changes |

## Commands

```json
{"command":"scan_start"}
{"command":"scan_stop"}
{"command":"set_sensitivity","threshold_db":15}
```

Legacy names `scan_start` / `scan_stop` mean start/stop continuous spectrum capture, **not sequential channel scanning**. Threshold accepts 8–30 dB and applies without restarting the SDR.

## Snapshot

Top-level state: `revision`, `status` (STOPPED, SCANNING, ERROR), `mode=LIVE_SPECTRUM`, `window`, `threshold_db`, `audio`, `message`, and `spectrum` (null when stopped).

`spectrum` contains `center_mhz=462.650`, `low_mhz=462.000`, `high_mhz=463.300`, `sample_rate_hz=1536000`, FFT metadata and 512-point `power_db`/`noise_db` arrays (uncalibrated relative dB), and timestamp `captured_at`.

- `candidates`: experimental spectral peaks (`frequency_mhz`, `width_khz`, `contrast_db`, `provisional`, `seen_frames`), not confirmed voice or logged traffic.
- `selection`: `status` SEARCHING/SELECTED/HANG; nominal selected GMRS frequency or null, last detected estimate, relative contrast, width, release countdown, `audio_active` and `audio_hold`.
- `audio`, `audio_gate` and `audio_frequency_mhz`: local NFM status, OPEN/CLOSED and nominal channel being demodulated.
- `candidate_threshold_db`, `candidate_method`: detector diagnostics.
- `audio_diagnostics`: `pcm_supply_ratio` (captured IQ seconds / elapsed seconds), `avg_iq_read_ms` (mean synchronous USB read time), `iq_block_ms` (85.3 ms), `avg_processing_ms` (cumulative average NFM processing time), `iq_dropped_blocks`, `iq_audio_queue_ms`, `queued_ms` (PCM queue), `written_chunks`, `dropped_chunks`, and `error` (PCM writer).

Only the most recent FFT snapshot is sent; no raw IQ or browser audio stream. One RTL device stays tuned to 462.650 MHz throughout capture.

**Security:** LAN-only prototype without authentication; no public port-forwarding. The WebSocket checks browser Origin against Host, but this is not a substitute for authenticated access.
