# Running SDRbox v0.1 (simulator)

The current build is a **browser-controlled simulator**. It does not access the NESDR, produce audio, detect real RF signals or claim real hits. It runs from a normal browser, both on rackio and other home-LAN devices. No kiosk or headless-only operation is needed.

On rackio (Linux Mint, Python 3.12):

```bash
sudo apt update
sudo apt install -y python3-venv
git clone https://github.com/Arnbargler/SDRbox.git  # or git pull in existing checkout
cd SDRbox
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn sdrbox.main:app --host 0.0.0.0 --port 8080
```

Open **http://localhost:8080** from rackio's graphical Chrome/Chromium, or **http://rackio.local:8080** from a home-LAN browser. If mDNS is unavailable use rackio's LAN IP. This command keeps the server running in the terminal until Ctrl+C. It is not installed as a background service.

Test: GMRS should be enabled by default. SCAN moves through demo GMRS channels; HOLD stops advancing; SKIP resumes; other bank switches affect the simulated rotation. Open the page in a second browser: the two copies should stay synchronized. Closing either browser must not stop the backend. Hits are simulated and visibly labelled DEMO.

Test endpoints: /api/v1/health, /api/v1/state, /api/v1/banks, /api/v1/hits and /docs. /api/v1/commands accepts JSON. /api/v1/events is the state WebSocket.

Security: this is a **trusted-home-LAN prototype without authentication**. Do not port-forward it or publish it on the Internet. We must add authentication/CSRF protections before using it on untrusted networks. Future real SDR support will require separate hardware/audio work.
