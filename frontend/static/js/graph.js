// Force-directed knowledge tree on a plain canvas.
// Nodes: documents (amber), tags (green), entities (blue).
// Simulation: pair repulsion + edge springs + centering, few hundred nodes max.

const canvas = document.getElementById('graph');
const ctx = canvas.getContext('2d');
const panel = document.getElementById('panel');

const COLORS = {
  document: {fill: '#d97706', text: '#fff', r: 9},
  tag: {fill: '#059669', text: '#fff', r: 6},
  entity: {fill: '#0369a1', text: '#fff', r: 7},
};

// Edge/label colors follow the active theme; node fills read on both.
function theme() { return window.cmpdiColors ? cmpdiColors() : {seam: '#e7e5e4', muted3: '#57534e', coal: '#d97706'}; }

let nodes = [];
let edges = [];
let hovered = null;
let selected = null;
let transform = {x: 0, y: 0, k: 1};

function resize() {
  canvas.width = canvas.clientWidth * devicePixelRatio;
  canvas.height = canvas.clientHeight * devicePixelRatio;
}
window.addEventListener('resize', resize);

async function load() {
  const q = new URLSearchParams(location.search).get('subsidiary') || '';
  const data = await (await fetch('/api/graph?subsidiary=' + encodeURIComponent(q))).json();
  const W = canvas.clientWidth || 800, H = canvas.clientHeight || 560;
  nodes = data.nodes.map((n, i) => ({
    ...n,
    x: W / 2 + Math.cos(i * 2.4) * (60 + i % 7 * 22),
    y: H / 2 + Math.sin(i * 2.4) * (60 + i % 5 * 26),
    vx: 0, vy: 0,
    r: n.type === 'document' ? 10 : n.type === 'entity' ? 7 : 5 + Math.min(6, (n.count || 1)),
  }));
  edges = data.edges
    .map(e => ({source: nodes.find(n => n.id === e.source), target: nodes.find(n => n.id === e.target)}))
    .filter(e => e.source && e.target);
  resize();
  requestAnimationFrame(tick);
}

function tick() {
  // repulsion (capped pair scan; fine at this scale)
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let d2 = dx * dx + dy * dy;
      if (d2 < 1) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 1; }
      if (d2 > 40000) continue;
      const f = 1800 / d2;
      const d = Math.sqrt(d2);
      a.vx += (dx / d) * f; a.vy += (dy / d) * f;
      b.vx -= (dx / d) * f; b.vy -= (dy / d) * f;
    }
  }
  // springs
  for (const e of edges) {
    const dx = e.target.x - e.source.x, dy = e.target.y - e.source.y;
    const d = Math.max(1, Math.hypot(dx, dy));
    const f = (d - 90) * 0.015;
    e.source.vx += (dx / d) * f; e.source.vy += (dy / d) * f;
    e.target.vx -= (dx / d) * f; e.target.vy -= (dy / d) * f;
  }
  // integrate with damping + centering
  const W = canvas.clientWidth, H = canvas.clientHeight;
  for (const n of nodes) {
    n.vx += (W / 2 - n.x) * 0.003;
    n.vy += (H / 2 - n.y) * 0.003;
    if (n === dragged) { n.vx = 0; n.vy = 0; continue; }
    n.vx *= 0.82; n.vy *= 0.82;
    n.x += n.vx; n.y += n.vy;
    n.x = Math.max(24, Math.min(W - 24, n.x));
    n.y = Math.max(24, Math.min(H - 24, n.y));
  }
  draw();
  requestAnimationFrame(tick);
}

function draw() {
  const {width: W, height: H} = canvas;
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.scale(devicePixelRatio, devicePixelRatio);
  const t = theme();
  for (const e of edges) {
    const hot = hovered && (e.source === hovered || e.target === hovered);
    ctx.strokeStyle = hot ? t.coal : t.seam;
    ctx.lineWidth = hot ? 1.6 : 1;
    ctx.beginPath();
    ctx.moveTo(e.source.x, e.source.y);
    ctx.lineTo(e.target.x, e.target.y);
    ctx.stroke();
  }
  ctx.textAlign = 'center';
  for (const n of nodes) {
    const c = COLORS[n.type];
    const hot = n === hovered || n === selected;
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r + (hot ? 2.5 : 0), 0, Math.PI * 2);
    ctx.fillStyle = c.fill;
    ctx.globalAlpha = hovered && !hot && hovered.type === 'document' ? 0.35 : 1;
    ctx.fill();
    ctx.globalAlpha = 1;
    if (n.type !== 'document' || hot) {
      ctx.font = `${hot ? '600 ' : ''}11px "IBM Plex Mono", monospace`;
      ctx.fillStyle = t.muted3;
      ctx.fillText(n.label.length > 26 ? n.label.slice(0, 24) + '…' : n.label,
                   n.x, n.y + n.r + 13);
    }
  }
  ctx.restore();
}

function nodeAt(x, y) {
  return nodes.find(n => Math.hypot(n.x - x, n.y - y) <= n.r + 4) || null;
}

function showPanel(n) {
  if (!n) { panel.classList.add('hidden'); return; }
  panel.classList.remove('hidden');
  if (n.type === 'document') {
    panel.innerHTML = `
      <div class="flex items-start justify-between gap-2">
        <h3 class="text-[13px] font-semibold leading-snug">${n.label}</h3>
        <button id="closepanel" class="text-stone-400 hover:text-ink">✕</button>
      </div>
      <p class="mt-2 font-mono text-[11px] uppercase text-stone-400">${n.group}</p>
      <a href="/doc/${n.ref}" class="mt-4 block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white">Open Document</a>
      <a href="/search?q=${encodeURIComponent(n.label)}" class="mt-2 block rounded-lg border border-seamdark px-3 py-2 text-center text-[13px] font-medium text-stone-600 hover:border-coal hover:text-coal">Search Inside</a>`;
  } else if (n.type === 'tag') {
    panel.innerHTML = `
      <div class="flex items-start justify-between gap-2">
        <h3 class="text-[13px] font-semibold">#${n.label}</h3>
        <button id="closepanel" class="text-stone-400 hover:text-ink">✕</button>
      </div>
      <p class="mt-2 text-[13px] text-stone-500">Extracted tag on ${n.count || '?'} document(s).</p>
      <a href="/search?tag=${encodeURIComponent(n.label)}" class="mt-4 block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white">Search This Tag</a>`;
  } else {
    panel.innerHTML = `
      <div class="flex items-start justify-between gap-2">
        <h3 class="text-[13px] font-semibold">${n.label}</h3>
        <button id="closepanel" class="text-stone-400 hover:text-ink">✕</button>
      </div>
      <p class="mt-2 text-[13px] text-stone-500">Entity resolved from the fact index.</p>
      <a href="/search?q=${encodeURIComponent(n.label)}" class="mt-4 block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white">Search Mentions</a>`;
  }
  panel.querySelector('#closepanel').onclick = () => {
    selected = null; panel.classList.add('hidden');
  };
}

let dragged = null;
canvas.addEventListener('mousedown', (e) => {
  const r = canvas.getBoundingClientRect();
  const n = nodeAt(e.clientX - r.left, e.clientY - r.top);
  if (n) { dragged = n; selected = n; showPanel(n); }
});
window.addEventListener('mouseup', () => { dragged = null; });
canvas.addEventListener('mousemove', (e) => {
  const r = canvas.getBoundingClientRect();
  const n = nodeAt(e.clientX - r.left, e.clientY - r.top);
  if (n !== hovered) { hovered = n; canvas.style.cursor = n ? 'pointer' : 'default'; }
});

load();
