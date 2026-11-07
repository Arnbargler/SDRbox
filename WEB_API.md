# SDRbox HTTP/WebSocket contract (proposed)

**Planning specification, 2026-11-07. Not implemented.** This describes how one scanner engine on rackio serves the local rack displays and remote home browsers. Endpoint paths and payloads are initial design suggestions, not existing network APIs.

## Networking and deployment

- Proposed development URL: **`http://rackio.local:8080`**. Hostname `rackio.local` is known to resolve over the LAN; port `8080` is a proposal, not verified free or running.
- Python **FastAPI / ASGI** serves HTML/CSS/JS and machine-readable endpoints from the **same origin**, avoiding unnecessary cross-origin complexity.
- **Local rack**: `/status` upper HDMI-1 (1424×280, no touch); `/control` lower HDMI-2 (1280×400, touch).
- **LAN remote**: `/` responsive composite control/status view. All browser sessions share the **same** scanner engine, state, bank selection, audio output and event log.
- Browser page closure is **not** equivalent to shutting down the engine; server lifecycle is independent of the browser lifecycle.
- Local **rackio speaker audio** is the only planned audio output in v1; streaming to web browsers is later.

## Proposed routes

| Method/path | Purpose | Notes |
| --- | --- | --- |
| `GET /` | Responsive scanner view for LAN browsers | Controls + status |
| `GET /status` | Dedicated 1U read-only status HTML | No scanner controls |
| `GET /control` | Dedicated 2U touch-control HTML | Native 1280×400 layout |
| `GET /api/v1/state` | Full authoritative status snapshot | Refresh/reconnect |
| `GET /api/v1/banks` | Configured bank definitions and on/off values | E.g. AIR, CB, GMRS, AMB, FIRE |
| `GET /api/v1/hits?limit=30` | Recent confirmed activity | SQLite eventually |
| `POST /api/v1/commands` | One validated scanner command | Serialize in controller |
| `GET /api/v1/health` | Server/receiver/audio readiness | Include degraded/error states |
| `WS /api/v1/events` | Live state changes, telemetry, hits and connection health | Snapshot on connect |

**Possible commands**: `scan_start`, `scan_hold`, `scan_resume`, `scan_skip`, `set_bank_enabled`, `set_local_volume`. Frequency/channel manual tuning and record controls are subsequent additions. Use typed payloads with validation; do not allow arbitrary shell/driver commands or direct USB control from a browser.

### Example command

```json
{
  "command": "set_bank_enabled",
  "bank": "AIR",
  "enabled": true,
  "request_id": "client-generated-id"
}
```

A command acknowledgment is **not** evidence that the SDR finished retuning. Acknowledge acceptance/rejection, then publish a new authoritative scanner state after the controller applies it. In case of race/conflicting clients, server order and state version determine the outcome.

### Example state snapshot (illustrative only)

```json
{
  "version": 1,
  "revision": 42,
  "receiver": { "connected": true, "type": "rtl-sdr" },
  "scan": {
    "state": "SCANNING",
    "bank": "AIR",
    "frequency_hz": 118800000,
    "modulation": "AM",
    "enabled_banks": ["AIR"],
    "signal": { "active": false, "relative_db": null }
  },
  "audio": { "output": "rackio-local", "streaming": false, "muted": false },
  "recent_hits": [],
  "error": null
}
```

Values in this snippet are **mock data**, not a report from the real radio; sample revision numbers and RSSI values are not calibration. Prefer nullable/unknown fields instead of invented measurements.

## Event delivery

- Send a **full snapshot immediately on connection**, then server-originated `state_changed`, `signal`, `hit`, `error` and `health` events.
- Each event should carry a monotonically increasing revision or timestamp. Transient high-rate measurements may be coalesced/throttled; do not overwhelm a small touchscreen or client.
- On reconnect, fetch a full snapshot before applying more events. A client should visibly indicate disconnected/stale state.
- Never send raw IQ or continuous audio samples over the standard state WebSocket.
- Restrict read-only `/status` page to presentation controls only; its backend connection is read-only.
- Multiple browsers are mirrors/controllers of the same receiver; never create one receiver instance per browser.
- Simulated backend/testing mode should be explicitly flagged in events and UI.

## Local-first audio

V1 audio path: `RTL-SDR IQ -> AM/NFM decode -> squelch -> rackio sound output`. Volume/mute control should be mediated by the shared scanner controller (not per-client hardware state). Closing any web tab must not cut off local audio. Server audio device failures should be surfaced as status/errors.

Future browser audio: add a **separate optional stream/endpoint** for encoded demodulated voice and a frontend audio player with browser autoplay/user-gesture handling. The exact codec, format and endpoint are **not decided**. Do not require this capability to complete v1.

## LAN security (requirements before any exposure beyond localhost)

The local rack browser can use localhost while other home devices use `rackio.local`; binding network interfaces, firewall settings and port are deployment-time decisions. **Home LAN only at first**: no port forwarding, public reverse proxy, remote-Internet exposure or unauthenticated cross-network access. Validate command input and WebSocket `Origin`; consider protection for commands against cross-site requests, and add user authentication if the server will be reachable from less-trusted devices/networks.

## Implementation and test checklist

- Start with a fake scanner backend to demonstrate `/status`, `/control`, `/` and synchronized bank toggles without needing the NESDR.
- From a separate LAN machine, change a bank; both rack browsers must reflect the authoritative state immediately.
- Unplug/reconnect LAN or reload a client: scan engine must keep running and client must recover a consistent snapshot.
- Start live RTL-SDR backend only after confirming the existing GQRX process has released the receiver.
- Verify commands never block FastAPI event loop during IQ reads/retuning and that simultaneous controls are serialized.
- Confirm local sound operates when all remote browsers are closed.
