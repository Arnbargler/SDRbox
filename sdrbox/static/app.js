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
    document.querySelectorAll("button[data-bank], #scan, #hold, #skip").forEach(b => b.disabled = !yes); if (yes && latest) render(latest);
    if (!yes) $("message").textContent = "Connection lost · reconnecting…";
  };
  function render(s) {
    latest = s;
    $("status").textContent = s.status;
    $("frequency").textContent = s.frequency_mhz == null ? "---.----" : Number(s.frequency_mhz).toFixed(4);
    $("channel").textContent = s.channel || "NO CHANNEL";
    $("profile").value = s.scan_profile === "FIXED_1" ? "FIXED_1" : s.scan_profile === "SCAN_1_7" ? "SCAN_1_7" : s.scan_profile === "MANAGED_1_7" ? "MANAGED_1_7" : "PERSISTENT_1_7";
    $("squelch").value = s.squelch ?? 15;
    $("squelch-value").textContent = s.squelch ?? 15;
    $("profile").disabled = !connected || s.mode !== "LIVE" || ["SCANNING","RECEIVING","HELD"].includes(s.status);
    $("squelch").disabled = !connected || s.mode !== "LIVE" || s.scan_profile === "PERSISTENT_1_7" || ["SCANNING","RECEIVING","HELD"].includes(s.status);
    $("modulation").textContent = s.modulation || "—";
    $("signal-value").textContent = s.mode === "LIVE" ? (s.activity ? "SQUELCH OPEN" : "SQUELCH CLOSED / UNKNOWN") : s.signal_percent + "% (DEMO)";
    $("signal-bar").style.width = s.mode === "LIVE" ? (s.activity ? "100%" : "0%") : (s.signal_percent ?? 0) + "%";
    $("mode-badge").textContent = s.mode === "LIVE" ? "LIVE GMRS · LOCAL AUDIO" : "SIMULATION · NO RF";
    $("mode-badge").className = s.mode === "LIVE" ? "online" : "demo";
    $("activity-label").textContent = s.mode === "LIVE" ? "DETECTED SQUELCH EVENTS" : "DEMO DATA ONLY";
    $("audio").textContent = "AUDIO: " + s.audio;
    $("message").textContent = s.message;
    $("device").textContent = s.device;
    $("scan").textContent = ["SCANNING", "RECEIVING", "HELD"].includes(s.status) ? "■ STOP" : "▶ SCAN";
    $("skip").disabled = !connected || (s.mode === "LIVE" && (!["MANAGED_1_7", "PERSISTENT_1_7"].includes(s.scan_profile) || !["SCANNING", "RECEIVING", "HELD"].includes(s.status)));
    $("hold").disabled = !connected || (s.mode === "LIVE" && s.scan_profile === "SCAN_1_7") || !["SCANNING", "RECEIVING", "HELD"].includes(s.status);
    $("hold").textContent = s.status === "HELD" ? "▶ RESUME" : "Ⅱ HOLD";
    buttons.forEach(b => {
      const enabled = !!s.bank_enabled[b.dataset.bank];
      b.classList.toggle("active", enabled);
      b.setAttribute("aria-pressed", String(enabled));
      b.disabled = !connected || (s.mode === "LIVE" && b.dataset.bank !== "GMRS");
    });
    const hits = $("hits");
    hits.replaceChildren();
    if (!s.hits.length) {
      const p = document.createElement("p");
      p.className = "empty";
      p.textContent = s.mode === "LIVE" ? "No detected activity yet." : "No simulated activity yet.";
      hits.append(p);
    }
    s.hits.forEach(h => {
      const item = document.createElement("div");
      item.className = "hit";
      const time = document.createElement("time");
      time.textContent = formatTime(h.time);
      const name = document.createElement("span");
      name.textContent = h.channel + (h.simulated ? " · DEMO" : "");
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
  $("scan").addEventListener("click", () => send(["SCANNING", "RECEIVING", "HELD"].includes(latest?.status) ? "scan_stop" : "scan_start"));
  $("hold").addEventListener("click", () => send("scan_hold"));
  $("skip").addEventListener("click", () => send("scan_skip"));
  $("profile").addEventListener("change", () => send("set_scan_profile", {profile: $("profile").value}));
  $("squelch").addEventListener("change", () => send("set_squelch", {squelch: Number($("squelch").value)}));
  $("squelch").addEventListener("input", () => $("squelch-value").textContent = $("squelch").value);
  $("settings").addEventListener("click", () => { $("info-mode").textContent = latest?.mode === "LIVE" ? "Persistent scan retains the USB receiver across channel changes. RF detection and in-process audio are experimental. Python/rtl_fm scan is the working fallback. HOLD/SKIP work in both Python modes." : "Simulated scanning. No radio hardware or sound."; $("info").showModal(); });
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
