import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Pickaxe } from 'lucide-react';
import { getJSON } from '../api.js';
import { usePageData } from '../hooks/useData.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';

function docHref(docId, pageNo, sheetNo) {
  if (pageNo) return `/doc/${docId}?page=${pageNo}`;
  if (sheetNo != null) return `/doc/${docId}?sheet=${sheetNo}`;
  return `/doc/${docId}`;
}

function ReceiptLink({ docId, filename, pageNo, sheetNo }) {
  if (!docId) return <span className='text-stone-400'>no source</span>;
  const loc = pageNo ? `, page ${pageNo}` : sheetNo != null ? `, sheet ${sheetNo}` : '';
  return (
    <Link className='font-medium text-coal hover:underline' to={docHref(docId, pageNo, sheetNo)}>
      {filename}{loc}
    </Link>
  );
}

function Sparkline({ points }) {
  if (points.length < 2) return <span className='font-mono text-[11px] text-stone-400'>single point</span>;
  const W = 120, H = 32;
  const vals = points.map((p) => p.value_mt);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = hi - lo || 1;
  const path = points.map((p, i) =>
    `${(i / (points.length - 1)) * W},${H - 3 - ((p.value_mt - lo) / span) * (H - 6)}`).join(' ');
  const up = vals[vals.length - 1] >= vals[0];
  return (
    <svg width={W} height={H} className='shrink-0'>
      <polyline points={path} fill='none' stroke={up ? '#059669' : '#dc2626'} strokeWidth='2' />
    </svg>
  );
}

function Profile({ name }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!name) return;
    let alive = true;
    setProfile(null);
    setError(null);
    getJSON(`/api/assets/profile?name=${encodeURIComponent(name)}`)
      .then((p) => alive && setProfile(p))
      .catch((e) => alive && setError(e.message));
    return () => { alive = false; };
  }, [name]);

  if (!name) return <p className='text-sm text-stone-500'>Select an asset to open its intelligence profile.</p>;
  if (error) return <ErrorBox message={error} />;
  if (!profile) return <Loading />;

  const lib = profile.library || {};
  const refGroups = profile.reference || {};
  const refCats = Object.entries(refGroups).filter(([, rows]) => (rows || []).length > 0);
  return (
    <div className='space-y-6'>
      <div className='rounded-xl border border-seam bg-white p-5 shadow-card'>
        <div className='flex flex-wrap items-center gap-2'>
          <h2 className='text-xl font-bold tracking-tight'>{profile.entity}</h2>
          <span className='rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 font-mono text-[10.5px] uppercase tracking-wide text-coal'>
            {profile.type}
          </span>
        </div>
        <p className='mt-2 text-[13px] text-stone-500'>
          {lib.documents ?? 0} documents · {lib.facts ?? 0} facts · {(lib.attributes || []).length} metrics · {(lib.periods || []).length} periods
          {profile.n_reference > 0 && <span> · {profile.n_reference} reference entries</span>}
        </p>
        {(lib.periods || []).length > 0 && (
          <p className='mt-1 font-mono text-[11px] text-stone-400'>
            {lib.periods[0].slice(0, 4)} – {lib.periods[lib.periods.length - 1].slice(0, 4)}
          </p>
        )}
      </div>

      {refCats.length > 0 && (
        <section>
          <h3 className='text-[15px] font-semibold tracking-tight'>Reference <span className='font-normal text-stone-400'>(public context, not evidence)</span></h3>
          <div className='mt-3 grid grid-cols-1 gap-3 md:grid-cols-2'>
            {refCats.map(([cat, rows]) => (
              <div key={cat} className='rounded-xl border border-seam bg-white p-4 shadow-card'>
                <p className='text-[12px] font-medium uppercase tracking-wide text-stone-500'>{cat}</p>
                <ul className='mt-2 space-y-2'>
                  {rows.map((r, i) => (
                    <li key={i} className='text-[13px]'>
                      <span className='font-medium'>{r.label}: </span>
                      <span>{r.value}{r.unit ? ` ${r.unit}` : ''}</span>
                      <span className='mt-0.5 block font-mono text-[11px] text-stone-400'>
                        {r.as_of ? `${r.as_of} · ` : ''}{r.source}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className='text-[15px] font-semibold tracking-tight'>Key Figures <span className='font-normal text-stone-400'>(latest reported period, median when several sources report)</span></h3>
        {!profile.key_figures.length && <p className='mt-2 text-sm text-stone-500'>No windowed metrics for this asset yet.</p>}
        <div className='mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3'>
          {profile.key_figures.map((f) => (
            <div key={f.attribute} className='rounded-xl border border-seam bg-white p-4 shadow-card'>
              <p className='text-[12px] font-medium uppercase tracking-wide text-stone-500'>{f.attribute.replace(/_/g, ' ')}</p>
              <p className='mt-1 font-mono text-[20px] font-semibold'>{f.value_mt} <span className='text-[12px] font-normal text-stone-500'>MT</span></p>
              <p className='mt-0.5 font-mono text-[11.5px] text-stone-500'>reported {f.value_raw} {f.unit || ''} · {f.period.slice(0, 7)}{f.n_sources > 1 ? ` · median of ${f.n_sources} sources` : ''}</p>
              <p className='mt-1.5 text-[12px]'><ReceiptLink docId={f.doc_id} filename={f.filename} pageNo={f.page_no} sheetNo={f.sheet_no} /></p>
            </div>
          ))}
        </div>
      </section>

      {!!profile.trends.length && (
        <section>
          <h3 className='text-[15px] font-semibold tracking-tight'>Trends <span className='font-normal text-stone-400'>(median of reported values, MT)</span></h3>
          <div className='mt-3 space-y-2'>
            {profile.trends.map((t) => (
              <div key={t.attribute} className='flex flex-wrap items-center gap-3 rounded-xl border border-seam bg-white px-4 py-3 shadow-card'>
                <div className='min-w-[140px] flex-1'>
                  <p className='text-[13.5px] font-semibold'>{t.attribute.replace(/_/g, ' ')}</p>
                  <p className='font-mono text-[11.5px] text-stone-500'>
                    {t.first} → {t.last} MT · {t.delta_pct != null ? `${t.delta_pct > 0 ? '+' : ''}${t.delta_pct}%` : 'n/a'} · {t.n_periods} periods
                  </p>
                </div>
                <Sparkline points={t.points} />
              </div>
            ))}
          </div>
        </section>
      )}

      {!!profile.documents.length && (
        <section>
          <h3 className='text-[15px] font-semibold tracking-tight'>Documents <span className='font-normal text-stone-400'>({profile.documents.length})</span></h3>
          <div className='mt-3 overflow-x-auto rounded-xl border border-seam bg-white shadow-card'>
            <table className='w-full min-w-[560px] text-sm'>
              <tbody>
                {profile.documents.map((d) => (
                  <tr key={d.doc_id} className='border-b border-seam last:border-0'>
                    <td className='px-4 py-2.5'>
                      <Link to={docHref(d.doc_id)} className={`font-medium hover:text-coal hover:underline ${d.is_current_version ? '' : 'text-stone-400 line-through'}`}>
                        {d.display_name || d.filename}
                      </Link>
                      <span className='ml-2 font-mono text-[11px] text-stone-400'>{d.doc_type}{d.subsidiary ? ` · ${d.subsidiary}` : ''}{d.doc_date_raw ? ` · ${d.doc_date_raw}` : ''}</span>
                    </td>
                    <td className='px-4 py-2.5 text-right font-mono text-[12px] text-stone-500'>{d.n_facts} facts</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {(profile.related.operators.length + profile.related.places.length + profile.related.geology.length) > 0 && (
        <section>
          <h3 className='text-[15px] font-semibold tracking-tight'>Related <span className='font-normal text-stone-400'>(share a document with this asset)</span></h3>
          <div className='mt-3 grid grid-cols-1 gap-3 md:grid-cols-3'>
            {[['operators', 'Operators'], ['places', 'Places'], ['geology', 'Geology']].map(([key, label]) => (
              <div key={key} className='rounded-xl border border-seam bg-white p-4 shadow-card'>
                <p className='text-[12px] font-medium uppercase tracking-wide text-stone-500'>{label}</p>
                {!profile.related[key].length && <p className='mt-1 text-[12.5px] text-stone-400'>None found.</p>}
                <ul className='mt-2 space-y-1.5'>
                  {profile.related[key].map((r) => (
                    <li key={r.id} className='text-[13px]'>
                      <Link to={`/assets?name=${encodeURIComponent(r.canonical_name)}`} className='font-medium hover:text-coal hover:underline'>
                        {r.canonical_name}
                      </Link>
                      <span className='ml-1.5 font-mono text-[11px] text-stone-400'>{r.shared_docs} docs</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {!!profile.conflicts.length && (
        <section>
          <div className='flex items-baseline justify-between'>
            <h3 className='text-[15px] font-semibold tracking-tight'>Conflicts <span className='font-normal text-stone-400'>({profile.conflicts.length})</span></h3>
            <Link to={`/conflicts?entity=${encodeURIComponent(profile.entity)}`} className='text-[12.5px] font-medium text-coal hover:underline'>Open in Conflict Radar</Link>
          </div>
          <div className='mt-3 space-y-2'>
            {profile.conflicts.map((c) => (
              <div key={c.key} className='rounded-xl border border-red-200 bg-red-50/60 px-4 py-3'>
                <p className='text-[13px] font-semibold'>{c.attribute.replace(/_/g, ' ')} · {c.period} <span className='font-mono font-normal text-red-700'>differs by {c.spread_pct}%</span></p>
                <div className='mt-1.5 space-y-1'>
                  {c.values.map((v, i) => (
                    <p key={i} className='text-[12.5px] text-stone-600'>
                      <span className='font-mono font-semibold text-stone-800'>{v.value_raw} {v.unit || ''}</span>
                      {' '}— <ReceiptLink docId={v.doc_id} filename={v.filename} pageNo={v.page_no} sheetNo={v.sheet_no} />
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {!!profile.evidence.length && (
        <section>
          <h3 className='text-[15px] font-semibold tracking-tight'>Evidence <span className='font-normal text-stone-400'>(recent facts, every value with its receipt)</span></h3>
          <div className='mt-3 overflow-x-auto rounded-xl border border-seam bg-white shadow-card'>
            <table className='w-full min-w-[640px] text-sm'>
              <thead>
                <tr className='border-b border-seam bg-paper text-left font-mono text-[11px] uppercase tracking-wide text-stone-500'>
                  <th className='px-4 py-2.5 font-medium'>Metric</th>
                  <th className='px-4 py-2.5 font-medium'>Period</th>
                  <th className='px-4 py-2.5 font-medium'>Reported</th>
                  <th className='px-4 py-2.5 font-medium'>Source</th>
                </tr>
              </thead>
              <tbody>
                {profile.evidence.map((f, i) => (
                  <tr key={i} className='border-b border-seam last:border-0'>
                    <td className='px-4 py-2'>{f.attribute.replace(/_/g, ' ')}</td>
                    <td className='px-4 py-2 font-mono text-[12px]'>{(f.period_norm || '').slice(0, 7)}</td>
                    <td className='px-4 py-2 font-mono text-[12.5px]'>
                      {f.value_raw} {f.unit || ''}
                      {!f.is_current_version && <span className='ml-1.5 rounded-full border border-seam px-1.5 py-px text-[10px] line-through'>superseded</span>}
                    </td>
                    <td className='px-4 py-2 text-[12.5px]'><ReceiptLink docId={f.doc_id} filename={f.display_name || f.filename} pageNo={f.page_no} sheetNo={f.sheet_no} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

export default function Assets() {
  const { data, error } = usePageData('/api/pages/assets');
  const [params, setParams] = useSearchParams();
  const [kind, setKind] = useState('');
  const [q, setQ] = useState('');
  const [list, setList] = useState(null);
  const selected = params.get('name') || '';

  useEffect(() => {
    const qs = new URLSearchParams();
    if (kind) qs.set('kind', kind);
    if (q.trim()) qs.set('q', q.trim());
    getJSON(`/api/assets?${qs.toString()}`).then((r) => setList(r.assets)).catch(() => setList([]));
  }, [kind, q]);

  if (error) return <ErrorBox message={error} />;
  if (!data || !list) return <Loading />;

  const shown = selected || (list[0] ? list[0].canonical_name : '');

  return (
    <div>
      <PageHeader
        title='Assets'
        subtitle='Every mine, coalfield and project with a unified intelligence profile — key figures, trends, documents, related entities, conflicts and evidence with receipts.'
      />
      <Rise delay={0.05}>
        <div className='mt-6 flex flex-wrap items-end gap-3'>
          <label className='w-full min-w-0 flex-1 sm:min-w-[160px] sm:max-w-[200px]'>
            <span className='text-[12px] font-medium text-stone-500'>Kind</span>
            <select value={kind} onChange={(e) => setKind(e.target.value)}
                    className='mt-1 w-full rounded-lg border border-seamdark bg-white px-3 py-2 text-sm focus:border-coal focus:outline-none'>
              <option value=''>Mines + regions</option>
              <option value='mine'>Mines</option>
              <option value='region'>Regions</option>
            </select>
          </label>
          <label className='w-full min-w-0 flex-1 sm:min-w-[200px]'>
            <span className='text-[12px] font-medium text-stone-500'>Search</span>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder='Filter by name…'
                   className='mt-1 w-full rounded-lg border border-seamdark bg-white px-3 py-2 text-sm focus:border-coal focus:outline-none' />
          </label>
        </div>
      </Rise>

      {!list.length && (
        <p className='mt-6 rounded-xl border border-dashed border-seamdark bg-white p-6 text-center text-sm text-stone-500'>
          No mine or region entities found yet. Ingest reports mentioning mines, coalfields or projects and they will appear here.
        </p>
      )}

      {!!list.length && (
        <div className='mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[280px_minmax(0,1fr)]'>
          <nav className='h-fit rounded-xl border border-seam bg-white p-2 shadow-card lg:sticky lg:top-4 lg:max-h-[70vh] lg:overflow-y-auto'>
            {list.map((a) => (
              <button key={a.id} onClick={() => setParams({ name: a.canonical_name })}
                      className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] transition-colors ${shown === a.canonical_name ? 'bg-coal/10 font-semibold text-coal' : 'hover:bg-paper'}`}>
                <Pickaxe className='h-4 w-4 shrink-0 opacity-60' />
                <span className='min-w-0 flex-1 truncate'>{a.canonical_name}</span>
                <span className='font-mono text-[11px] text-stone-400'>{a.n_facts}</span>
              </button>
            ))}
          </nav>
          <div className='min-w-0'>
            <Profile key={shown} name={shown} />
          </div>
        </div>
      )}
    </div>
  );
}
