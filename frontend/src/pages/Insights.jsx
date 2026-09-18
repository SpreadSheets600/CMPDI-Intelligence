import { useCallback, useEffect, useRef, useState } from 'react';
import { getJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button, Table, TableHead, TableHeader, TableBody, TableRow, TableCell } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { AnimatedNumber } from '../components/motion/animated-number.jsx';
import { Reveal } from '../components/ui.jsx';
import { usePageData, cmpdiColors } from '../hooks/useData.js';

// Bar chart over the fact series, drawn on canvas; every bar carries a
// receipt (document, page/sheet) shown on hover.
function FactChart({ entity, attribute, series }) {
  const canvasRef = useRef(null);
  const meta = useRef(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = devicePixelRatio;
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.scale(dpr, dpr);
    const W = canvas.clientWidth, H = canvas.clientHeight;
    ctx.clearRect(0, 0, W, H);
    const T = cmpdiColors();

    if (!series.length) {
      ctx.fillStyle = T.muted1;
      ctx.font = '13px "IBM Plex Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('No reported values for this combination.', W / 2, H / 2);
      return;
    }
    const pad = { l: 56, r: 16, t: 18, b: 34 };
    const maxV = Math.max(...series.map((s) => s.value_norm)) * 1.12;
    const bw = Math.min(34, (W - pad.l - pad.r) / series.length - 4);
    const plotH = H - pad.t - pad.b;

    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.textAlign = 'right';
    ctx.fillStyle = T.muted1;
    ctx.strokeStyle = T.seam;
    for (let i = 0; i <= 4; i++) {
      const y = pad.t + plotH - plotH * i / 4;
      const v = (maxV * i) / 4;
      ctx.fillText(v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v.toFixed(1), pad.l - 8, y + 3);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    }

    const step = (W - pad.l - pad.r) / series.length;
    series.forEach((s, i) => {
      const h = (s.value_norm / maxV) * plotH;
      const x = pad.l + i * step + (step - bw) / 2;
      const y = pad.t + plotH - h;
      ctx.fillStyle = i === 0 ? '#d97706' : '#f59e0b';
      ctx.fillRect(x, y, bw, h);
      ctx.save();
      ctx.translate(x + bw / 2, H - pad.b + 12);
      ctx.fillStyle = T.muted2;
      ctx.textAlign = 'center';
      const yr = (s.period_norm || '').slice(0, 4);
      ctx.fillText(yr ? yr.slice(2) + "'" : '?', 0, 0);
      ctx.restore();
      s._x = x; s._y = y; s._w = bw; s._h = h;
    });
    meta.current = { entity, attribute };
  }, [series, entity, attribute]);

  useEffect(() => {
    draw();
    window.addEventListener('themechange', draw);
    return () => window.removeEventListener('themechange', draw);
  }, [draw]);

  const onMove = (e) => {
    const canvas = canvasRef.current;
    const r = canvas.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    const hit = series.find((s) => s._x !== undefined && mx >= s._x && mx <= s._x + s._w && my >= s._y - 6);
    const box = document.getElementById('receipts');
    if (!hit || !box) { box && box.classList.add('hidden'); return; }
    box.classList.remove('hidden');
    const loc = hit.page_no ? `page ${hit.page_no}` : `sheet ${hit.sheet_no}`;
    box.innerHTML = `
      <strong>${meta.current.entity} · ${meta.current.attribute.replace('_', ' ')} · ${hit.period_norm || 'period n/a'}</strong><br>
      Reported value: <span class="font-mono">${hit.value_raw}</span> ${hit.unit || ''}<br>
      Source: <a class="text-coal font-medium underline underline-offset-2"
                  href="/doc/${hit.doc_id}${hit.page_no ? `?page=${hit.page_no}` : `?sheet=${hit.sheet_no || 1}`}">${hit.filename}, ${loc}</a>
      ${hit.flags ? `<span class="ml-2 font-mono text-[11px] text-bad font-semibold">${String(hit.flags).replace('_', ' ')}</span>` : ''}`;
  };

  return <canvas ref={canvasRef} onMouseMove={onMove} className='block h-[320px] w-full' />;
}

export default function Insights() {
  const { data, error } = usePageData('/api/pages/insights');
  const params = new URLSearchParams(window.location.search);
  const [entity, setEntity] = useState(params.get('entity') || '');
  const [attribute, setAttribute] = useState(params.get('attribute') || '');
  const [series, setSeries] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    getJSON('/api/insights/summary').then(setSummary).catch(() => {});
  }, []);

  const loadFacts = async (e = null, a = null) => {
    const ent = e ?? entity, attr = a ?? attribute;
    if (!ent || !attr) return;
    setSeries(null);
    try {
      const res = await getJSON(`/api/facts?entity=${encodeURIComponent(ent)}&attribute=${encodeURIComponent(attr)}`);
      setSeries(res);
    } catch { setSeries({ entity: ent, attribute: attr, series: [] }); }
  };

  // Deep-links from the Dashboard signals carry entity + attribute.
  useEffect(() => {
    if (entity && attribute && series === null && data) loadFacts(entity, attribute);
  }, [data]);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const qs = data.quality_stats;

  const qualityCards = [
    { label: 'Documents processed', value: qs.documents.pct, suffix: '%', bar: qs.documents.pct, barCls: 'bg-emerald-600', foot: `${qs.documents.completed} of ${qs.documents.total} · ${qs.documents.failed} failed` },
    { label: 'High-confidence OCR', value: qs.ocr.pct, suffix: '%', bar: qs.ocr.pct || 0, barCls: 'bg-coal', foot: `${qs.ocr.high_confidence} of ${qs.ocr.documents} OCR documents (threshold 88%)`, dash: qs.ocr.pct == null },
    { label: 'Facts without quarantine', value: qs.facts.pct, suffix: '%', bar: qs.facts.pct, barCls: 'bg-emerald-600', foot: `${parseInt(qs.facts.verified)} of ${parseInt(qs.facts.total)} flagged clean` },
  ];

  return (
    <div>
      <PageHeader
        title='Insights'
        subtitle='The fact index made visible: explore any metric across documents and fiscal years — every value with its receipt — then check how clean the extraction layer is.'
      />

      <Rise delay={0.05}>
        <Card className='mt-6 p-5'>
          <div className='flex flex-wrap items-end gap-3'>
            <label className='w-full min-w-0 flex-1 sm:min-w-[200px] sm:max-w-[280px]'>
              <span className='text-xs font-medium text-muted1'>Entity</span>
              <select
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                className='mt-1 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink focus:border-coal focus:outline-none'
              >
                <option value=''>Choose entity...</option>
                {data.entities.map((e) => <option key={e.canonical_name} value={e.canonical_name}>{e.canonical_name} ({e.n})</option>)}
              </select>
            </label>
            <label className='w-full min-w-0 flex-1 sm:min-w-[200px] sm:max-w-[280px]'>
              <span className='text-xs font-medium text-muted1'>Metric</span>
              <select
                value={attribute}
                onChange={(e) => setAttribute(e.target.value)}
                className='mt-1 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink focus:border-coal focus:outline-none'
              >
                <option value=''>Choose metric...</option>
                {data.attributes.map((a) => <option key={a.attribute} value={a.attribute}>{a.attribute.replace('_', ' ')}</option>)}
              </select>
            </label>
            <Button
              variant='primary'
              size='md'
              onClick={() => loadFacts()}
              className='px-5'
            >
              Load Facts
            </Button>
          </div>
          {series && <FactChart entity={series.entity} attribute={series.attribute} series={series.series} />}
          <div id='receipts' className='mt-3 hidden rounded-xl border border-coalline bg-coalsoft px-3.5 py-2.5 text-xs text-ink'></div>
        </Card>
      </Rise>

      <Rise delay={0.1}>
        <h2 id='quality' className='mt-10 text-base font-semibold tracking-tight text-ink'>Data Quality</h2>
        <p className='mt-1 max-w-[65ch] text-xs text-muted1'>Measured from the live library: how much survived processing, how trustworthy the OCR layer is, and how much of the fact index is clean of quarantine flags.</p>

        <AnimatedGroup preset='blur-slide' className='mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3'>
          {qualityCards.map((c) => (
            <Card key={c.label} className='p-5'>
              <div className='flex items-center justify-between'>
                <span className='text-xs font-medium text-muted1'>{c.label}</span>
                {c.dash
                  ? <span className='font-mono text-xl font-semibold text-ink'>-%</span>
                  : <AnimatedNumber value={c.value} className='font-mono text-xl font-semibold tabular-nums text-ink' />}
              </div>
              <div className='mt-2.5 h-1.5 overflow-hidden rounded-full bg-paper'>
                <div className={`h-full rounded-full ${c.barCls}`} style={{ width: `${c.bar}%` }}></div>
              </div>
              <p className='mt-2 font-mono text-[11px] text-muted1 tabular-nums'>{c.foot}</p>
            </Card>
          ))}
        </AnimatedGroup>
      </Rise>

      {summary && (
        <Reveal className='mt-6'>
          <Table>
            <TableHead>
              <tr>
                <TableHeader>Document</TableHeader>
                <TableHeader>Type</TableHeader>
                <TableHeader numeric>Pages/OCR</TableHeader>
                <TableHeader numeric>Chunks</TableHeader>
                <TableHeader numeric>Facts</TableHeader>
                <TableHeader numeric>Tags</TableHeader>
              </tr>
            </TableHead>
            <TableBody>
              {summary.doc_quality.map((d, i) => (
                <TableRow key={i}>
                  <TableCell className='font-medium text-ink'>{d.filename}</TableCell>
                  <TableCell mono className='uppercase text-muted1'>{d.doc_type}</TableCell>
                  <TableCell numeric>{d.page_count || d.ocr_pages || '—'}</TableCell>
                  <TableCell numeric>{d.chunks}</TableCell>
                  <TableCell numeric>{d.facts}</TableCell>
                  <TableCell numeric>{d.tags}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Reveal>
      )}

      <Reveal>
        <h2 className='mt-10 text-base font-semibold tracking-tight text-ink'>Extraction By Type</h2>
        <Table className='mt-4'>
          <TableHead>
            <tr>
              <TableHeader>Document Type</TableHeader>
              <TableHeader numeric>Documents</TableHeader>
              <TableHeader numeric>Processed</TableHeader>
            </tr>
          </TableHead>
          <TableBody>
            {qs.by_type.map((r) => (
              <TableRow key={r.doc_type}>
                <TableCell mono className='uppercase text-ink'>{r.doc_type}</TableCell>
                <TableCell numeric>{r.documents}</TableCell>
                <TableCell numeric className={r.processed_pct >= 95 ? 'text-ok font-semibold' : 'text-coal'}>
                  {r.processed_pct}%
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Reveal>
    </div>
  );
}
