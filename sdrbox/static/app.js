(() => {
  const $ = id => document.getElementById(id);
  let connected = false;
  let latest = null;
  let zoomGmrs = false;
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
    $("profile").value = s.scan_profile === "SPECTRUM_462" ? "SPECTRUM_462" : s.scan_profile === "FIXED_1" ? "FIXED_1" : s.scan_profile === "SCAN_1_7" ? "SCAN_1_7" : s.scan_profile === "MANAGED_1_7" ? "MANAGED_1_7" : "PERSISTENT_1_7";
    const spectrumMode = s.mode === "LIVE" && s.scan_profile === "SPECTRUM_462";
    $("spectrum-panel").hidden = !spectrumMode;
    $("activity-panel").hidden = spectrumMode;
    if (spectrumMode) drawSpectrum(s.spectrum);
    $("squelch").value = s.squelch ?? 15;
    $("squelch-value").textContent = s.squelch ?? 15;
    $("profile").disabled = !connected || s.mode !== "LIVE" || ["SCANNING","RECEIVING","HELD"].includes(s.status);
    $("squelch").disabled = !connected || s.mode !== "LIVE" || ["PERSISTENT_1_7", "SPECTRUM_462"].includes(s.scan_profile) || ["SCANNING","RECEIVING","HELD"].includes(s.status);
    $("modulation").textContent = s.modulation || "—";
    $("signal-value").textContent = spectrumMode ? "FFT ONLY · NO SQUELCH" : s.mode === "LIVE" ? (s.activity ? "SQUELCH OPEN" : "SQUELCH CLOSED / UNKNOWN") : s.signal_percent + "% (DEMO)";
    $("signal-bar").style.width = s.mode === "LIVE" ? (s.activity ? "100%" : "0%") : (s.signal_percent ?? 0) + "%";
    $("mode-badge").textContent = spectrumMode ? "LIVE IQ · NO AUDIO" : s.mode === "LIVE" ? "LIVE GMRS · LOCAL AUDIO" : "SIMULATION · NO RF";
    $("mode-badge").className = s.mode === "LIVE" ? "online" : "demo";
    $("activity-label").textContent = s.mode === "LIVE" ? "DETECTED SQUELCH EVENTS" : "DEMO DATA ONLY";
    $("audio").textContent = "AUDIO: " + s.audio;
    $("message").textContent = s.message;
    $("device").textContent = s.device;
    $("scan").textContent = ["SCANNING", "RECEIVING", "HELD"].includes(s.status) ? "■ STOP" : "▶ SCAN";
    $("skip").disabled = spectrumMode || !connected || (s.mode === "LIVE" && (!["MANAGED_1_7", "PERSISTENT_1_7"].includes(s.scan_profile) || !["SCANNING", "RECEIVING", "HELD"].includes(s.status)));
    $("hold").disabled = spectrumMode || !connected || (s.mode === "LIVE" && s.scan_profile === "SCAN_1_7") || !["SCANNING", "RECEIVING", "HELD"].includes(s.status);
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

  function drawSpectrum(data) {
    const canvas = $("spectrum-plot"), ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height, left = 40, right = w - 10, top = 12, bottom = h - 24;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#101b1a"; ctx.fillRect(0, 0, w, h);
    if (!data || !data.power_db || !data.noise_db) {
      ctx.fillStyle = "#96ad9f"; ctx.font = "14px system-ui";
      ctx.fillText("Waiting for measured IQ samples…", 60, h / 2);
      $("spectrum-age").textContent = "AWAITING DATA";
      return;
    }
    const low = zoomGmrs ? 462.49 : data.low_mhz;
    const high = zoomGmrs ? 462.79 : data.high_mhz;
    $("spectrum-span").textContent = low.toFixed(3) + " – " + high.toFixed(3) + " MHz";
    $("spectrum-age").textContent = "LIVE · " + new Date(data.captured_at * 1000).toLocaleTimeString();
    const indexes = data.power_db.map((_, i) => i).filter(i => {
      const frequency = data.low_mhz + i * (data.high_mhz - data.low_mhz) / (data.power_db.length - 1);
      return frequency >= low && frequency <= high;
    });
    if (!indexes.length) return;
    const floor = indexes.map(i => data.noise_db[i]);
    const power = indexes.map(i => data.power_db[i]);
    const floorMedian = floor.slice().sort((a,b) => a-b)[Math.floor(floor.length / 2)];
    const min = floorMedian - 12;
    const max = Math.max(min + 30, Math.max(...power) + 4);
    const xp = freq => left + (freq - low) / (high - low) * (right - left);
    const yp = val => bottom - Math.max(0, Math.min(1, (val - min) / (max - min))) * (bottom - top);
    ctx.lineWidth = 1;
    ctx.font = "10px system-ui";
    for (let j = 0; j <= 4; j++) {
      const y = top + j * (bottom - top) / 4;
      ctx.strokeStyle = "#355047"; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
      ctx.fillStyle = "#90a69a"; ctx.fillText((max - j * (max-min)/4).toFixed(0), 5, y + 4);
    }
    for (let j = 0; j <= 4; j++) {
      const f = low + j * (high-low)/4, x = xp(f);
      ctx.fillStyle = "#9eafa5"; ctx.fillText(f.toFixed(3), x-20, h-5);
    }
    [462.5625,462.5875,462.6125,462.6375,462.6625,462.6875,462.7125].forEach((freq,i) => {
      if (freq < low || freq > high) return;
      const x = xp(freq);
      ctx.strokeStyle = "#547a69"; ctx.setLineDash([2,3]); ctx.beginPath();
      ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke(); ctx.setLineDash([]);
      if (zoomGmrs) { ctx.fillStyle="#b2ccb8"; ctx.fillText(String(i+1),x-3,top+10); }
    });
    function trace(values, color, width) {
      ctx.strokeStyle=color; ctx.lineWidth=width; ctx.beginPath();
      indexes.forEach((i,j) => {
        const freq = data.low_mhz + i*(data.high_mhz-data.low_mhz)/(data.power_db.length-1);
        if (j===0) ctx.moveTo(xp(freq),yp(values[i])); else ctx.lineTo(xp(freq),yp(values[i]));
      });
      ctx.stroke();
    }
    trace(data.noise_db,"#e4b66c",1.5);
    trace(data.power_db,"#70efa8",1.5);
  }
  $("spectrum-zoom").addEventListener("click", () => {
    zoomGmrs = !zoomGmrs;
    $("spectrum-zoom").textContent = zoomGmrs ? "ZOOM: GMRS" : "ZOOM: FULL";
    drawSpectrum(latest?.spectrum);
  });
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
  $("settings").addEventListener("click", () => { $("info-mode").textContent = latest?.mode === "LIVE" ? "S1 spectrum visualizes live FFT/noise-floor measurements across one 1.7 MHz usable slice, with optional GMRS zoom. No audio or automatic signal selection. Persistent scan retains the USB receiver across channel changes. RF detection and in-process audio are experimental. Python/rtl_fm scan is the working fallback. HOLD/SKIP work in both Python modes." : "Simulated scanning. No radio hardware or sound."; $("info").showModal(); });
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
