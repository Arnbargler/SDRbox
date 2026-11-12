"""SDRbox spectrum-first S1: single live IQ receiver and FFT-only web interface."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .spectrum import SpectrumMonitor

BASE = Path(__file__).resolve().parent
CLIENTS: set[WebSocket] = set()
LOCK = asyncio.Lock()
monitor = None
loop = None
state = {"revision": 0, "status": "STOPPED", "mode": "LIVE_SPECTRUM",
         "window": "GMRS 462", "spectrum": None,
         "message": "Ready for wideband IQ capture",
         "audio": "OFF — S1 diagnostics only"}

def snapshot():
    return dict(state)

async def broadcast():
    packet = {"type": "snapshot", "state": snapshot()}
    stale = []
    for ws in tuple(CLIENTS):
        try:
            await ws.send_json(packet)
        except Exception:
            stale.append(ws)
    for ws in stale:
        CLIENTS.discard(ws)

async def spectrum_event(event, data):
    async with LOCK:
        if state["status"] != "SCANNING":
            return
        if event == "spectrum":
            state.update(spectrum=data, message="Receiving live wideband IQ")
        elif event == "spectrum_error":
            state.update(status="ERROR", spectrum=None, message=f"Receiver error: {data}"[:400])
        else:
            return
        state["revision"] += 1
        await broadcast()

def worker_callback(event, data):
    if loop is not None and not loop.is_closed():
        loop.call_soon_threadsafe(lambda: asyncio.create_task(spectrum_event(event, data)))

@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitor, loop
    loop = asyncio.get_running_loop()
    monitor = SpectrumMonitor(worker_callback)
    try:
        yield
    finally:
        await asyncio.to_thread(monitor.stop)
        loop = None

app = FastAPI(title="SDRbox Spectrum Monitor", version="0.7.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

class Command(BaseModel):
    command: str

@app.get("/")
@app.get("/control")
async def index():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/v1/health")
async def health():
    return {"ok": True, "mode": state["mode"], "status": state["status"],
            "receiver_connected": bool(monitor and monitor.running),
            "local_audio_ready": False}

@app.get("/api/v1/state")
async def get_state():
    return snapshot()

@app.post("/api/v1/commands")
async def command(payload: Command):
    async with LOCK:
        if payload.command == "scan_start":
            if not monitor.running:
                state.update(status="SCANNING", spectrum=None, message="Opening RTL-SDR…")
                state["revision"] += 1
                await broadcast()
                try:
                    await asyncio.to_thread(monitor.start)
                    await asyncio.sleep(0.2)
                    if not monitor.running:
                        raise RuntimeError(monitor.error or "FFT worker exited")
                except Exception as exc:
                    state.update(status="ERROR", message=f"Cannot start SDR: {exc}"[:400])
                    state["revision"] += 1
                    await broadcast()
                    raise HTTPException(503, state["message"]) from exc
        elif payload.command == "scan_stop":
            if monitor.running:
                try:
                    await asyncio.to_thread(monitor.stop)
                except Exception as exc:
                    state.update(status="ERROR", message=f"Cannot stop SDR: {exc}"[:400])
                    state["revision"] += 1
                    await broadcast()
                    raise HTTPException(503, state["message"]) from exc
            state.update(status="STOPPED", spectrum=None, message="Receiver stopped")
        else:
            raise HTTPException(422, "Only START and STOP are supported in spectrum mode")
        state["revision"] += 1
        await broadcast()
        return {"accepted": True, "revision": state["revision"]}

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
