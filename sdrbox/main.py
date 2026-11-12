"""SDRbox v0.4: Python-managed GMRS scanner and legacy receiver."""
import asyncio
import os
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .receiver import LocalGMRSReceiver
from .scanner import ManagedScanner

BASE = Path(__file__).resolve().parent
BANKS = ("CB", "GMRS", "AIR", "AMB", "FIRE")
GMRS_CHANNELS = (
    ("GMRS 01", 462.5625), ("GMRS 02", 462.5875),
    ("GMRS 03", 462.6125), ("GMRS 04", 462.6375),
    ("GMRS 05", 462.6625), ("GMRS 06", 462.6875),
    ("GMRS 07", 462.7125), ("GMRS 08", 467.5625),
)
MODE = "SIMULATED" if os.getenv("SDRBOX_RECEIVER", "real").lower() == "sim" else "LIVE"
receiver = LocalGMRSReceiver()
scanner = None
CLIENTS: set[WebSocket] = set()
LOCK = asyncio.Lock()
HITS = deque(maxlen=40)
state = {
    "revision": 0, "mode": MODE, "status": "STOPPED",
    "scan_profile": "MANAGED_1_7" if MODE == "LIVE" else "SIM", "squelch": 15,
    "bank_enabled": {bank: bank == "GMRS" for bank in BANKS},
    "frequency_mhz": None, "channel": None, "modulation": "NFM",
    "signal_percent": None if MODE == "LIVE" else 0,
    "activity": False,
    "device": "RTL-SDR / R820T · GMRS CH 1" if MODE == "LIVE" else "SIMULATOR · NO SDR CONNECTED",
    "audio": "LOCAL / RACKIO (when active)" if MODE == "LIVE" else "SIMULATION · NO AUDIO",
    "message": "Ready · GMRS 01" if MODE == "LIVE" else "Ready · simulation",
}
worker_task = None


def scanner_callback(event, data):
    # Runs on the scanner worker thread; schedule updates on the FastAPI event loop.
    LOOP.call_soon_threadsafe(lambda: asyncio.create_task(scanner_event(event, data)))


async def scanner_event(event, data):
    async with LOCK:
        if state["scan_profile"] != "MANAGED_1_7" or state["status"] in ("STOPPED", "ERROR"):
            return
        if event == "tuned":
            channel, freq = data
            state.update(channel=channel, frequency_mhz=freq, activity=False,
                         status="HELD" if scanner._hold.is_set() else "SCANNING",
                         message=f"Monitoring {channel}")
        elif event == "activity_start":
            state.update(activity=True, status="RECEIVING",
                         message=f"Signal detected on {state['channel']}")
            HITS.appendleft({"time": datetime.now(timezone.utc).isoformat(),
                             "bank": "GMRS", "channel": state["channel"],
                             "frequency_mhz": state["frequency_mhz"], "simulated": False})
        elif event == "activity_end":
            state.update(activity=False, status="HELD" if scanner._hold.is_set() else "SCANNING",
                         message=f"Scanning after {state['channel']}")
        elif event == "held":
            state.update(status="HELD", message="Manual HOLD on current frequency")
        elif event == "resumed":
            state.update(status="SCANNING", message="Scan resumed")
        elif event == "error":
            state.update(status="ERROR", activity=False, audio="LOCAL AUDIO STOPPED", message=f"Scanner error: {data}"[:400])
        state["revision"] += 1
        await broadcast()


def snapshot():
    return {**state, "bank_enabled": dict(state["bank_enabled"]), "hits": list(HITS)[:8]}


async def broadcast():
    event = {"type": "snapshot", "state": snapshot()}
    stale = []
    for ws in tuple(CLIENTS):
        try:
            await ws.send_json(event)
        except Exception:
            stale.append(ws)
    for ws in stale:
        CLIENTS.discard(ws)


async def cycle():
    """Watch real child-process health or advance the simulator."""
    index = tick = 0
    while True:
        await asyncio.sleep(1 if MODE == "LIVE" else 1.5)
        async with LOCK:
            if MODE == "LIVE":
                if state["status"] in ("RECEIVING", "HELD", "SCANNING") and state["scan_profile"] != "MANAGED_1_7" and not receiver.running:
                    reason = receiver.failure()
                    await asyncio.to_thread(receiver.stop)
                    state.update(status="ERROR", message=reason, audio="LOCAL AUDIO STOPPED")
                    state["revision"] += 1
                    await broadcast()
                continue
            if state["status"] != "SCANNING":
                continue
            enabled = [b for b in BANKS if state["bank_enabled"][b]]
            if not enabled:
                state.update(status="STOPPED", message="Enable a bank to scan", signal_percent=0)
            else:
                bank = enabled[index % len(enabled)]
                if bank == "GMRS":
                    channel, freq = GMRS_CHANNELS[index % len(GMRS_CHANNELS)]
                    state.update(channel=channel, frequency_mhz=freq, modulation="NFM")
                else:
                    state.update(channel=f"{bank} · NOT CONFIGURED", frequency_mhz=None, modulation="—")
                state.update(signal_percent=0, message=f"Scanning {bank} · SIMULATED")
                index += 1
                tick += 1
                if tick % 8 == 0 and bank == "GMRS":
                    HITS.appendleft({
                        "time": datetime.now(timezone.utc).isoformat(),
                        "channel": channel, "frequency_mhz": freq,
                        "bank": bank, "simulated": True
                    })
                    state["message"] = "Demo activity logged · NOT A REAL SIGNAL"
                    state["signal_percent"] = 72
            state["revision"] += 1
            await broadcast()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_task, scanner, LOOP
    LOOP = asyncio.get_running_loop()
    scanner = ManagedScanner(scanner_callback)
    worker_task = asyncio.create_task(cycle())
    try:
        yield
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        await asyncio.to_thread(receiver.stop)
        await asyncio.to_thread(scanner.stop)


app = FastAPI(title="SDRbox", version="0.4.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class Command(BaseModel):
    command: str
    bank: str | None = None
    enabled: bool | None = None
    profile: str | None = None
    squelch: int | None = None
    request_id: str | None = Field(default=None, max_length=80)


@app.get("/")
@app.get("/control")
async def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/v1/health")
async def health():
    return {"ok": True, "mode": MODE, "receiver_connected": (receiver.running or scanner.running) if MODE == "LIVE" else False,
            "local_audio_ready": (receiver.running or scanner.running) if MODE == "LIVE" else False,
            "status": state["status"]}


@app.get("/api/v1/state")
async def get_state():
    return snapshot()


@app.get("/api/v1/banks")
async def get_banks():
    return {"banks": [{"id": b, "enabled": state["bank_enabled"][b],
                       "configured": MODE == "SIMULATED" or b == "GMRS"} for b in BANKS]}


@app.get("/api/v1/hits")
async def get_hits(limit: int = 30):
    if not 1 <= limit <= 40:
        raise HTTPException(422, "limit must be 1–40")
    return {"hits": list(HITS)[:limit], "simulated": MODE == "SIMULATED"}


@app.post("/api/v1/commands")
async def command(payload: Command):
    async with LOCK:
        name = payload.command
        if name in ("scan_start", "scan_resume"):
            if not any(state["bank_enabled"].values()):
                raise HTTPException(409, "Enable at least one bank")
            if MODE == "LIVE":
                if not state["bank_enabled"]["GMRS"]:
                    raise HTTPException(409, "Only GMRS is configured for live reception")
                managed = state["scan_profile"] == "MANAGED_1_7"
                if not (scanner.running if managed else receiver.running):
                    try:
                        if managed:
                            await asyncio.to_thread(scanner.start, state["squelch"])
                        else:
                            await asyncio.to_thread(receiver.start,
                                state["scan_profile"] == "SCAN_1_7", state["squelch"])
                        await asyncio.sleep(0.35)
                        if not (scanner.running if managed else receiver.running):
                            raise RuntimeError(scanner.error if managed else receiver.failure())
                    except Exception as exc:
                        await asyncio.to_thread(receiver.stop)
                        await asyncio.to_thread(scanner.stop)
                        state.update(status="ERROR", audio="LOCAL AUDIO STOPPED",
                                     message=f"Could not start receiver: {exc}"[:450])
                        state["revision"] += 1
                        await broadcast()
                        raise HTTPException(503, state["message"]) from exc
                if managed and state["status"] == "HELD":
                    scanner.resume()
                scanning = state["scan_profile"] != "FIXED_1"
                managed = state["scan_profile"] == "MANAGED_1_7"
                state.update(status="SCANNING" if scanning else "RECEIVING",
                             channel="TUNING" if managed else ("GMRS 01–07 · SCANNING" if scanning else "GMRS 01 · FIXED"),
                             frequency_mhz=None if scanning else 462.5625,
                             activity=False,
                             modulation="NFM", signal_percent=None,
                             message=(("Python channel scan · squelch " if managed else "Legacy rtl_fm scan · squelch ") + str(state["squelch"])
                                      if scanning else "Listening on GMRS 01 · squelch off"),
                             audio="LOCAL AUDIO ACTIVE")
            else:
                state.update(status="SCANNING", message="Simulated scanning started")
        elif name == "scan_hold":
            if state["status"] == "HELD":
                if MODE == "LIVE" and state["scan_profile"] == "MANAGED_1_7":
                    scanner.resume()
                state.update(status="SCANNING" if state["scan_profile"] != "FIXED_1" else "RECEIVING",
                             message="Resumed current receiver")
                state["revision"] += 1
                await broadcast()
                return {"accepted": True, "revision": state["revision"], "request_id": payload.request_id}
            if MODE == "LIVE" and state["scan_profile"] == "SCAN_1_7":
                raise HTTPException(409, "Active frequency not exposed by legacy rtl_fm scan; HOLD unavailable")
            if state["status"] not in ("SCANNING", "RECEIVING"):
                raise HTTPException(409, "Start scanning or receiving first")
            if MODE == "LIVE" and state["scan_profile"] == "MANAGED_1_7":
                scanner.hold()
            state.update(status="HELD", message=("Holding current channel · local audio continues"
                        if MODE == "LIVE" else "Manual hold · SIMULATED"))
        elif name == "scan_stop":
            if MODE == "LIVE":
                await asyncio.to_thread(receiver.stop)
                await asyncio.to_thread(scanner.stop)
                state["audio"] = "LOCAL AUDIO STOPPED"
                state["activity"] = False
            state.update(status="STOPPED", message="Stopped", signal_percent=None if MODE == "LIVE" else 0)
        elif name == "scan_skip":
            if MODE == "LIVE":
                if state["scan_profile"] != "MANAGED_1_7" or state["status"] not in ("SCANNING", "RECEIVING", "HELD"):
                    raise HTTPException(409, "SKIP available only during managed scanning")
                scanner.skip()
                state["message"] = "Skipping channel"
                state["revision"] += 1
                await broadcast()
                return {"accepted": True, "revision": state["revision"], "request_id": payload.request_id}
            if state["status"] not in ("SCANNING", "HELD"):
                raise HTTPException(409, "Start scanning first")
            state.update(status="SCANNING", message="Skipping · SIMULATED", signal_percent=0)
        elif name == "set_scan_profile":
            if MODE != "LIVE" or payload.profile not in ("MANAGED_1_7", "SCAN_1_7", "FIXED_1"):
                raise HTTPException(422, "Select MANAGED_1_7, SCAN_1_7 or FIXED_1")
            if receiver.running or scanner.running:
                raise HTTPException(409, "Stop the receiver before changing scan profile")
            state["scan_profile"] = payload.profile
            state.update(status="STOPPED", message="Profile selected · press SCAN",
                         channel=None, frequency_mhz=None)
        elif name == "set_squelch":
            if MODE != "LIVE" or payload.squelch is None or not 1 <= payload.squelch <= 100:
                raise HTTPException(422, "Squelch must be 1–100")
            if receiver.running or scanner.running:
                raise HTTPException(409, "Stop receiver before changing squelch")
            state["squelch"] = payload.squelch
            state["message"] = "Squelch set · press SCAN"
        elif name == "set_bank_enabled":
            if payload.bank not in BANKS or payload.enabled is None:
                raise HTTPException(422, "Valid bank and enabled boolean required")
            if MODE == "LIVE" and payload.bank != "GMRS":
                raise HTTPException(409, f"{payload.bank} live receiving is not implemented yet")
            state["bank_enabled"][payload.bank] = payload.enabled
            if not any(state["bank_enabled"].values()) and state["status"] in ("RECEIVING", "HELD", "SCANNING"):
                if MODE == "LIVE":
                    await asyncio.to_thread(receiver.stop)
                    await asyncio.to_thread(scanner.stop)
                    state["audio"] = "LOCAL AUDIO STOPPED"
                state.update(status="STOPPED", message="All banks disabled")
        else:
            raise HTTPException(422, "Unknown command")
        state["revision"] += 1
        await broadcast()
        return {"accepted": True, "revision": state["revision"], "request_id": payload.request_id}


@app.websocket("/api/v1/events")
async def events(ws: WebSocket):
    origin = ws.headers.get("origin")
    host = ws.headers.get("host", "")
    if origin:
        parsed = urlparse(origin)
        if parsed.netloc != host or parsed.scheme not in ("http", "https"):
            await ws.close(code=1008)
            return
    await ws.accept()
    CLIENTS.add(ws)
    try:
        await ws.send_json({"type": "snapshot", "state": snapshot()})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        CLIENTS.discard(ws)
