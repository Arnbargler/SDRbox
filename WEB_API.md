# SDRbox HTTP/WebSocket API (proposed)

**Updated 2026-11-08. Not implemented.** One local touchscreen and many remote LAN browsers share one scanner backend.

## Serving pages

| Path | Use |
| --- | --- |
| `GET /` | Responsive scanner **control + status** for home LAN browsers |
| `GET /control` | Compact **1280×400** local Chromium scanner page; may be alias/layout of `/` |
| `GET /api/v1/state` | Full authoritative scanner snapshot |
| `GET /api/v1/banks` | Configured bank definitions and enabled state |
| `GET /api/v1/hits?limit=30` | Real confirmed activity |
| `POST /api/v1/commands` | Validated, serialized scan/tune/bank commands |
| `GET /api/v1/health` | Server, receiver and local audio readiness |
| `WS /api/v1/events` | Snapshot on connect, then live state/telemetry/hits/errors |

**Retired:** `/status` as a dedicated upper-1U display. That hardware has been removed. A future optional read-only web view is not prohibited, but is **not required** or part of the kiosk startup.

Suggested address: `http://rackio.local:8080`; hostname exists, but **no web server/port has yet been deployed**.

## Shared state

- **One authoritative scanner state** for all connected clients, not one tuner per connection.
- State includes receiver/device status, scan state (SCANNING/RECEIVING/HELD/ERROR), active bank/frequency/modulation, relative signal strength, enabled banks, audio output status and actual recent hits.
- WebSocket clients receive complete snapshot on connect/reconnect followed by versioned events.
- REST commands such as `scan_start`, `scan_hold`, `scan_resume`, `scan_skip`, `set_bank_enabled`, and `set_local_volume` are validated and queued into the scanner engine.
- ACK means command accepted/rejected; reflect real state only when applied, rather than optimistic fake tuning.
- When local and remote clients issue commands at once, server serializes them. Clients show disconnected/stale state if needed.
- SDR backend and local sound **continue regardless of browsers closing**; a backend/server restart is a different lifecycle concern.

Example command (illustrative):

```json
{"command":"set_bank_enabled","bank":"AIR","enabled":true,"request_id":"example"}
```

No raw IQ or continuous audio in the ordinary status WebSocket.

## Audio phases

- **V1:** decoded AM/NFM voice plays on rackio's local audio device. Volume/mute may be shared controls. Audio output independent of Chromium being open.
- **Later:** separate encoded voice stream/player for remote browsers, including codec, playback permission/autoplay, bandwidth and latency decisions. Do not let browser audio delay initial working scanner.

## Safety / networking

Start on **home LAN only**; no WAN exposure/port forwarding/public reverse proxy. Validate origins/commands; use appropriate cross-site protections for HTTP mutating requests and WebSocket connections. Add authentication/access control before allowing less-trusted network clients. Avoid arbitrary shell/USB commands through the API.

Test with a simulated scanner first, clearly labelled as simulated, then connect real NESDR. Use local 1280×400 browser and a remote PC to confirm shared state, reconnect snapshots and audio continuing when browsers close.
