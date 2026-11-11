(() => {
  const $ = id => document.getElementById(id);
  let connected = false;
  let latest = null;
  const buttons = [...document.querySelectorAll("[data-bank]")];
  const formatTime = value => new Date(value).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit", second: "2-digit"});
  const setConnected = yes => {
    connected = yes;
    $("connection").textContent = yes ? "LAN CONNECTED" : "DISCONNECTED";
    $("connection").className = yes ? "online" : "offline";
    document.querySelectorAll("button[data-bank], #scan, #hold, #skip").forEach(b => b.disabled = !yes);
    if (!yes) $("message").textContent = "Connection lost · reconnecting…";
  };
  function render(s) {
    latest = s;
    $("status").textContent = s.status;
    $("frequency").textContent = s.frequency_mhz == null ? "---.----" : Number(s.frequency_mhz).toFixed(4);
    $("channel").textContent = s.channel || "NO CHANNEL";
    $("modulation").textContent = s.modulation || "—";
    $("signal-value").textContent = s.signal_percent + "% (DEMO)";
    $("signal-bar").style.width = s.signal_percent + "%";
    $("message").textContent = s.message;
    $("device").textContent = s.device;
    $("scan").textContent = s.status === "SCANNING" ? "■ STOP" : "▶ SCAN";
    buttons.forEach(b => {
      const enabled = !!s.bank_enabled[b.dataset.bank];
      b.classList.toggle("active", enabled);
      b.setAttribute("aria-pressed", String(enabled));
    });
    const hits = $("hits");
    hits.replaceChildren();
    if (!s.hits.length) {
      const p = document.createElement("p");
      p.className = "empty";
      p.textContent = "No simulated activity yet.";
      hits.append(p);
    }
    s.hits.forEach(h => {
      const item = document.createElement("div");
      item.className = "hit";
      const time = document.createElement("time");
      time.textContent = formatTime(h.time);
      const name = document.createElement("span");
      name.textContent = h.channel + " · DEMO";
      const freq = document.createElement("span");
      freq.textContent = h.frequency_mhz.toFixed(4);
      item.append(time, name, freq);
      hits.append(item);
    });
  }
  async function send(command, extra = {}) {
    if (!connected) return;
    try {
      const response = await fetch("/api/v1/commands", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({command, ...extra})
      });
      if (!response.ok) {
        const error = await response.json();
        $("message").textContent = error.detail || "Command rejected";
      }
    } catch {
      $("message").textContent = "Cannot reach server";
    }
  }
  buttons.forEach(b => b.addEventListener("click", () => {
    if (!latest) return;
    send("set_bank_enabled", {bank: b.dataset.bank, enabled: !latest.bank_enabled[b.dataset.bank]});
  }));
  $("scan").addEventListener("click", () => send(latest?.status === "SCANNING" ? "scan_stop" : "scan_start"));
  $("hold").addEventListener("click", () => send("scan_hold"));
  $("skip").addEventListener("click", () => send("scan_skip"));
  $("settings").addEventListener("click", () => $("info").showModal());
  $("close-info").addEventListener("click", () => $("info").close());
  function connect() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(protocol + "//" + location.host + "/api/v1/events");
    ws.onopen = () => setConnected(true);
    ws.onmessage = event => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "snapshot") render(payload.state);
      } catch (e) { console.error("Bad server event", e); }
    };
    ws.onclose = () => { setConnected(false); setTimeout(connect, 1800); };
    ws.onerror = () => ws.close();
  }
  connect();
})();
