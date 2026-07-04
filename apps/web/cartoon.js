/*
 * cartoonomics renderer — consumes the predefined CartoonSpec (format §7.6)
 * and draws an accessible, animated cashflow cartoon. Framework-free on purpose
 * so the exchange format — not any UI library — is the contract.
 */
"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";

// Fixed stage layout keyed by the node ids the backend emits.
const LAYOUT = {
  operating: { x: 155, y: 115, emoji: "⚙️" },
  investing: { x: 155, y: 260, emoji: "🌱" },
  financing: { x: 155, y: 405, emoji: "🏦" },
  cash: { x: 470, y: 260, emoji: "💰" },
  net: { x: 790, y: 260, emoji: "📊" },
};

const DIR_GLYPH = { inflow: "▶ in", outflow: "◀ out", neutral: "•" };

let currentSpec = null;
let motionEnabled = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function el(tag, attrs = {}, text) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text != null) node.textContent = text;
  return node;
}

function pathD(from, to) {
  // Quadratic bezier bowing away from the horizontal centre line.
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2 - 55;
  return { d: `M ${from.x} ${from.y} Q ${mx} ${my} ${to.x} ${to.y}`, cx: mx, cy: my };
}

function bezierPoint(t, p0, c, p1) {
  const mt = 1 - t;
  return {
    x: mt * mt * p0.x + 2 * mt * t * c.x + t * t * p1.x,
    y: mt * mt * p0.y + 2 * mt * t * c.y + t * t * p1.y,
  };
}

function drawNode(scene, id, node) {
  const pos = LAYOUT[id];
  if (!pos) return;
  const g = el("g", { class: "node-bubble", transform: `translate(${pos.x} ${pos.y})` });
  const roleColor = { inflow: "var(--inflow)", outflow: "var(--outflow)", neutral: "var(--neutral)" }[node.role];
  const r = id === "cash" ? 58 : 46;
  g.appendChild(el("circle", { r, fill: "var(--panel)", stroke: roleColor, "stroke-width": 4 }));
  g.appendChild(el("text", { class: "node-emoji", "text-anchor": "middle", dy: 12 }, pos.emoji));
  g.appendChild(el("text", { class: "node-label", "text-anchor": "middle", y: r + 22 }, node.label));
  g.appendChild(el("text", { class: "node-value", "text-anchor": "middle", y: r + 40 }, fmtValue(node.value)));
  scene.appendChild(g);
}

function drawFlow(scene, flow, durationMs) {
  const from = LAYOUT[flow.source];
  const to = LAYOUT[flow.target];
  if (!from || !to) return;
  const { d, cx, cy } = pathD(from, to);

  scene.appendChild(el("path", { d, class: `flow-path flow-${flow.direction}` }));

  // Directional glyph + label near the arc apex (never colour-only, A11Y-3).
  scene.appendChild(
    el("text", { class: "dir-glyph", x: cx, y: cy - 8, "text-anchor": "middle", fill: dirColor(flow.direction) }, DIR_GLYPH[flow.direction])
  );
  if (flow.label) {
    scene.appendChild(el("text", { class: "flow-tag", x: cx, y: cy + 10, "text-anchor": "middle" }, flow.label));
  }

  const coinCount = 3;
  const p0 = { x: from.x, y: from.y };
  const c = { x: cx, y: cy };
  const p1 = { x: to.x, y: to.y };
  for (let i = 0; i < coinCount; i++) {
    const coin = el("text", { class: "coin", "text-anchor": "middle", dy: 6 }, "🪙");
    if (motionEnabled) {
      const move = el("animateMotion", {
        dur: `${Math.max(400, durationMs) / 1000}s`,
        repeatCount: "indefinite",
        rotate: "auto",
        begin: `${(i / coinCount) * (durationMs / 1000)}s`,
        path: d,
      });
      coin.appendChild(move);
    } else {
      const pt = bezierPoint((i + 1) / (coinCount + 1), p0, c, p1);
      coin.setAttribute("x", pt.x);
      coin.setAttribute("y", pt.y);
    }
    scene.appendChild(coin);
  }
}

function dirColor(dir) {
  return { inflow: "var(--inflow)", outflow: "var(--outflow)", neutral: "var(--neutral)" }[dir];
}

function fmtValue(v) {
  const unit = currentSpec ? prettyUnit(currentSpec.unit) : "";
  return `₹${Math.abs(v).toLocaleString("en-IN")} ${unit}`.trim();
}

function prettyUnit(unit) {
  return { INR_CRORE: "cr", INR_LAKH: "lakh" }[unit] || unit || "";
}

function renderScene() {
  const scene = document.getElementById("scene");
  scene.innerHTML = "";
  if (!currentSpec) return;
  const dur = currentSpec.animation ? currentSpec.animation.duration_ms : 1200;
  for (const flow of currentSpec.flows) drawFlow(scene, flow, dur);
  for (const node of currentSpec.nodes) drawNode(scene, node.id, node);
}

function renderSpec(spec) {
  currentSpec = spec;
  document.getElementById("title").textContent = spec.title;
  document.getElementById("subtitle").textContent =
    `${spec.entity_name}${spec.subtitle ? " · " + spec.subtitle : ""}`;

  document.getElementById("stage").setAttribute("aria-label", spec.accessibility.alt_text);

  const narrative = document.getElementById("narrative");
  narrative.innerHTML = "";
  for (const line of spec.narrative) {
    const li = document.createElement("li");
    li.textContent = line;
    narrative.appendChild(li);
  }

  document.getElementById("table-caption").textContent = spec.accessibility.table_caption;
  const body = document.getElementById("numbers-body");
  body.innerHTML = "";
  for (const row of spec.table) {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = row.label;
    const td = document.createElement("td");
    td.className = "amount " + (row.value < 0 ? "amount--neg" : "amount--pos");
    td.textContent = `${row.value < 0 ? "−" : ""}₹${Math.abs(row.value).toLocaleString("en-IN")} ${prettyUnit(row.unit)}`;
    tr.append(th, td);
    body.appendChild(tr);
  }

  const p = spec.provenance;
  document.getElementById("provenance").innerHTML =
    `Source: <strong>${p.source}</strong> · Period: ${p.filing_period} · ` +
    `<a href="${p.source_url}" rel="noopener">original filing</a> · ` +
    `fetched ${p.fetched_at} · hash <code>${p.source_hash.slice(0, 12)}…</code>` +
    `<br/>Illustrative research & education — not investment advice.`;

  renderScene();
}

function wireControls() {
  const motionBtn = document.getElementById("toggle-motion");
  motionBtn.setAttribute("aria-pressed", String(!motionEnabled));
  motionBtn.addEventListener("click", () => {
    motionEnabled = !motionEnabled;
    motionBtn.setAttribute("aria-pressed", String(!motionEnabled));
    renderScene();
  });

  const numbersBtn = document.getElementById("toggle-numbers");
  numbersBtn.addEventListener("click", () => {
    const numbers = document.getElementById("numbers");
    const show = numbers.hasAttribute("hidden");
    numbers.toggleAttribute("hidden", !show);
    numbersBtn.setAttribute("aria-pressed", String(show));
  });

  document.getElementById("replay").addEventListener("click", renderScene);
}

async function boot() {
  wireControls();
  try {
    const res = await fetch("cartoon_spec.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    renderSpec(await res.json());
  } catch (err) {
    document.querySelector(".app__header h1").textContent = "Could not load cartoon";
    const stage = document.getElementById("stage");
    stage.innerHTML =
      `<p class="error">Failed to load <code>cartoon_spec.json</code> (${err.message}).<br/>` +
      `Serve this folder over HTTP, e.g. <code>python3 -m http.server</code> from the <code>apps/web/</code> directory, ` +
      `then open <code>http://localhost:8000</code>.</p>`;
  }
}

document.addEventListener("DOMContentLoaded", boot);
