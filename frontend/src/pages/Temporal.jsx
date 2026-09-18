import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { getJSON } from '../api.js';
import { usePageData, cmpdiColors } from '../hooks/useData.js';
import { Rise, PageHeader, Loading, ErrorBox, Reveal } from '../components/ui.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';

function docHref(docId, pageNo, sheetNo) {
  if (pageNo) return `/doc/${docId}?page=${pageNo}`;
  if (sheetNo != null) return `/doc/${docId}?sheet=${sheetNo}`;
  return `/doc/${docId}`;
}

// Line chart over the median-per-period series; hover shows the
// period's receipt (first reported value with its source link).
// Forecast estimates render as a dashed extension with a shaded band,
// visually distinct from reported values.
function TimelineChart({ points, forecast }) {
  const canvasRef = useRef(null);
  const hover = useRef(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.scale(dpr, dpr);
    const W = canvas.clientWidth, H = canvas.clientHeight;
    ctx.clearRect(0, 0, W, H);
    const T = cmpdiColors();
    if (!points.length) {
      ctx.fillStyle = T.muted1;
      ctx.font = '13px "IBM Plex Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('No reported values for this combination.', W / 2, H / 2);
      return;
    }
    const pad = { l: 56, r: 16, t: 18, b: 34 };
    const fc = forecast && forecast.status === 'ok' ? (forecast.forecast || []) : [];
    const vals = [...points.map((p) => p.value_mt)];
    fc.forEach((f) => { vals.push(f.value_mt, f.low_mt, f.high_mt); });
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const span = hi - lo || Math.abs(hi) || 1;
    const yOf = (v) => pad.t + (H - pad.t - pad.b) * (1 - (v - lo) / span);
    const total = points.length + fc.length;
    const xOf = (i) => total === 1
      ? (pad.l + W - pad.r) / 2
      : pad.l + ((W - pad.l - pad.r) * i) / (total - 1);

    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.textAlign = 'right';
    ctx.fillStyle = T.muted1;
    ctx.strokeStyle = T.seam;
    for (let i = 0; i <= 4; i++) {
      const v = lo + (span * i) / 4;
      const y = yOf(v);
      ctx.fillText(v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(1), pad.l - 8, y + 3);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
    }

    ctx.strokeStyle = '#d97706';
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((p, i) => {
      const x = xOf(i), y = yOf(p.value_mt);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    points.forEach((p, i) => {
      const x = xOf(i), y = yOf(p.value_mt);
      ctx.fillStyle = p.low_conf ? '#dc2626' : '#d97706';
      ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = T.muted2;
      ctx.textAlign = 'center';
      ctx.fillText((p.label || '').replace('FY', ''), x, H - pad.b + 14);
      p._x = x; p._y = y;
    });
    if (fc.length) {
      // Shaded uncertainty band over the forecast span.
      ctx.beginPath();
      fc.forEach((f, k) => {
        const x = xOf(points.length + k), y = yOf(f.high_mt);
        if (k === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      for (let k = fc.length - 1; k >= 0; k--) {
        ctx.lineTo(xOf(points.length + k), yOf(fc[k].low_mt));
      }
      ctx.closePath();
      ctx.fillStyle = 'rgba(217, 119, 6, 0.14)';
      ctx.fill();
      // Dashed estimate line continuing from the last reported point.
      ctx.strokeStyle = '#b45309';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(xOf(points.length - 1), yOf(points[points.length - 1].value_mt));
      fc.forEach((f, k) => ctx.lineTo(xOf(points.length + k), yOf(f.value_mt)));
      ctx.stroke();
      ctx.setLineDash([]);
      fc.forEach((f, k) => {
        const x = xOf(points.length + k), y = yOf(f.value_mt);
        ctx.strokeStyle = '#b45309';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = T.surface || '#ffffff';
        ctx.fill();
        ctx.fillStyle = T.muted2;
        ctx.textAlign = 'center';
        ctx.fillText((f.label || '').replace('FY', ''), x, H - pad.b + 14);
      });
    }
    hover.current = { xOf, yOf };
  }, [points, forecast]);

  useEffect(() => {
    draw();
    window.addEventListener('themechange', draw);
    return () => window.removeEventListener('themechange', draw);
  }, [draw]);

  const onMove = (e) => {
    const canvas = canvasRef.current;
    const box = document.getElementById('temporal-receipt');
    if (!box) return;
    const r = canvas.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    const hit = points.find((p) => p._x !== undefined && Math.hypot(mx - p._x, my - p._y) < 14);
    if (!hit) { box.classList.add('hidden'); return; }
    box.classList.remove('hidden');
    const first = hit.values[0];
    const loc = first.page_no ? `page ${first.page_no}` : first.sheet_no != null ? `sheet ${first.sheet_no}` : 'source';
    box.innerHTML = `
      <strong>${hit.label}</strong> · median <span class="font-mono">${hit.value_mt} MT</span>
      ${hit.yoy_pct != null ? `(${hit.yoy_pct > 0 ? '+' : ''}${hit.yoy_pct}% YoY)` : ''}<br>
      First value: <span class="font-mono">${first.value_raw}</span> ${first.unit || ''} —
      <a class="text-coal font-medium underline underline-offset-2"
         href="/doc/${first.doc_id}${first.page_no ? `/?page=${first.page_no}` : `?sheet=${first.sheet_no ?? 1}`}">${first.filename}, ${loc}</a>
      ${hit.n_sources > 1 ? `<span class="ml-2 text-stone-500">median of ${hit.n_sources} sources</span>` : ''}`;
  };

  return <canvas ref={canvasRef} onMouseMove={onMove} className='block h-[300px] w-full' />;
}

export default function Temporal() {
  const { data: options, error: optionsError } = usePageData('/api/temporal/options');
  const [entity, setEntity] = useState('');
  const [attribute, setAttribute] = useState('');
  const [superseded, setSuperseded] = useState(false);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [horizon, setHorizon] = useState(3);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState(null);

  const load = async (e = null, a = null, s = null) => {
    const ent = e ?? entity, attr = a ?? attribute, sup = s ?? superseded;
    if (!ent || !attr) return;
    setLoading(true);
    setError(null);
    setForecast(null);
    setForecastError(null);
    try {
      const qs = new URLSearchParams({ entity: ent, attribute: attr });
      if (sup) qs.set('superseded', '1');
      setTimeline(await getJSON(`/api/temporal/timeline?${qs.toString()}`));
    } catch (err) {
      setError(err.message);
      setTimeline(null);
    } finally {
      setLoading(false);
    }
  };

  const loadForecast = async () => {
    if (!timeline || !timeline.points.length) return;
    setForecastLoading(true);
    setForecastError(null);
    try {
      const qs = new URLSearchParams({
        entity: timeline.entity,
        attribute: timeline.attribute,
        horizon: String(horizon),
      });
      if (superseded) qs.set('superseded', '1');
      setForecast(await getJSON(`/api/temporal/forecast?${qs.toString()}`));
    } catch (err) {
      setForecastError(err.message);
      setForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  if (optionsError) return <ErrorBox message={optionsError} />;
  if (!options) return <Loading label='Loading timeline options…' />;

  const stats = timeline && timeline.points.length > 0 ? [
    { label: 'Periods', value: String(timeline.n_periods) },
    { label: 'Documents', value: String(timeline.n_docs) },
    { label: 'Change', value: timeline.delta_pct != null ? `${timeline.delta_pct > 0 ? '+' : ''}${timeline.delta_pct}%` : 'n/a' },
    { label: 'CAGR', value: timeline.cagr_pct != null ? `${timeline.cagr_pct > 0 ? '+' : ''}${timeline.cagr_pct}% p.a.` : 'n/a' },
  ] : [];

  return (
    <div>
      <PageHeader
        title='Temporal'
        subtitle='Historical timelines for production, reserves, drilling, dispatch and other metrics — median of reported values per period, every point with its receipt.'
      />

      <Rise delay={0.05}>
        <div className='mt-6 rounded-xl border border-seam bg-white p-5 shadow-card'>
          <div className='flex flex-wrap items-end gap-3'>
            <label className='w-full min-w-0 flex-1 sm:min-w-[200px] sm:max-w-[280px]'>
              <span className='text-[12px] font-medium text-stone-500'>Entity</span>
              <select value={entity} onChange={(e) => setEntity(e.target.value)}
                      className='mt-1 w-full rounded-lg border border-seamdark bg-white px-3 py-2 text-sm focus:border-coal focus:outline-none'>
                <option value=''>Choose entity...</option>
                {options.entities.map((e) => <option key={e.name} value={e.name}>{e.name} ({e.n_periods}p)</option>)}
              </select>
            </label>
            <label className='w-full min-w-0 flex-1 sm:min-w-[200px] sm:max-w-[280px]'>
              <span className='text-[12px] font-medium text-stone-500'>Metric</span>
              <select value={attribute} onChange={(e) => setAttribute(e.target.value)}
                      className='mt-1 w-full rounded-lg border border-seamdark bg-white px-3 py-2 text-sm focus:border-coal focus:outline-none'>
                <option value=''>Choose metric...</option>
                {options.attributes.map((a) => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
              </select>
            </label>
            <label className='flex items-center gap-2 pb-2.5 text-[13px] text-stone-500'>
              <input type='checkbox' checked={superseded} onChange={(e) => setSuperseded(e.target.checked)} />
              Include superseded
            </label>
            <Magnetic intensity={0.25} range={90}>
              <button onClick={() => load()} disabled={loading || !entity || !attribute}
                      className='rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-colors hover:bg-amber-500 disabled:opacity-50'>
                {loading ? 'Loading…' : 'Load Timeline'}
              </button>
            </Magnetic>
          </div>
          {error && <ErrorBox message={error} />}
          {!timeline && !error && (
            <p className='mt-4 text-sm text-stone-500'>Select an entity and a metric to build its historical timeline.</p>
          )}
          {timeline && !timeline.points.length && (
            <p className='mt-4 rounded-lg border border-dashed border-seamdark p-4 text-center text-sm text-stone-500'>
              No timeline values for {timeline.entity} · {timeline.attribute.replace(/_/g, ' ')} in the reporting window.
            </p>
          )}
          {timeline && !!timeline.points.length && (
            <>
              <div className='mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4'>
                {stats.map((s) => (
                  <div key={s.label} className='rounded-lg border border-seam bg-paper px-3 py-2.5'>
                    <p className='text-[11px] font-medium uppercase tracking-wide text-stone-500'>{s.label}</p>
                    <p className='mt-0.5 font-mono text-[17px] font-semibold'>{s.value}</p>
                  </div>
                ))}
              </div>
              <div className='mt-4'>
                <TimelineChart points={timeline.points} forecast={forecast} />
                <div id='temporal-receipt' className='mt-3 hidden rounded-lg border border-coalline bg-coalsoft px-3 py-2 text-[12.5px]'></div>
                <p className='mt-2 font-mono text-[11px] text-stone-400'>
                  Values in MT (scale-normalized) · {timeline.include_superseded ? 'including superseded revisions' : 'current versions only'}
                  {timeline.low_conf_share > 0 ? ` · ${(timeline.low_conf_share * 100).toFixed(0)}% low-confidence digits` : ''}
                </p>
              </div>
              <div className='mt-5 rounded-lg border border-dashed border-seamdark p-4'>
                <div className='flex flex-wrap items-center gap-3'>
                  <div>
                    <p className='text-[13px] font-semibold'>Trend forecast</p>
                    <p className='text-[12px] text-stone-500'>Linear projection of the reported medians — estimates, not reported figures.</p>
                  </div>
                  <div className='ml-auto flex items-center gap-2'>
                    <label className='text-[12px] text-stone-500'>
                      Horizon{' '}
                      <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}
                              className='rounded-lg border border-seamdark bg-white px-2 py-1.5 text-[13px] focus:border-coal focus:outline-none'>
                        {[1, 2, 3, 4, 5].map((h) => <option key={h} value={h}>{h} yr</option>)}
                      </select>
                    </label>
                    <button onClick={loadForecast} disabled={forecastLoading}
                            className='rounded-lg border border-coal px-4 py-2 text-[13px] font-semibold text-coal transition-colors hover:bg-coal hover:text-white disabled:opacity-50'>
                      {forecastLoading ? 'Estimating…' : forecast ? 'Re-estimate' : 'Estimate future trend'}
                    </button>
                  </div>
                </div>
                {forecastError && <ErrorBox message={forecastError} />}
                {forecast && forecast.status === 'insufficient' && (
                  <p className='mt-3 rounded-lg bg-paper px-3 py-2.5 text-[13px] text-stone-500'>{forecast.reason}</p>
                )}
                {forecast && forecast.status === 'ok' && (
                  <>
                    <p className='mt-3 text-[12.5px] text-stone-600'>
                      <span className={`mr-2 inline-block rounded-full px-2 py-px font-mono text-[11px] font-semibold uppercase tracking-wide ${
                        forecast.confidence === 'high' ? 'bg-emerald-100 text-emerald-800'
                        : forecast.confidence === 'medium' ? 'bg-amber-100 text-amber-800'
                        : 'bg-red-100 text-red-800'}`}>
                        {forecast.confidence} confidence
                      </span>
                      OLS linear trend: {forecast.slope_mt_per_year > 0 ? '+' : ''}{forecast.slope_mt_per_year} MT/yr,
                      R² {forecast.r_squared}, fit over {forecast.n_periods} periods
                      ({forecast.confidence_reasons.join('; ')}).
                    </p>
                    <div className='mt-2 overflow-x-auto'>
                      <table className='w-full min-w-[420px] text-sm'>
                        <thead>
                          <tr className='border-b border-seam text-left font-mono text-[11px] uppercase tracking-wide text-stone-500'>
                            <th className='py-2 pr-4 font-medium'>Period</th>
                            <th className='py-2 pr-4 text-right font-medium'>Estimate (MT)</th>
                            <th className='py-2 text-right font-medium'>Range (MT)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {forecast.forecast.map((f) => (
                            <tr key={f.period} className='border-b border-seam last:border-0'>
                              <td className='py-1.5 pr-4 font-mono text-[12.5px]'>{f.label}</td>
                              <td className='py-1.5 pr-4 text-right font-mono text-[13px] font-semibold'>
                                {f.value_mt}
                                <span className='ml-1.5 rounded-full bg-amber-100 px-1.5 py-px text-[10px] font-normal text-amber-800'>estimated</span>
                              </td>
                              <td className='py-1.5 text-right font-mono text-[12px] text-stone-500'>{f.low_mt} – {f.high_mt}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <ul className='mt-2 space-y-1'>
                      {forecast.warnings.map((w, i) => (
                        <li key={i} className='text-[12px] text-stone-500'>· {w}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </Rise>

      {timeline && !!timeline.points.length && (
        <Reveal className='mt-6 overflow-x-auto rounded-xl border border-seam bg-white shadow-card'>
          <table className='w-full min-w-[640px] text-sm'>
            <thead>
              <tr className='border-b border-seam bg-paper text-left font-mono text-[11px] uppercase tracking-wide text-stone-500'>
                <th className='px-4 py-2.5 font-medium'>Period</th>
                <th className='px-4 py-2.5 text-right font-medium'>Median (MT)</th>
                <th className='px-4 py-2.5 text-right font-medium'>YoY</th>
                <th className='px-4 py-2.5 text-center font-medium'>Sources</th>
                <th className='px-4 py-2.5 font-medium'>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {timeline.points.map((p) => (
                <tr key={p.period} className='border-b border-seam last:border-0'>
                  <td className='px-4 py-2 font-mono text-[12.5px]'>{p.label}</td>
                  <td className='px-4 py-2 text-right font-mono text-[13px] font-semibold'>
                    {p.value_mt}
                    {p.low_conf && <span className='ml-1.5 rounded-full bg-red-50 px-1.5 py-px text-[10px] font-normal text-red-700'>low-conf</span>}
                  </td>
                  <td className='px-4 py-2 text-right font-mono text-[12.5px] text-stone-500'>
                    {p.yoy_pct != null ? `${p.yoy_pct > 0 ? '+' : ''}${p.yoy_pct}%` : '—'}
                  </td>
                  <td className='px-4 py-2 text-center font-mono text-[12px] text-stone-500'>{p.n_sources}</td>
                  <td className='px-4 py-2 text-[12.5px]'>
                    <Link className='font-medium text-coal hover:underline'
                          to={docHref(p.values[0].doc_id, p.values[0].page_no, p.values[0].sheet_no)}>
                      {p.values[0].filename}
                    </Link>
                    <span className='ml-1.5 font-mono text-[11px] text-stone-400'>
                      {p.values[0].value_raw} {p.values[0].unit || ''}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Reveal>
      )}

      {timeline && !!timeline.coverage_gaps?.length && (
        <p className='mt-4 rounded-xl border border-seam bg-white px-4 py-3 text-[13px] text-stone-500 shadow-card'>
          Coverage gap: no reported values for {timeline.coverage_gaps.join(', ')}. Gaps mean silence in the library, not zero output.
        </p>
      )}

      {timeline && !!timeline.conflicts?.length && (
        <Reveal>
          <div className='mt-6 flex items-baseline justify-between'>
            <h2 className='text-lg font-semibold tracking-tight'>Conflicts on this timeline ({timeline.conflicts.length})</h2>
            <Link to={`/conflicts?entity=${encodeURIComponent(timeline.entity)}&attribute=${encodeURIComponent(timeline.attribute)}`}
                  className='text-[12.5px] font-medium text-coal hover:underline'>Open in Conflict Radar</Link>
          </div>
          <div className='mt-3 space-y-2'>
            {timeline.conflicts.map((c) => (
              <div key={c.key} className='rounded-xl border border-red-200 bg-red-50/60 px-4 py-3'>
                <p className='text-[13px] font-semibold'>{c.period} <span className='font-mono font-normal text-red-700'>differs by {c.spread_pct}%</span></p>
                <div className='mt-1.5 space-y-1'>
                  {c.values.map((v, i) => (
                    <p key={i} className='text-[12.5px] text-stone-600'>
                      <span className='font-mono font-semibold text-stone-800'>{v.value_raw} {v.unit || ''}</span>
                      {' '}— <Link className='font-medium text-coal hover:underline' to={docHref(v.doc_id, v.page_no, v.sheet_no)}>{v.filename}</Link>
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Reveal>
      )}
    </div>
  );
}
