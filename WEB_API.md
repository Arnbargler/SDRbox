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

## S3 field added to spectrum snapshots (v0.9)

`spectrum.selection` has `status` (`SEARCHING`, `SELECTED`, `HANG`), `frequency_mhz` (locked approximate FFT peak frequency or null), `last_detected_mhz`, `contrast_db`, `width_khz`, `release_remaining_s`, `audio_active=false`. This is produced by a server-side selector tied to the existing S2 candidate stream; no browser controls or other commands were added. A selected peak is **not** confirmed voice or a change in tuner frequency. The receiver remains centered on 462.650 MHz for the entire capture.

## S4 controls and telemetry (v1.0)

POST `/api/v1/commands`: `{"command":"set_sensitivity","threshold_db":15}` (value 8–30 dB). The authoritative server state includes `threshold_db`. Spectrum snapshots include `audio` (LOCAL NFM ACTIVE/LOCAL AUDIO MUTED or ALSA error), `audio_frequency_mhz` (nominal GMRS center currently demodulated or null), and `selection.audio_active` reporting audio gating. WebSocket `state.audio` reflects the local ALSA status. No browser audio; no new receive-only frequency commands. Candidate thresholds, lock strength and audio frequency have distinct meanings.


## PCM playback diagnostics

`spectrum.audio_diagnostics` contains `queued_ms`, `written_chunks`, `dropped_chunks`, `max_writer_gap_ms`, `slow_writes`, `max_iq_interval_ms`, `max_demod_ms`, and `error`. These values are diagnostic maxima/snapshots; they are not precise ALSA underrun counters. The browser's S4 audio detail shows Gate OPEN/CLOSED, peak IQ interval, queued milliseconds and dropped chunks. PCM is now passed to a dedicated bounded writer thread instead of synchronously blocking SDR capture on `aplay` stdin. No API command changes.

## Sample supply diagnostic

`spectrum.audio_diagnostics.pcm_supply_ratio` is `(IQ samples processed / 2048000) / elapsed_monotonic_seconds` since starting SDR capture (startup settling buffer excluded). Around 1.00 means the capture loop processes approximately real-time audio sample count; a sustained lower ratio indicates PCM production cannot match wall clock. Unlike max IQ gap, this is an average throughput metric. FFT analysis and the S2/S3 selector now run on a separate worker using the latest IQ frame from a queue of capacity one. The capture worker does not block on FFT. S4 display shows `rate <ratio>x · Q <ms> · drop <count>`.

## Throughput diagnostics update
The receiver now reads 131072 IQ samples (64ms nominal at 2.048MS/s) per synchronous RTL USB call; NFM PCM is 1536 samples (64ms at 24kHz) per block. `spectrum.audio_diagnostics` includes `iq_block_ms` (64), `avg_iq_read_ms`, `avg_processing_ms`, `max_iq_interval_ms`, `max_demod_ms`, `pcm_supply_ratio`, queued_ms, dropped_chunks and writer timing. The UI shows `rate x · R.. P..ms` (R average read, P average processing), with other metrics in the audio detail tooltip. Experimental diagnostics for periodic audio starvation and still awaiting hardware test.
