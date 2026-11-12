# SDRbox HTTP / WebSocket interface

**Current endpoints (implemented v0.6):**

| Endpoint | Meaning |
| --- | --- |
| `GET /` and `GET /control` | Same current responsive scanner page |
| `GET /api/v1/health` | Server mode, receiver and local-audio status |
| `GET /api/v1/state` | Authoritative scanner snapshot |
| `GET /api/v1/banks` | Bank enabled/configured summary |
| `GET /api/v1/hits?limit=30` | In-memory recent hits (not persistent storage) |
| `POST /api/v1/commands` | Serialized controls |
| `WS /api/v1/events` | Initial snapshot and subsequent shared-state snapshots |

Current commands: `scan_start`, `scan_resume`, `scan_hold`, `scan_stop`, `scan_skip`, `set_scan_profile`, `set_squelch`, `set_bank_enabled`. Check `sdrbox/main.py` for actual validation and errors rather than assuming unimplemented commands (e.g. volume or window selection) exist.

Current profiles: `PERSISTENT_1_7` (default live), `MANAGED_1_7`, `SCAN_1_7`, `FIXED_1`; simulation via process environment. Current state includes mode, status, commanded frequency, channel, audio label, activity, and latest hits. The known-channel frequency is **commanded tuning**, not a measured carrier frequency. Legacy native scan cannot report its internal currently tuned frequency.

Example existing commands:

```json
{"command":"scan_start"}
```

```json
{"command":"set_scan_profile","profile":"MANAGED_1_7"}
```

## Proposed additions for spectrum-first mode — NOT IMPLEMENTED

- `window_center_mhz`, `window_low_mhz`, `window_high_mhz`, usable bandwidth, configured sample rate and capture timestamp.
- Separate `candidates` (estimated center/width/contrast, confidence/qualification), `selected_signal` (demodulation target), and `hits` (confirmed real events).
- Relative spectral power/noise data with explicit units/definition; possibly a throttled compact FFT trace/event. Keep high-rate IQ/audio **off** ordinary status WebSocket.
- Window scheduling and selector policy controls only after stable S1/S2 tests.

**Do not claim that a candidate FFT peak is a confirmed audio hit.** Event types and timestamps should support stale-state and ordering checks; websocket snapshots remain authoritative. Explicitly differentiate WINDOW_SCAN, CANDIDATE, RECEIVING and manual HOLD in future status.

## Web ownership and security

One authoritative server and SDR worker; local and remote browsers observe the same state. Audio generated on rackio independently of browser lifetime. The present system is an unauthenticated **trusted-LAN prototype**; do not expose the API publicly. Current origin checks cover WebSocket only; stronger HTTP origin/CSRF protection and authentication are needed before wider use. No arbitrary shell execution or remote transmission commands.

## S1 additions in v0.6

Added selectable profile `SPECTRUM_462` through the existing `set_scan_profile` command. Under this profile `scan_start` starts a single fixed-window RTL IQ capture; `scan_stop` releases the device. The shared state snapshot includes `spectrum` when active: `center_mhz`, `low_mhz`, `high_mhz`, `sample_rate_hz`, `fft_size`, `power_db` (512 relative spectral maxima), `noise_db` (512 nearby local baseline points), `units="relative_dB_uncalibrated"`, and Unix `captured_at`. Spectrum null means no current data. No audio or hit events from this profile. This is a prototype snapshot representation; do not send raw IQ or unbounded telemetry through WebSockets.
