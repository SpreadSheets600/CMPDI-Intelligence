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

function KnowledgeCanvas({ subsidiary, kind, query, onPick, onMeta }) {
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
        const params = new URLSearchParams();
        if (subsidiary) params.set('subsidiary', subsidiary);
        if (kind) params.set('kinds', kind);
        if (query) params.set('q', query);
        const data = await getJSON('/api/graph?' + params.toString());
        if (dead) return;
        const W = canvas.clientWidth || 800, H = canvas.clientHeight || 560;
        setEmpty(!data.nodes || data.nodes.length === 0);
        if (onMeta) onMeta({ legend: data.legend || [], counts: data.counts || {} });
        sim.current.nodes = (data.nodes || []).map((n, i) => ({
          ...n,
          x: W / 2 + Math.cos(i * 2.4) * (60 + (i % 7) * 22),
          y: H / 2 + Math.sin(i * 2.4) * (60 + (i % 5) * 26),
          vx: 0, vy: 0,
          r: n.type === 'document' ? 10
            : n.type === 'organization' || n.type === 'mine' ? 8
            : n.type === 'entity' || n.type === 'event' || n.type === 'location' ? 7
            : 5 + Math.min(6, n.count || 1),
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
        const c = COLORS[n.type] || COLORS.entity;
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
  }, [subsidiary, kind, query]);

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
          className='absolute inset-y-0 right-0 w-80 overflow-y-auto border-l border-seam bg-white/95 p-4 backdrop-blur'
        >
          <div className='flex items-start justify-between gap-2'>
            <div>
              <h3 className='text-[13px] font-semibold leading-snug'>
                {picked.type === 'tag' ? `#${picked.label}` : picked.label}
              </h3>
              <p className='mt-0.5 font-mono text-[10px] uppercase tracking-widest text-stone-400'>{picked.type}</p>
            </div>
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
          {(picked.type === 'entity' || picked.type === 'organization') && (
            <EntityContext name={picked.ref || picked.label} />
          )}
          {hood && hood.edges && hood.edges.length > 0 && (
            <div className='mt-4'>
              <h4 className='font-mono text-[10px] uppercase tracking-widest text-stone-400'>
                Relationships ({hood.edges.length})
              </h4>
              <ul className='mt-2 space-y-2'>
                {hood.edges.slice(0, 12).map((e, i) => {
                  const otherId = e.source === picked.id ? e.target : e.source;
                  const other = (hood.neighbours || []).find((n) => n.id === otherId);
                  const ev = e.evidence || {};
                  return (
                    <li key={i} className='rounded-lg border border-seam bg-paper px-2.5 py-1.5'>
                      <p className='font-mono text-[10px] text-coal'>{e.relation.replace(/_/g, ' ')}</p>
                      <p className='text-[12.5px] font-semibold text-ink'>{other ? other.label : otherId}</p>
                      {ev.filename && (
                        <p className='mt-0.5 font-mono text-[10px] text-stone-400'>
                          {ev.filename}{ev.page_no ? ` · p.${ev.page_no}` : ''}
                        </p>
                      )}
                      {ev.snippet && (
                        <p className='mt-1 text-[11.5px] leading-snug text-stone-500'>
                          {ev.snippet.length > 140 ? ev.snippet.slice(0, 140) + '…' : ev.snippet}
                        </p>
                      )}
                      {ev.doc_id && (
                        <Link
                          to={ev.page_no ? `/doc/${ev.doc_id}?page=${ev.page_no}` : `/doc/${ev.doc_id}`}
                          className='mt-1 inline-block font-mono text-[10.5px] text-sky-700 hover:underline'
                        >
                          View Source
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
      <div className='mt-2'>
        <p className='text-[13px] text-stone-500'>Entity resolved from the fact index.</p>
        <p className='mt-1 font-mono text-[11px] text-stone-400'>No public reference for this entity yet.</p>
        <Link to={`/search?q=${encodeURIComponent(name)}`} className='mt-4 block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white'>Search Mentions</Link>
      </div>
    );
  }
  if (!data) return <p className='mt-2 font-mono text-[11px] text-stone-400'>Loading public reference…</p>;

  const groups = [
    ['profile', 'Profile'],
    ['geography', 'Operating Geography'],
    ['production', 'Reference Production'],
    ['statistic', 'Reference Statistics'],
  ];
  const lib = data.library || {};
  return (
    <div className='mt-2 space-y-3'>
      {groups.map(([key, title]) => (data.reference?.[key]?.length > 0) && (
        <div key={key}>
          <h4 className='font-mono text-[10px] uppercase tracking-widest text-stone-400'>{title}</h4>
          <dl className='mt-1 space-y-1.5'>
            {data.reference[key].map((r, i) => (
              <div key={i} className='rounded-lg border border-seam bg-paper px-2.5 py-1.5'>
                <dt className='text-[11px] font-medium text-stone-500'>{r.label}</dt>
                <dd className='text-[12.5px] font-semibold text-ink'>
                  {r.value}{r.unit ? ` ${r.unit}` : ''}
                </dd>
                <dd className='mt-0.5 font-mono text-[10px] text-stone-400'>
                  public reference{r.as_of ? ` · ${r.as_of}` : ''} · {r.source}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
      <div>
        <h4 className='font-mono text-[10px] uppercase tracking-widest text-stone-400'>From Your Library</h4>
        <p className='mt-1 text-[12.5px] text-stone-600'>
          {lib.documents ?? 0} document(s) · {lib.facts ?? 0} fact(s)
          {(lib.periods?.length > 0) && (
            <> · {lib.periods[0].slice(0, 4)}–{lib.periods[lib.periods.length - 1].slice(0, 4)}</>
          )}
        </p>
        {(lib.attributes?.length > 0) && (
          <p className='mt-0.5 font-mono text-[10.5px] text-stone-400'>
            {lib.attributes.map((a) => String(a).replace('_', ' ')).join(' · ')}
          </p>
        )}
      </div>
      <Link to={`/search?q=${encodeURIComponent(name)}`} className='block rounded-lg bg-coal px-3 py-2 text-center text-[13px] font-semibold text-white'>Search Mentions</Link>
      <p className='font-mono text-[10px] leading-relaxed text-stone-400'>
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
  const subsidiary = params.get('subsidiary') || '';
  const kind = params.get('kind') || '';
  const query = params.get('q') || '';

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

  const legendDots = {
    document: 'bg-coal', organization: 'bg-violet-700', mine: 'bg-sky-700',
    location: 'bg-teal-600', geology: 'bg-yellow-700', metric: 'bg-pink-700',
    event: 'bg-red-600', tag: 'bg-emerald-600',
  };

  return (
    <div>
      <PageHeader
        title='Knowledge Graph'
        subtitle='Organizations, mines, locations, geology, documents, metrics and events — every relationship keeps its source receipt. Click a node to inspect it.'>
        <div className='flex flex-wrap gap-2'>
          <select value={subsidiary}
                  onChange={(e) => set({ subsidiary: e.target.value })}
                  className='rounded-lg border border-seamdark bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none'>
            <option value=''>All subsidiaries</option>
            {data.subs.map((s) => <option key={s.subsidiary} value={s.subsidiary}>{s.subsidiary}</option>)}
          </select>
          <select value={kind}
                  onChange={(e) => set({ kind: e.target.value })}
                  className='rounded-lg border border-seamdark bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none'>
            {KIND_FILTERS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
          <input value={query}
                 onChange={(e) => set({ q: e.target.value })}
                 placeholder='Filter nodes…'
                 className='w-40 rounded-lg border border-seamdark bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none' />
        </div>
      </PageHeader>

      <Rise delay={0.05}>
        <div className='mt-6 grid gap-5 lg:grid-cols-[1fr_280px]'>
          <div className='relative overflow-hidden rounded-xl border border-seam bg-white shadow-card'>
            <KnowledgeCanvas subsidiary={subsidiary} kind={kind} query={query} onPick={setPicked} onMeta={setMeta} />
            <div className='pointer-events-none absolute left-4 top-4 flex max-w-[70%] flex-wrap gap-3 font-mono text-[10px] uppercase tracking-wide text-stone-400'>
              {(meta.legend.length > 0 ? meta.legend : [{ kind: 'document' }, { kind: 'tag' }, { kind: 'entity' }]).map((l) => (
                <span key={l.kind} className='flex items-center gap-1.5'>
                  <i className={`h-2.5 w-2.5 rounded-full ${legendDots[l.kind] || 'bg-stone-400'}`} />
                  {l.kind}{meta.counts[l.kind] != null ? ` ${meta.counts[l.kind]}` : ''}
                </span>
              ))}
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
              <p className='mt-2 text-[13px] leading-relaxed text-stone-600'>Amber nodes are documents. Violet nodes are organizations, blue mines, teal locations, ochre geology, pink metrics and red events. Green nodes are tags extracted at ingestion time. Edges are typed relationships — operates, located in, has geology, reports metric, occurred at — each keeping its source receipt.</p>
              <p className='mt-2 text-[13px] text-stone-500'>Click any node to see its relationships with evidence. Click a document node to open it, or a tag to run a search.</p>
            </div>
          </aside>
        </div>
      </Rise>
    </div>
  );
}
