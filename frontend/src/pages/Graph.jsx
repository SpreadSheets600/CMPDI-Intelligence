import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Network, ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { usePageData, cmpdiColors } from '../hooks/useData.js';
import { useTheme } from '../hooks/useTheme.jsx';
import { getJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Button, EmptyState } from '../components/ui.jsx';

const COLORS = {
  document: { fill: '#d97706', text: '#fff', r: 9 },
  organization: { fill: '#7c3aed', text: '#fff', r: 8 },
  mine: { fill: '#0369a1', text: '#fff', r: 7 },
  location: { fill: '#0d9488', text: '#fff', r: 7 },
  geology: { fill: '#a16207', text: '#fff', r: 6 },
  metric: { fill: '#db2777', text: '#fff', r: 6 },
  event: { fill: '#dc2626', text: '#fff', r: 7 },
  tag: { fill: '#059669', text: '#fff', r: 6 },
  entity: { fill: '#0369a1', text: '#fff', r: 7 },
};

const KIND_FILTERS = [
  ['', 'All kinds'],
  ['organization', 'Organizations'],
  ['mine', 'Mines'],
  ['location', 'Locations'],
  ['geology', 'Geology'],
  ['metric', 'Metrics'],
  ['event', 'Events'],
];

// Interactive canvas: force layout settles synchronously on load (no idle
// animation loop), then renders only on interaction (dirty-flag). Wheel zooms
// to cursor, background drag pans, node drag moves, pinch works on touch.
const MIN_ZOOM = 0.25, MAX_ZOOM = 3;

function layoutSync(nodes, edges) {
  const budget = nodes.length > 500 ? 150 : 260;
  for (let t = 0; t < budget; t++) {
    const alpha = 1 - t / budget;
    let maxD = 0;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        let dx = a.x - b.x, dy = a.y - b.y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) {
          dx = 0.5 - ((i * 7 + j) % 10) / 10;
          dy = 0.5 - ((i * 13 + j * 3) % 10) / 10;
          d2 = 1;
        }
        if (d2 > 40000) continue;
        const d = Math.sqrt(d2), f = (1800 / d2) * alpha;
        a.vx += (dx / d) * f; a.vy += (dy / d) * f;
        b.vx -= (dx / d) * f; b.vy -= (dy / d) * f;
      }
    }
    for (const e of edges) {
      const dx = e.target.x - e.source.x, dy = e.target.y - e.source.y;
      const d = Math.max(1, Math.hypot(dx, dy));
      const f = (d - 90) * 0.015 * alpha;
      e.source.vx += (dx / d) * f; e.source.vy += (dy / d) * f;
      e.target.vx -= (dx / d) * f; e.target.vy -= (dy / d) * f;
    }
    for (const n of nodes) {
      n.vx *= 0.82; n.vy *= 0.82;
      const sx = n.vx, sy = n.vy;
      n.x += sx; n.y += sy;
      const step = Math.abs(sx) + Math.abs(sy);
      if (step > maxD) maxD = step;
    }
    if (maxD < 0.4 && t > 60) break;
  }
  for (const n of nodes) { n.vx = 0; n.vy = 0; }
}

function KnowledgeCanvas({ subsidiary, kind, query, theme, onPick, onMeta }) {
  const canvasRef = useRef(null);
  const eng = useRef(null);
  const [empty, setEmpty] = useState(false);
  const [zoomPct, setZoomPct] = useState(100);
  if (!eng.current) {
    eng.current = {
      nodes: [], edges: [], cam: { x: 0, y: 0, k: 1 },
      hover: null, sel: null, colors: null, raf: 0, w: 0, h: 0,
    };
  }

  const draw = () => {
    const canvas = canvasRef.current, E = eng.current;
    if (!canvas || !E.nodes) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    if (!E.colors) E.colors = cmpdiColors();
    const t = E.colors;
    const { w: W, h: H } = E;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const { x: cx, y: cy, k } = E.cam;
    const toX = (wx) => (wx - cx) * k + W / 2;
    const toY = (wy) => (wy - cy) * k + H / 2;
    const inView = (wx, wy, m) => {
      const sx = toX(wx), sy = toY(wy);
      return sx > -m && sx < W + m && sy > -m && sy < H + m;
    };
    for (const e of E.edges) {
      if (!inView(e.source.x, e.source.y, 0) && !inView(e.target.x, e.target.y, 0)) continue;
      const hot = E.hover && (e.source === E.hover || e.target === E.hover);
      ctx.strokeStyle = hot ? t.coal : t.seam;
      ctx.lineWidth = hot ? 1.6 : 1;
      ctx.beginPath();
      ctx.moveTo(toX(e.source.x), toY(e.source.y));
      ctx.lineTo(toX(e.target.x), toY(e.target.y));
      ctx.stroke();
    }
    const showLabels = k > 0.55;
    ctx.textAlign = 'center';
    for (const n of E.nodes) {
      if (!inView(n.x, n.y, n.r * k + 20)) continue;
      const c = COLORS[n.type] || COLORS.entity;
      const hot = n === E.hover || n === E.sel;
      if (E.hover && !hot && E.hover.type === 'document') ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.arc(toX(n.x), toY(n.y), Math.max(2, n.r * k + (hot ? 2.5 : 0)), 0, Math.PI * 2);
      ctx.fillStyle = c.fill;
      ctx.fill();
      ctx.globalAlpha = 1;
      if (hot) {
        ctx.beginPath();
        ctx.arc(toX(n.x), toY(n.y), Math.max(4, n.r * k + 5), 0, Math.PI * 2);
        ctx.strokeStyle = t.coal;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
      if (n.type !== 'document' || hot) {
        if (!showLabels && !hot) continue;
        ctx.font = `${hot ? '600 ' : ''}11px "IBM Plex Mono", monospace`;
        ctx.fillStyle = t.muted3;
        const label = n.label.length > 26 ? n.label.slice(0, 24) + '…' : n.label;
        ctx.fillText(label, toX(n.x), toY(n.y) + n.r * k + 13);
      }
    }
  };

  const requestDraw = () => {
    const E = eng.current;
    if (E.raf) return;
    E.raf = requestAnimationFrame(() => { E.raf = 0; draw(); });
  };

  const syncZoomLabel = () => {
    const pct = Math.round(eng.current.cam.k * 100);
    setZoomPct((p) => (p === pct ? p : pct));
  };

  const fit = () => {
    const E = eng.current;
    if (!E.nodes.length || !E.w) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const n of E.nodes) {
      if (n.x < x0) x0 = n.x; if (n.y < y0) y0 = n.y;
      if (n.x > x1) x1 = n.x; if (n.y > y1) y1 = n.y;
    }
    const pad = 80;
    const k = Math.max(MIN_ZOOM, Math.min(1.6,
      Math.min(E.w / Math.max(1, x1 - x0 + pad * 2), E.h / Math.max(1, y1 - y0 + pad * 2))));
    E.cam = { x: (x0 + x1) / 2, y: (y0 + y1) / 2, k };
    syncZoomLabel();
    requestDraw();
  };

  const zoomAt = (px, py, factor) => {
    const E = eng.current;
    const k2 = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, E.cam.k * factor));
    if (k2 === E.cam.k) return;
    const wx = E.cam.x + (px - E.w / 2) / E.cam.k;
    const wy = E.cam.y + (py - E.h / 2) / E.cam.k;
    E.cam = { k: k2, x: wx - (px - E.w / 2) / k2, y: wy - (py - E.h / 2) / k2 };
    syncZoomLabel();
    requestDraw();
  };

  // ---- data + layout (filter change; synchronous settle, one paint)
  useEffect(() => {
    const canvas = canvasRef.current, E = eng.current;
    E.w = canvas.clientWidth || 800;
    E.h = canvas.clientHeight || 560;
    E.hover = null; E.sel = null;
    let dead = false;
    (async () => {
      try {
        const params = new URLSearchParams();
        if (subsidiary) params.set('subsidiary', subsidiary);
        if (kind) params.set('kinds', kind);
        if (query) params.set('q', query);
        const data = await getJSON('/api/graph?' + params.toString());
        if (dead) return;
        setEmpty(!data.nodes || data.nodes.length === 0);
        if (onMeta) onMeta({ legend: data.legend || [], counts: data.counts || {} });
        E.nodes = (data.nodes || []).map((n, i) => ({
          ...n,
          x: Math.cos(i * 2.4) * (60 + (i % 7) * 22),
          y: Math.sin(i * 2.4) * (60 + (i % 5) * 26),
          vx: 0, vy: 0,
          r: n.type === 'document' ? 10
            : n.type === 'organization' || n.type === 'mine' ? 8
            : n.type === 'entity' || n.type === 'event' || n.type === 'location' ? 7
            : 5 + Math.min(6, n.count || 1),
        }));
        const byId = new Map(E.nodes.map((n) => [n.id, n]));
        const seen = new Set();
        E.edges = (data.edges || [])
          .map((e) => ({ source: byId.get(e.source), target: byId.get(e.target) }))
          .filter((e) => {
            if (!e.source || !e.target) return false;
            const k = `${e.source.id}→${e.target.id}`;
            if (seen.has(k)) return false;
            seen.add(k);
            return true;
          });
        layoutSync(E.nodes, E.edges);
        if (!dead) { fit(); draw(); }
      } catch {
        if (!dead) setEmpty(true);
      }
    })();
    return () => { dead = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subsidiary, kind, query]);

  // ---- theme change repaints with fresh tokens (no refetch)
  useEffect(() => {
    eng.current.colors = null;
    requestDraw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme]);

  // ---- canvas backing store tracks element size
  useEffect(() => {
    const canvas = canvasRef.current, E = eng.current;
    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      E.w = canvas.clientWidth || 800;
      E.h = canvas.clientHeight || 560;
      canvas.width = Math.max(1, E.w * dpr);
      canvas.height = Math.max(1, E.h * dpr);
      requestDraw();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- pointer interaction (attached once; all state lives in the ref)
  useEffect(() => {
    const canvas = canvasRef.current, E = eng.current;
    const pos = (e) => {
      const r = canvas.getBoundingClientRect();
      return [e.clientX - r.left, e.clientY - r.top];
    };
    const toWorld = (px, py) => [
      E.cam.x + (px - E.w / 2) / E.cam.k,
      E.cam.y + (py - E.h / 2) / E.cam.k,
    ];
    const nodeAt = (px, py) => {
      const [wx, wy] = toWorld(px, py);
      const slop = 5 / E.cam.k;
      let best = null, bestD = Infinity;
      for (const n of E.nodes) {
        const d = Math.hypot(n.x - wx, n.y - wy) - n.r;
        if (d <= slop && d < bestD) { best = n; bestD = d; }
      }
      return best;
    };
    const pointers = new Map();
    let panStart = null, dragNode = null, pinchD0 = 0, pinchK0 = 1;

    const down = (e) => {
      canvas.setPointerCapture?.(e.pointerId);
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        pinchD0 = Math.hypot(a[0] - b[0], a[1] - b[1]) || 1;
        pinchK0 = E.cam.k;
        dragNode = null; panStart = null;
        return;
      }
      const [px, py] = pos(e);
      const n = nodeAt(px, py);
      if (n) {
        dragNode = n;
        E.sel = n;
        if (onPick) onPick(n);
      } else {
        panStart = { px, py, cx: E.cam.x, cy: E.cam.y };
        E.sel = null;
        if (onPick) onPick(null);
      }
      requestDraw();
    };
    const move = (e) => {
      if (!pointers.has(e.pointerId)) {
        const [px, py] = pos(e);
        const n = nodeAt(px, py);
        if (n !== E.hover) {
          E.hover = n;
          canvas.style.cursor = n ? 'pointer' : 'default';
          requestDraw();
        }
        return;
      }
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()];
        const d = Math.hypot(a[0] - b[0], a[1] - b[1]) || 1;
        const r = canvas.getBoundingClientRect();
        const mx = (a[0] + b[0]) / 2 - r.left, my = (a[1] + b[1]) / 2 - r.top;
        const k2 = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, pinchK0 * (d / pinchD0)));
        const wx = E.cam.x + (mx - E.w / 2) / E.cam.k;
        const wy = E.cam.y + (my - E.h / 2) / E.cam.k;
        E.cam = { k: k2, x: wx - (mx - E.w / 2) / k2, y: wy - (my - E.h / 2) / k2 };
        syncZoomLabel();
        requestDraw();
        return;
      }
      const [px, py] = pos(e);
      if (dragNode) {
        const [wx, wy] = toWorld(px, py);
        dragNode.x = wx; dragNode.y = wy;
        for (let t = 0; t < 3; t++) {
          for (const ed of E.edges) {
            if (ed.source !== dragNode && ed.target !== dragNode) continue;
            const dx = ed.target.x - ed.source.x, dy = ed.target.y - ed.source.y;
            const d = Math.max(1, Math.hypot(dx, dy));
            const f = (d - 90) * 0.015 * 0.3;
            ed.source.vx += (dx / d) * f; ed.source.vy += (dy / d) * f;
            ed.target.vx -= (dx / d) * f; ed.target.vy -= (dy / d) * f;
          }
          for (const n of E.nodes) {
            if (n === dragNode) { n.vx = 0; n.vy = 0; continue; }
            n.vx *= 0.82; n.vy *= 0.82;
            n.x += n.vx; n.y += n.vy;
          }
        }
        requestDraw();
      } else if (panStart) {
        E.cam.x = panStart.cx - (px - panStart.px) / E.cam.k;
        E.cam.y = panStart.cy - (py - panStart.py) / E.cam.k;
        requestDraw();
      }
    };
    const up = (e) => {
      pointers.delete(e.pointerId);
      if (pointers.size < 2) pinchD0 = 0;
      if (pointers.size === 0) { dragNode = null; panStart = null; }
    };
    const wheel = (e) => {
      e.preventDefault();
      const [px, py] = pos(e);
      zoomAt(px, py, e.deltaY < 0 ? 1.15 : 1 / 1.15);
    };
    const dbl = (e) => {
      const [px, py] = pos(e);
      const n = nodeAt(px, py);
      if (n) {
        E.sel = n;
        if (onPick) onPick(n);
        E.cam.x = n.x; E.cam.y = n.y;
        E.cam.k = Math.min(MAX_ZOOM, E.cam.k * 1.6);
        syncZoomLabel();
      } else {
        zoomAt(px, py, 1.4);
      }
      requestDraw();
    };
    canvas.addEventListener('pointerdown', down);
    canvas.addEventListener('pointermove', move);
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
    canvas.addEventListener('wheel', wheel, { passive: false });
    canvas.addEventListener('dblclick', dbl);
    return () => {
      canvas.removeEventListener('pointerdown', down);
      canvas.removeEventListener('pointermove', move);
      canvas.removeEventListener('pointerup', up);
      canvas.removeEventListener('pointercancel', up);
      canvas.removeEventListener('wheel', wheel);
      canvas.removeEventListener('dblclick', dbl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className='relative'>
      <canvas ref={canvasRef} className='block h-[560px] w-full touch-none' />
      <div className='absolute bottom-3 right-3 flex items-center gap-1 rounded-xl border border-seam bg-surface/95 p-1 shadow-card backdrop-blur'>
        <button
          type='button' title='Zoom out' aria-label='Zoom out'
          onClick={() => zoomAt(eng.current.w / 2, eng.current.h / 2, 1 / 1.25)}
          className='flex h-8 w-8 items-center justify-center rounded-lg text-muted0 transition-colors hover:bg-paper hover:text-coal'
        >
          <ZoomOut className='h-4 w-4' />
        </button>
        <span className='w-12 text-center font-mono text-[11px] text-muted1 tabular-nums'>{zoomPct}%</span>
        <button
          type='button' title='Zoom in' aria-label='Zoom in'
          onClick={() => zoomAt(eng.current.w / 2, eng.current.h / 2, 1.25)}
          className='flex h-8 w-8 items-center justify-center rounded-lg text-muted0 transition-colors hover:bg-paper hover:text-coal'
        >
          <ZoomIn className='h-4 w-4' />
        </button>
        <button
          type='button' title='Fit to view' aria-label='Fit to view'
          onClick={() => fit()}
          className='flex h-8 w-8 items-center justify-center rounded-lg text-muted0 transition-colors hover:bg-paper hover:text-coal'
        >
          <Maximize className='h-4 w-4' />
        </button>
      </div>
      {empty && (
        <div className='pointer-events-none absolute inset-0 flex items-center justify-center p-6'>
          <EmptyState
            icon={Network}
            title='Nothing to draw in this view'
            description='No nodes match the current subsidiary, kind or search — loosen the filters, or ingest files to grow the tree.'
            className='pointer-events-auto max-w-md border-solid bg-surface/95 backdrop-blur'
          />
        </div>
      )}
    </div>
  );
}

function NodePanel({ picked, onClose }) {
  const [hood, setHood] = useState(null);
  useEffect(() => {
    if (!picked || picked.type === 'tag') { setHood(null); return undefined; }
    let alive = true;
    setHood(null);
    getJSON('/api/graph/node?id=' + encodeURIComponent(picked.id))
      .then((data) => { if (alive) setHood(data); })
      .catch(() => { if (alive) setHood(null); });
    return () => { alive = false; };
  }, [picked]);

  return (
    <AnimatePresence>
      {picked && (
        <motion.div
          initial={{ x: 60, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 60, opacity: 0 }}
          transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
          className='absolute inset-y-0 right-0 w-80 overflow-y-auto border-l border-seam bg-surface/95 p-4 backdrop-blur'
        >
          <div className='flex items-start justify-between gap-2'>
            <div>
              <h3 className='text-xs font-semibold leading-snug text-ink'>
                {picked.type === 'tag' ? `#${picked.label}` : picked.label}
              </h3>
              <p className='mt-0.5 font-mono text-[10px] uppercase tracking-wider text-muted1'>{picked.type}</p>
            </div>
            <button onClick={onClose} className='text-muted1 hover:text-ink text-sm'>✕</button>
          </div>
          {picked.type === 'document' && (
            <div className='mt-3 space-y-2'>
              <p className='font-mono text-[11px] uppercase text-muted1'>{picked.group}</p>
              <Button to={`/doc/${picked.ref}`} variant='primary' size='sm' className='w-full'>Open Document</Button>
              <Button to={`/search?q=${encodeURIComponent(picked.label)}`} variant='secondary' size='sm' className='w-full'>Search Inside</Button>
            </div>
          )}
          {picked.type === 'tag' && (
            <div className='mt-3 space-y-2'>
              <p className='text-xs text-muted1'>Extracted tag on {picked.count || '?'} document(s).</p>
              <Button to={`/search?tag=${encodeURIComponent(picked.label)}`} variant='primary' size='sm' className='w-full'>Search This Tag</Button>
            </div>
          )}
          {(picked.type === 'entity' || picked.type === 'organization') && (
            <EntityContext name={picked.ref || picked.label} />
          )}
          {hood && hood.edges && hood.edges.length > 0 && (
            <div className='mt-4'>
              <h4 className='font-mono text-[10px] uppercase tracking-wider text-muted1'>
                Relationships ({hood.edges.length})
              </h4>
              <ul className='mt-2 space-y-2'>
                {hood.edges.slice(0, 12).map((e, i) => {
                  const otherId = e.source === picked.id ? e.target : e.source;
                  const other = (hood.neighbours || []).find((n) => n.id === otherId);
                  const ev = e.evidence || {};
                  return (
                    <li key={i} className='rounded-xl border border-seam bg-paper/50 px-3 py-2'>
                      <p className='font-mono text-[10px] text-coal font-semibold'>{e.relation.replace(/_/g, ' ')}</p>
                      <p className='text-xs font-semibold text-ink'>{other ? other.label : otherId}</p>
                      {ev.filename && (
                        <p className='mt-0.5 font-mono text-[10px] text-muted1'>
                          {ev.filename}{ev.page_no ? ` · p.${ev.page_no}` : ''}
                        </p>
                      )}
                      {ev.snippet && (
                        <p className='mt-1 text-xs leading-snug text-muted0'>
                          {ev.snippet.length > 140 ? ev.snippet.slice(0, 140) + '…' : ev.snippet}
                        </p>
                      )}
                      {ev.doc_id && (
                        <Link
                          to={ev.page_no ? `/doc/${ev.doc_id}?page=${ev.page_no}` : `/doc/${ev.doc_id}`}
                          className='mt-1 inline-block font-mono text-[10.5px] font-semibold text-coal hover:underline'
                        >
                          View Source →
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Public reference context for an entity node: curated profile, geography,
// production and statistics (origin: reference) kept visually separate from
// the entity's footprint in the ingested library (origin: evidence).
// Reference values are context, never receipts.
function EntityContext({ name }) {
  const [state, setState] = useState({ data: null, error: null });
  useEffect(() => {
    let alive = true;
    setState({ data: null, error: null });
    getJSON('/api/reference/entity?name=' + encodeURIComponent(name))
      .then((data) => alive && setState({ data, error: null }))
      .catch((e) => alive && setState({ data: null, error: e.message }));
    return () => { alive = false; };
  }, [name]);

  const { data, error } = state;
  if (error) {
    return (
      <div className='mt-3 space-y-2'>
        <p className='text-xs text-muted0'>Entity resolved from the fact index.</p>
        <p className='font-mono text-[11px] text-muted1'>No public reference for this entity yet.</p>
        <Button to={`/search?q=${encodeURIComponent(name)}`} variant='secondary' size='sm' className='w-full'>Search Mentions</Button>
      </div>
    );
  }
  if (!data) return <p className='mt-2 font-mono text-[11px] text-muted1'>Loading public reference…</p>;

  const groups = [
    ['profile', 'Profile'],
    ['geography', 'Operating Geography'],
    ['production', 'Reference Production'],
    ['statistic', 'Reference Statistics'],
  ];
  const lib = data.library || {};
  return (
    <div className='mt-3 space-y-3'>
      {groups.map(([key, title]) => (data.reference?.[key]?.length > 0) && (
        <div key={key}>
          <h4 className='font-mono text-[10px] uppercase tracking-wider text-muted1'>{title}</h4>
          <dl className='mt-1 space-y-1.5'>
            {data.reference[key].map((r, i) => (
              <div key={i} className='rounded-xl border border-seam bg-paper/50 px-3 py-1.5'>
                <dt className='text-xs font-medium text-muted1'>{r.label}</dt>
                <dd className='text-xs font-semibold text-ink'>
                  {r.value}{r.unit ? ` ${r.unit}` : ''}
                </dd>
                <dd className='mt-0.5 font-mono text-[10px] text-muted1'>
                  public reference{r.as_of ? ` · ${r.as_of}` : ''} · {r.source}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
      <div>
        <h4 className='font-mono text-[10px] uppercase tracking-wider text-muted1'>From Your Library</h4>
        <p className='mt-1 font-mono text-xs text-muted0 tabular-nums'>
          {lib.documents ?? 0} document(s) · {lib.facts ?? 0} fact(s)
          {(lib.periods?.length > 0) && (
            <> · {lib.periods[0].slice(0, 4)}–{lib.periods[lib.periods.length - 1].slice(0, 4)}</>
          )}
        </p>
        {(lib.attributes?.length > 0) && (
          <p className='mt-0.5 font-mono text-[10.5px] text-muted1'>
            {lib.attributes.map((a) => String(a).replace('_', ' ')).join(' · ')}
          </p>
        )}
      </div>
      <Button to={`/search?q=${encodeURIComponent(name)}`} variant='secondary' size='sm' className='w-full'>Search Mentions</Button>
      <p className='font-mono text-[10px] leading-relaxed text-muted1'>
        Reference values are public context, not evidence — every number from
        your documents keeps its own receipt.
      </p>
    </div>
  );
}

export default function Graph() {
  const { data, error } = usePageData('/api/pages/graph');
  const [params, setParams] = useSearchParams();
  const [picked, setPicked] = useState(null);
  const [meta, setMeta] = useState({ legend: [], counts: {} });
  const { dark } = useTheme();
  const subsidiary = params.get('subsidiary') || '';
  const kind = params.get('kind') || '';
  const query = params.get('q') || '';
  const [qText, setQText] = useState(query);
  const qTimer = useRef(null);

  useEffect(() => { setQText(query); }, [query]);
  useEffect(() => () => { if (qTimer.current) clearTimeout(qTimer.current); }, []);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const set = (patch) => {
    setPicked(null);
    const next = {};
    if ('subsidiary' in patch) { if (patch.subsidiary) next.subsidiary = patch.subsidiary; }
    else if (subsidiary) next.subsidiary = subsidiary;
    if ('kind' in patch) { if (patch.kind) next.kind = patch.kind; }
    else if (kind) next.kind = kind;
    if ('q' in patch) { if (patch.q) next.q = patch.q; }
    else if (query) next.q = query;
    setParams(next);
  };

  const onQueryInput = (value) => {
    setQText(value);
    if (qTimer.current) clearTimeout(qTimer.current);
    qTimer.current = setTimeout(() => set({ q: value }), 350);
  };

  const legendDots = {
    document: 'bg-coal', organization: 'bg-violet-700', mine: 'bg-sky-700',
    location: 'bg-teal-600', geology: 'bg-yellow-700', metric: 'bg-pink-700',
    event: 'bg-red-600', tag: 'bg-emerald-600',
  };

  return (
    <div>
      <PageHeader
        title='Knowledge Graph'
        subtitle='Organizations, mines, locations, geology, documents, metrics and events — every relationship keeps its source receipt. Drag to pan, scroll to zoom, click a node to inspect it.'>
        <div className='flex flex-wrap gap-2'>
          <select
            value={subsidiary}
            onChange={(e) => set({ subsidiary: e.target.value })}
            className='rounded-lg border border-seam bg-surface px-3 py-1.5 text-xs text-ink shadow-card focus:border-coal focus:outline-none'
          >
            <option value=''>All subsidiaries</option>
            {data.subs.map((s) => <option key={s.subsidiary} value={s.subsidiary}>{s.subsidiary}</option>)}
          </select>
          <select
            value={kind}
            onChange={(e) => set({ kind: e.target.value })}
            className='rounded-lg border border-seam bg-surface px-3 py-1.5 text-xs text-ink shadow-card focus:border-coal focus:outline-none'
          >
            {KIND_FILTERS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
          <input
            value={qText}
            onChange={(e) => onQueryInput(e.target.value)}
            placeholder='Filter nodes…'
            className='w-40 rounded-lg border border-seam bg-surface px-3 py-1.5 text-xs text-ink placeholder:text-muted2 shadow-card focus:border-coal focus:outline-none'
          />
        </div>
      </PageHeader>

      <Rise delay={0.05}>
        <div className='mt-6 grid gap-5 lg:grid-cols-[1fr_280px]'>
          <Card className='relative overflow-hidden p-0'>
            <KnowledgeCanvas subsidiary={subsidiary} kind={kind} query={query} theme={dark ? 'dark' : 'light'} onPick={setPicked} onMeta={setMeta} />
            <div className='pointer-events-none absolute left-4 top-4 flex max-w-[70%] flex-wrap gap-3 font-mono text-[10px] uppercase tracking-wider text-muted1'>
              {(meta.legend.length > 0 ? meta.legend : [{ kind: 'document' }, { kind: 'tag' }, { kind: 'entity' }]).map((l) => (
                <span key={l.kind} className='flex items-center gap-1.5'>
                  <i className={`h-2 w-2 rounded-full ${legendDots[l.kind] || 'bg-stone-400'}`} />
                  {l.kind}{meta.counts[l.kind] != null ? ` ${meta.counts[l.kind]}` : ''}
                </span>
              ))}
            </div>
            <NodePanel picked={picked} onClose={() => setPicked(null)} />
          </Card>

          <aside className='space-y-4'>
            <Card className='p-4'>
              <h2 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Top Tags</h2>
              <div className='mt-3 flex flex-wrap gap-1.5'>
                {data.tags.length === 0 ? (
                  <p className='text-xs text-muted1'>No tags yet. Ingest documents to grow the tree.</p>
                ) : data.tags.map((t) => (
                  <Link
                    key={t.keyword}
                    to={`/search?tag=${encodeURIComponent(t.keyword)}`}
                    title={`used by ${t.count} documents`}
                    className='rounded-full border border-coalline bg-coalsoft px-2.5 py-1 text-xs text-coal transition-colors hover:border-coal'
                  >
                    {t.keyword} <span className='font-mono text-[10px] text-coal/60'>{t.count}</span>
                  </Link>
                ))}
              </div>
            </Card>
            <Card className='p-4'>
              <h2 className='text-xs font-semibold uppercase tracking-wider text-muted1'>How To Read It</h2>
              <p className='mt-2 text-xs leading-relaxed text-muted0'>Amber nodes are documents. Violet nodes are organizations, blue mines, teal locations, ochre geology, pink metrics and red events. Green nodes are tags extracted at ingestion time. Edges are typed relationships — operates, located in, has geology, reports metric, occurred at — each keeping its source receipt.</p>
              <p className='mt-2 text-xs text-muted1'>Drag the background to pan, scroll to zoom, double-click a node to focus it. Click any node to see its relationships with evidence.</p>
            </Card>
          </aside>
        </div>
      </Rise>
    </div>
  );
}
