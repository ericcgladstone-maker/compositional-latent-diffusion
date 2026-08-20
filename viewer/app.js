"use strict";
// Live viewer client. Renders frames streamed from the Python World; never
// reimplements the model. All control values flow back to the same engine.

const PALETTE = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#a855f7"];
const $ = (id) => document.getElementById(id);

const state = {
  ws: null, built: false, registry: null, phases: [],
  config: {}, controls: {},               // name -> DOM element
  net: null,                              // {edges, positions, bounds, big_things, n}
  hist: [],                              // chart history of metric snapshots
  nAgents: 100,
};

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  state.ws = ws;
  ws.onopen = () => { $("conn").textContent = "● connected"; $("conn").className = "ok"; };
  ws.onclose = () => { $("conn").textContent = "● disconnected"; $("conn").className = "bad";
                       setTimeout(connect, 1500); };
  ws.onmessage = (ev) => handle(JSON.parse(ev.data));
}
function send(msg) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) state.ws.send(JSON.stringify(msg));
}

// ---------------------------------------------------------------------------
// Bootstrap: registry + phases -> controls
// ---------------------------------------------------------------------------
async function boot() {
  state.registry = await (await fetch("/registry")).json();
  state.phases = await (await fetch("/phases")).json();
  buildParamPanel();
  buildPhaseDropdowns();
  connect();
}

function buildParamPanel() {
  const { params, group_order, group_labels } = state.registry;
  const host = $("params");
  $("paramCount").textContent = `${params.length} knobs`;
  const byGroup = {};
  params.forEach((p) => { (byGroup[p.group] ||= []).push(p); state.config[p.name] = p.default; });

  group_order.forEach((g, gi) => {
    if (!byGroup[g]) return;
    const det = document.createElement("details");
    det.className = "group"; if (gi < 5) det.open = true;
    det.innerHTML = `<summary>${group_labels[g] || g}</summary>`;
    const body = document.createElement("div"); body.className = "body";
    byGroup[g].forEach((p) => body.appendChild(makeControl(p)));
    det.appendChild(body); host.appendChild(det);
  });
}

function makeControl(p) {
  const wrap = document.createElement("label"); wrap.className = "field";
  const head = document.createElement("div"); head.className = "lab";
  const name = document.createElement("span"); name.className = "name"; name.textContent = p.name;
  const val = document.createElement("span"); val.className = "val";
  head.appendChild(name); head.appendChild(val); wrap.appendChild(head);

  let input;
  if (p.kind === "bool") {
    input = document.createElement("input"); input.type = "checkbox"; input.checked = !!p.default;
    val.replaceWith(input); head.appendChild(input);
    input.addEventListener("change", () => onParam(p, input.checked));
  } else if (p.kind === "choice") {
    input = document.createElement("select");
    p.choices.forEach((c) => { const o = document.createElement("option"); o.value = c; o.textContent = c; input.appendChild(o); });
    input.value = p.default; val.textContent = "";
    input.addEventListener("change", () => onParam(p, input.value));
    wrap.appendChild(input);
  } else {
    input = document.createElement("input"); input.type = "range";
    input.min = p.low; input.max = p.high; input.step = p.step || (p.kind === "int" ? 1 : 0.01);
    input.value = p.default; val.textContent = fmt(p.default);
    input.addEventListener("input", () => { val.textContent = fmt(coerce(p, input.value)); onParam(p, coerce(p, input.value)); });
    wrap.appendChild(input);
  }
  const doc = document.createElement("div"); doc.className = "doc"; doc.textContent = p.doc;
  wrap.appendChild(doc);
  state.controls[p.name] = { input, val, p };
  return wrap;
}

function coerce(p, v) { return p.kind === "int" ? parseInt(v, 10) : parseFloat(v); }
function fmt(v) { return (typeof v === "number" && !Number.isInteger(v)) ? v.toFixed(3) : v; }

function onParam(p, value) {
  state.config[p.name] = value;
  if (state.built) send({ type: "set_param", name: p.name, value });
}

function syncControls(cfg) {
  Object.entries(cfg).forEach(([k, v]) => {
    state.config[k] = v;
    const c = state.controls[k]; if (!c) return;
    if (c.p.kind === "bool") c.input.checked = !!v;
    else { c.input.value = v; if (c.val) c.val.textContent = fmt(v); }
  });
}

function buildPhaseDropdowns() {
  const sel = $("phase"), sweepSel = $("sweepPhase");
  state.phases.forEach((ph) => {
    sel.appendChild(new Option(ph.title, ph.id));
    sweepSel.appendChild(new Option(ph.title, ph.id));
  });
  sweepSel.insertBefore(new Option("FULL — V0 → end (all phases)", "__full__"), sweepSel.firstChild);
  sweepSel.value = "__full__";
  const showPhase = () => {
    const ph = state.phases.find((p) => p.id === sel.value);
    $("phaseDesc").textContent = ph ? ph.desc : "";
    $("phasePredict").textContent = ph ? "Predicted: " + ph.predict : "";
  };
  sel.addEventListener("change", showPhase); showPhase();
}

// ---------------------------------------------------------------------------
// Incoming messages
// ---------------------------------------------------------------------------
function handle(m) {
  switch (m.type) {
    case "built":
      state.built = true; state.nAgents = m.n_agents;
      state.net = { edges: m.edges, positions: m.positions, big_things: m.big_things,
                    n: m.n_agents, bounds: bounds(m.positions) };
      syncControls(m.config);
      state.hist = []; pushFrame(m.frame); drawAll(m.frame);
      break;
    case "frame": pushFrame(m); drawAll(m); break;
    case "status": $("tickReadout").textContent = `t=${m.t} · ${m.reason}`;
      if (m.reason === "quiescent" || m.reason === "stopped") setRunBar(1); break;
    case "sweep_progress":
      setSweepBar(m.done / m.total);
      logSweep(`[${m.done}/${m.total}] ${m.message}`); break;
    case "sweep_done":
      setSweepBar(1); logSweep(`✓ done → ${m.outdir}`); break;
    case "error": logSweep(`⚠ ${m.message}`); $("tickReadout").textContent = "⚠ " + m.message; break;
  }
}

function pushFrame(frame) {
  const me = frame.metrics; state.hist.push(me);
  $("tickReadout").textContent = `t=${me.t}`;
  const mt = parseInt($("maxTicks").value, 10) || 1000;
  setRunBar(Math.min(1, me.t / mt));
  drawMetrics(me);
}

// ---------------------------------------------------------------------------
// Drawing: metrics cards
// ---------------------------------------------------------------------------
function drawMetrics(me) {
  const n = state.nAgents || 1;
  const cards = [
    ["tick", me.t],
    ["manifest share", pct(me.manifest_share)],
    ["element saturation", pct(me.element_saturation)],
    ["observability gap", me.observability_gap.toFixed(3)],
  ];
  for (const [lab, pb] of Object.entries(me.per_big)) {
    cards.push([`${lab} manifest`, `${pb.manifest}`]);
    cards.push([`${lab} latent`, `${pb.latent}`]);
    cards.push([`${lab} at-risk`, `${pb.at_risk}`]);
    cards.push([`${lab} variants`, `${Object.keys(pb.variants).length}`]);
  }
  $("metrics").innerHTML = cards.map(([k, v]) =>
    `<div class="metric"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
}
function pct(x) { return (100 * x).toFixed(1) + "%"; }

// ---------------------------------------------------------------------------
// Drawing: network
// ---------------------------------------------------------------------------
function bounds(pos) {
  let xs = pos.map((p) => p[0]), ys = pos.map((p) => p[1]);
  return { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };
}
function drawNetwork(frame) {
  const cv = $("net"), ctx = cv.getContext("2d");
  fitCanvas(cv); const W = cv.width, H = cv.height, pad = 18;
  ctx.clearRect(0, 0, W, H);
  if (!state.net) return;
  const { positions: pos, edges, bounds: b } = state.net;
  const sx = (x) => pad + (W - 2 * pad) * (x - b.x0) / ((b.x1 - b.x0) || 1);
  const sy = (y) => pad + (H - 2 * pad) * (y - b.y0) / ((b.y1 - b.y0) || 1);

  ctx.strokeStyle = "rgba(148,163,184,0.18)"; ctx.lineWidth = 1; ctx.beginPath();
  edges.forEach(([i, j]) => { ctx.moveTo(sx(pos[i][0]), sy(pos[i][1])); ctx.lineTo(sx(pos[j][0]), sy(pos[j][1])); });
  ctx.stroke();

  frame.agents.forEach((a) => {
    const x = sx(pos[a.i][0]), y = sy(pos[a.i][1]);
    let color = "#cbd5e1";
    if (a.status === "manifest") color = PALETTE[(a.bid || 0) % PALETTE.length];
    else if (a.status === "latent") color = "#fb923c";
    else if (a.status === "at_risk") color = "#facc15";
    ctx.beginPath(); ctx.arc(x, y, a.status === "manifest" ? 6 : 5, 0, 2 * Math.PI);
    ctx.fillStyle = color; ctx.fill();
    if (a.is_change_agent) { ctx.lineWidth = 2; ctx.strokeStyle = "#f0abfc"; ctx.stroke(); }
  });
}

// ---------------------------------------------------------------------------
// Drawing: time-series chart
// ---------------------------------------------------------------------------
function drawChart() {
  const cv = $("chart"), ctx = cv.getContext("2d");
  fitCanvas(cv); const W = cv.width, H = cv.height, pad = 28;
  ctx.clearRect(0, 0, W, H);
  const h = state.hist; if (h.length < 2) return;
  const n = state.nAgents || 1;
  const labels = state.net ? state.net.big_things.map((b) => b.label) : [];

  const series = [
    { color: "#38bdf8", get: (m) => m.manifest_share },
    { color: "#a3e635", get: (m) => m.element_saturation },
    { color: "#f472b6", get: (m) => clamp01(m.observability_gap) },
  ];
  const bigColors = ["#fbbf24", "#fb7185", "#34d399", "#c084fc"];
  labels.forEach((lab, i) => series.push({ color: bigColors[i % bigColors.length],
    get: (m) => (m.per_big[lab] ? m.per_big[lab].manifest / n : 0) }));

  // axes
  ctx.strokeStyle = "rgba(148,163,184,0.25)"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, pad); ctx.lineTo(pad, H - pad); ctx.lineTo(W - pad, H - pad); ctx.stroke();
  ctx.fillStyle = "#64748b"; ctx.font = "10px sans-serif";
  ctx.fillText("1.0", 4, pad + 4); ctx.fillText("0.0", 4, H - pad + 4);
  ctx.fillText("t=" + h[h.length - 1].t, W - pad - 30, H - pad + 14);

  const tx = (i) => pad + (W - 2 * pad) * i / (h.length - 1);
  const ty = (v) => (H - pad) - (H - 2 * pad) * clamp01(v);
  series.forEach((s) => {
    ctx.strokeStyle = s.color; ctx.lineWidth = 1.8; ctx.beginPath();
    h.forEach((m, i) => { const X = tx(i), Y = ty(s.get(m)); i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
    ctx.stroke();
  });
}
function clamp01(x) { return Math.max(0, Math.min(1, x)); }

function fitCanvas(cv) {
  const r = cv.getBoundingClientRect();
  if (cv.width !== Math.round(r.width) || cv.height !== Math.round(r.height)) {
    cv.width = Math.round(r.width); cv.height = Math.round(r.height || 420);
  }
}
let _lastFrame = null;
function drawAll(frame) { _lastFrame = frame; drawNetwork(frame); drawChart(); }

// ---------------------------------------------------------------------------
// Progress bars + log
// ---------------------------------------------------------------------------
function setRunBar(f) { $("runBar").style.width = (100 * clamp01(f)) + "%"; }
function setSweepBar(f) { $("sweepBar").style.width = (100 * clamp01(f)) + "%"; }
function logSweep(s) { const el = $("sweepLog"); el.textContent += s + "\n"; el.scrollTop = el.scrollHeight; }

// ---------------------------------------------------------------------------
// Controls wiring
// ---------------------------------------------------------------------------
function wire() {
  $("buildPhase").onclick = () => { setRunBar(0); send({ type: "build_phase", phase: $("phase").value }); };
  $("buildCustom").onclick = () => { setRunBar(0); send({ type: "build", config: state.config }); };
  $("run").onclick = () => send({ type: "run", fps: +$("fps").value, max_ticks: +$("maxTicks").value });
  $("pause").onclick = () => send({ type: "pause" });
  $("step").onclick = () => send({ type: "step" });
  $("reset").onclick = () => { setRunBar(0); send({ type: "reset" }); };
  $("runSweep").onclick = () => {
    const v = $("sweepPhase").value;
    const phases = v === "__full__" ? null : [v];
    setSweepBar(0); logSweep(`▶ sweep ${v} · ${$("reps").value} reps…`);
    send({ type: "sweep", phases, replications: +$("reps").value, with_invariants: $("invariants").checked });
  };
  window.addEventListener("resize", () => { if (_lastFrame) drawAll(_lastFrame); });
}

boot().then(wire);
