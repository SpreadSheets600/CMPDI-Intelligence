import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'motion/react';
import { usePageData, cmpdiColors } from '../hooks/useData.js';
import { getJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { Tilt } from '../components/motion/tilt.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';

const COLORS = {
  document: { fill: '#d97706', text: '#fff', r: 9 },
  tag: { fill: '#059669', text: '#fff', r: 6 },
  entity: { fill: '#0369a1', text: '#fff', r: 7 },
};

function KnowledgeCanvas({ subsidiary, onPick }) {
  const canvasRef = useRef(null);
  const sim = useRef({ nodes: [], edges: [] });
  const hovered = useRef(null);
  const dragged = useRef(null);
  const selected = useRef(null);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext('2d');
    let raf = 0;
    let dead = false;
    selected.current = null;
    hovered.current = null;
    dragged.current = null;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, canvas.clientWidth * dpr);
      canvas.height = Math.max(1, canvas.clientHeight * dpr);
    };
    resize();
    window.addEventListener('resize', resize);

    (async () => {
      try {
        const data = await getJSON('/api/graph?subsidiary=' + encodeURIComponent(subsidiary || ''));
        if (dead) return;
        const W = canvas.clientWidth || 800, H = canvas.clientHeight || 560;
        setEmpty(!data.nodes || data.nodes.length === 0);
        sim.current.nodes = (data.nodes || []).map((n, i) => ({
          ...n,
          x: W / 2 + Math.cos(i * 2.4) * (60 + (i % 7) * 22),
          y: H / 2 + Math.sin(i * 2.4) * (60 + (i % 5) * 26),
          vx: 0, vy: 0,
          r: n.type === 'document' ? 10 : n.type === 'entity' ? 7 : 5 + Math.min(6, n.count || 1),
        }));
        const byId = new Map(sim.current.nodes.map((n) => [n.id, n]));
        const seen = new Set();
        sim.current.edges = (data.edges || [])
          .map((e) => ({ source: byId.get(e.source), target: byId.get(e.target) }))
          .filter((e) => {
            if (!e.source || !e.target) return false;
            const k = `${e.source.id}→${e.target.id}`;
            if (seen.has(k)) return false;
            seen.add(k);
            return true;
          });
        raf = requestAnimationFrame(tick);
      } catch {
        if (!dead) setEmpty(true);
      }
    })();

    function tick() {
      const { nodes, edges } = sim.current;
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
      for (const e of edges) {
        const dx = e.target.x - e.source.x, dy = e.target.y - e.source.y;
        const d = Math.max(1, Math.hypot(dx, dy));
        const f = (d - 90) * 0.015;
        e.source.vx += (dx / d) * f; e.source.vy += (dy / d) * f;
        e.target.vx -= (dx / d) * f; e.target.vy -= (dy / d) * f;
      }
      const W = canvas.clientWidth, H = canvas.clientHeight;
      for (const n of nodes) {
        n.vx += (W / 2 - n.x) * 0.003;
        n.vy += (H / 2 - n.y) * 0.003;
        if (n === dragged.current) { n.vx = 0; n.vy = 0; continue; }
        n.vx *= 0.82; n.vy *= 0.82;
        n.x += n.vx; n.y += n.vy;
        n.x = Math.max(24, Math.min(W - 24, n.x));
        n.y = Math.max(24, Math.min(H - 24, n.y));
      }
      draw();
      raf = requestAnimationFrame(tick);
    }

    function draw() {
      const dpr = window.devicePixelRatio || 1;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.scale(dpr, dpr);
      const t = cmpdiColors();
      const { nodes, edges } = sim.current;
      for (const e of edges) {
        const hot = hovered.current && (e.source === hovered.current || e.target === hovered.current);
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
        const hot = n === hovered.current || n === selected.current;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r + (hot ? 2.5 : 0), 0, Math.PI * 2);
        ctx.fillStyle = c.fill;
        ctx.globalAlpha = hovered.current && !hot && hovered.current.type === 'document' ? 0.35 : 1;
        ctx.fill();
        ctx.globalAlpha = 1;
        if (n.type !== 'document' || hot) {
          ctx.font = `${hot ? '600 ' : ''}11px "IBM Plex Mono", monospace`;
          ctx.fillStyle = t.muted3;
          ctx.fillText(n.label.length > 26 ? n.label.slice(0, 24) + '…' : n.label, n.x, n.y + n.r + 13);
        }
      }
      ctx.restore();
    }

    const nodeAt = (x, y) =>
      sim.current.nodes.find((n) => Math.hypot(n.x - x, n.y - y) <= n.r + 4) || null;

    const onDown = (e) => {
      const r = canvas.getBoundingClientRect();
      const n = nodeAt(e.clientX - r.left, e.clientY - r.top);
      if (n) { dragged.current = n; selected.current = n; onPick(n); }
    };
    const onUp = () => { dragged.current = null; };
    const onMove = (e) => {
      const r = canvas.getBoundingClientRect();
      const n = nodeAt(e.clientX - r.left, e.clientY - r.top);
      if (n !== hovered.current) {
        hovered.current = n;
        canvas.style.cursor = n ? 'pointer' : 'default';
      }
    };
    const onDrag = (e) => {
      if (!dragged.current) return;
      const r = canvas.getBoundingClientRect();
      dragged.current.x = e.clientX - r.left;
      dragged.current.y = e.clientY - r.top;
    };
    canvas.addEventListener('mousedown', onDown);
    window.addEventListener('mouseup', onUp);
    const onHover = (e) => { onMove(e); onDrag(e); };
    canvas.addEventListener('mousemove', onHover);
    return () => {
      dead = true;
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      canvas.removeEventListener('mousedown', onDown);
      window.removeEventListener('mouseup', onUp);
      canvas.removeEventListener('mousemove', onHover);
    };
  }, [subsidiary]);

  return (
    <div className='relative'>
      <canvas ref={canvasRef} className='block h-[560px] w-full' />
      {empty && (
        <p className='pointer-events-none absolute inset-0 flex items-center justify-center text-[13px] text-stone-400'>
          No documents in this view yet. Ingest files to grow the tree.
        </p>
      )}
    </div>
  );
}

function NodePanel({ picked, onClose }) {
  return (
    <AnimatePresence>
      {picked && (
        <motion.div
          initial={{ x: 60, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 60, opacity: 0 }}
          transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
          className='absolute inset-y-0 right-0 w-72 border-l border-seam bg-white/95 p-4 backdrop-blur'
        >
          <div className='flex items-start justify-between gap-2'>
            <h3 className='text-[13px] font-semibold leading-snug'>
              {picked.type === 'tag' ? `#${picked.label}` : picked.label}
            </h3>
            <button onClick={onClose} className='text-stone-400 hover:text-ink'>✕</button>
          </div>
          {picked.type === 'document' && (
            <>
              <p className='mt-2 font-mono text-[11px] uppercase text-stone-400'>{picked.group}</p>
              <Magnetic intensity={0.2} range={70} className='mt-4 block'>
                <Link to={`/doc/${picked.ref}`} className='block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white'>Open Document</Link>
              </Magnetic>
              <Link to={`/search?q=${encodeURIComponent(picked.label)}`} className='mt-2 block rounded-lg border border-seamdark px-3 py-2 text-center text-[13px] font-medium text-stone-600 hover:border-coal hover:text-coal'>Search Inside</Link>
            </>
          )}
          {picked.type === 'tag' && (
            <>
              <p className='mt-2 text-[13px] text-stone-500'>Extracted tag on {picked.count || '?'} document(s).</p>
              <Link to={`/search?tag=${encodeURIComponent(picked.label)}`} className='mt-4 block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white'>Search This Tag</Link>
            </>
          )}
          {picked.type === 'entity' && (
            <>
              <p className='mt-2 text-[13px] text-stone-500'>Entity resolved from the fact index.</p>
              <Link to={`/search?q=${encodeURIComponent(picked.label)}`} className='mt-4 block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white'>Search Mentions</Link>
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function Graph() {
  const { data, error } = usePageData('/api/pages/graph');
  const [params, setParams] = useSearchParams();
  const [picked, setPicked] = useState(null);
  const subsidiary = params.get('subsidiary') || '';

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  return (
    <div>
      <PageHeader
        title='Knowledge Tree'
        subtitle='Documents, their extracted tags and the entities they mention, laid out by force simulation. Click a node to inspect it.'>
        <select value={subsidiary}
                onChange={(e) => { setPicked(null); setParams(e.target.value ? { subsidiary: e.target.value } : {}); }}
                className='rounded-lg border border-seamdark bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none'>
          <option value=''>All subsidiaries</option>
          {data.subs.map((s) => <option key={s.subsidiary} value={s.subsidiary}>{s.subsidiary}</option>)}
        </select>
      </PageHeader>

      <Rise delay={0.05}>
        <div className='mt-6 grid gap-5 lg:grid-cols-[1fr_280px]'>
          <div className='relative overflow-hidden rounded-xl border border-seam bg-white shadow-card'>
            <KnowledgeCanvas subsidiary={subsidiary} onPick={setPicked} />
            <div className='pointer-events-none absolute left-4 top-4 flex max-w-[70%] flex-wrap gap-3 font-mono text-[10px] uppercase tracking-wide text-stone-400'>
              <span className='flex items-center gap-1.5'><i className='h-2.5 w-2.5 rounded-full bg-coal' />document</span>
              <span className='flex items-center gap-1.5'><i className='h-2.5 w-2.5 rounded-full bg-emerald-600' />tag</span>
              <span className='flex items-center gap-1.5'><i className='h-2.5 w-2.5 rounded-full bg-sky-700' />entity</span>
            </div>
            <NodePanel picked={picked} onClose={() => setPicked(null)} />
          </div>

          <aside className='space-y-4'>
            <Tilt rotationFactor={4} className='rounded-xl border border-seam bg-white p-4 shadow-card'>
              <h2 className='text-[13px] font-semibold uppercase tracking-wide text-stone-500'>Top Tags</h2>
              <div className='mt-3 flex flex-wrap gap-1.5'>
                {data.tags.length === 0 ? (
                  <p className='text-[13px] text-stone-400'>No tags yet. Ingest documents to grow the tree.</p>
                ) : data.tags.map((t) => (
                  <Link key={t.keyword} to={`/search?tag=${encodeURIComponent(t.keyword)}`}
                        title={`used by ${t.count} documents`}
                        className='rounded-full border border-coalline bg-coalsoft px-2.5 py-1 text-[12px] text-coal transition-colors hover:bg-amber-100'>
                    {t.keyword} <span className='font-mono text-[10px] text-coal/60'>{t.count}</span>
                  </Link>
                ))}
              </div>
            </Tilt>
            <div className='rounded-xl border border-seam bg-white p-4 shadow-card'>
              <h2 className='text-[13px] font-semibold uppercase tracking-wide text-stone-500'>How To Read It</h2>
              <p className='mt-2 text-[13px] leading-relaxed text-stone-600'>Amber nodes are documents. Green nodes are tags extracted at ingestion time. Blue nodes are entities resolved from the fact index. A document connects to every tag and entity it contains, so densely linked clusters usually mean one topic reported across many files.</p>
              <p className='mt-2 text-[13px] text-stone-500'>Click a document node to open it, or a tag to run a search.</p>
            </div>
          </aside>
        </div>
      </Rise>
    </div>
  );
}
