import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Pickaxe } from 'lucide-react';
import { getJSON } from '../api.js';
import { usePageData } from '../hooks/useData.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, EmptyState, Table, TableHead, TableHeader, TableBody, TableRow, TableCell } from '../components/ui.jsx';

function docHref(docId, pageNo, sheetNo) {
  if (pageNo) return `/doc/${docId}?page=${pageNo}`;
  if (sheetNo != null) return `/doc/${docId}?sheet=${sheetNo}`;
  return `/doc/${docId}`;
}

function ReceiptLink({ docId, filename, pageNo, sheetNo }) {
  if (!docId) return <span className='text-muted1'>no source</span>;
  const loc = pageNo ? `, page ${pageNo}` : sheetNo != null ? `, sheet ${sheetNo}` : '';
  return (
    <Link className='font-medium text-coal hover:underline' to={docHref(docId, pageNo, sheetNo)}>
      {filename}{loc}
    </Link>
  );
}

function Sparkline({ points }) {
  if (points.length < 2) return <span className='font-mono text-[11px] text-muted1'>single point</span>;
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

  if (!name) return <p className='text-xs text-muted1'>Select an asset to open its intelligence profile.</p>;
  if (error) return <ErrorBox message={error} />;
  if (!profile) return <Loading />;

  const lib = profile.library || {};
  const refGroups = profile.reference || {};
  const refCats = Object.entries(refGroups).filter(([, rows]) => (rows || []).length > 0);
  return (
    <div className='space-y-6'>
      <Card className='p-5'>
        <div className='flex flex-wrap items-center gap-2'>
          <h2 className='text-lg font-bold tracking-tight text-ink'>{profile.entity}</h2>
          <Badge variant='coal' className='text-[10.5px] uppercase'>
            {profile.type}
          </Badge>
        </div>
        <p className='mt-2 font-mono text-xs text-muted1 tabular-nums'>
          {lib.documents ?? 0} documents · {lib.facts ?? 0} facts · {(lib.attributes || []).length} metrics · {(lib.periods || []).length} periods
          {profile.n_reference > 0 && <span> · {profile.n_reference} reference entries</span>}
        </p>
        {(lib.periods || []).length > 0 && (
          <p className='mt-1 font-mono text-[11px] text-muted1 tabular-nums'>
            {lib.periods[0].slice(0, 4)} – {lib.periods[lib.periods.length - 1].slice(0, 4)}
          </p>
        )}
      </Card>

      {refCats.length > 0 && (
        <section>
          <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Reference <span className='font-normal text-muted2'>(public context, not evidence)</span></h3>
          <div className='mt-3 grid grid-cols-1 gap-3 md:grid-cols-2'>
            {refCats.map(([cat, rows]) => (
              <Card key={cat} className='p-4'>
                <p className='text-xs font-medium uppercase tracking-wider text-muted1'>{cat}</p>
                <ul className='mt-2 space-y-2'>
                  {rows.map((r, i) => (
                    <li key={i} className='text-xs text-ink'>
                      <span className='font-medium'>{r.label}: </span>
                      <span className='font-mono tabular-nums'>{r.value}{r.unit ? ` ${r.unit}` : ''}</span>
                      <span className='mt-0.5 block font-mono text-[11px] text-muted1'>
                        {r.as_of ? `${r.as_of} · ` : ''}{r.source}
                      </span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Key Figures <span className='font-normal text-muted2'>(latest reported period, median when several sources report)</span></h3>
        {!profile.key_figures.length && <p className='mt-2 text-xs text-muted1'>No windowed metrics for this asset yet.</p>}
        <div className='mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3'>
          {profile.key_figures.map((f) => (
            <Card key={f.attribute} className='p-4'>
              <p className='text-xs font-medium uppercase tracking-wider text-muted1'>{f.attribute.replace(/_/g, ' ')}</p>
              <p className='mt-1 font-mono text-xl font-semibold tabular-nums text-ink'>{f.value_mt} <span className='text-xs font-normal text-muted1'>MT</span></p>
              <p className='mt-0.5 font-mono text-xs text-muted1 tabular-nums'>reported {f.value_raw} {f.unit || ''} · {f.period.slice(0, 7)}{f.n_sources > 1 ? ` · median of ${f.n_sources} sources` : ''}</p>
              <p className='mt-2 text-xs'><ReceiptLink docId={f.doc_id} filename={f.filename} pageNo={f.page_no} sheetNo={f.sheet_no} /></p>
            </Card>
          ))}
        </div>
      </section>

      {!!profile.trends.length && (
        <section>
          <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Trends <span className='font-normal text-muted2'>(median of reported values, MT)</span></h3>
          <div className='mt-3 space-y-2'>
            {profile.trends.map((t) => (
              <Card key={t.attribute} className='flex flex-wrap items-center gap-3 p-4'>
                <div className='min-w-[140px] flex-1'>
                  <p className='text-xs font-semibold text-ink'>{t.attribute.replace(/_/g, ' ')}</p>
                  <p className='mt-0.5 font-mono text-xs text-muted1 tabular-nums'>
                    {t.first} → {t.last} MT · {t.delta_pct != null ? `${t.delta_pct > 0 ? '+' : ''}${t.delta_pct}%` : 'n/a'} · {t.n_periods} periods
                  </p>
                </div>
                <Sparkline points={t.points} />
              </Card>
            ))}
          </div>
        </section>
      )}

      {!!profile.documents.length && (
        <section>
          <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Documents <span className='font-normal text-muted2'>({profile.documents.length})</span></h3>
          <Table className='mt-3'>
            <TableBody>
              {profile.documents.map((d) => (
                <TableRow key={d.doc_id}>
                  <TableCell className='py-2.5'>
                    <Link to={docHref(d.doc_id)} className={`font-medium hover:text-coal hover:underline ${d.is_current_version ? 'text-ink' : 'text-muted2 line-through'}`}>
                      {d.display_name || d.filename}
                    </Link>
                    <span className='ml-2 font-mono text-[11px] text-muted1'>{d.doc_type}{d.subsidiary ? ` · ${d.subsidiary}` : ''}{d.doc_date_raw ? ` · ${d.doc_date_raw}` : ''}</span>
                  </TableCell>
                  <TableCell numeric className='py-2.5 text-xs text-muted1'>{d.n_facts} facts</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
      )}

      {(profile.related.operators.length + profile.related.places.length + profile.related.geology.length) > 0 && (
        <section>
          <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Related <span className='font-normal text-muted2'>(share a document with this asset)</span></h3>
          <div className='mt-3 grid grid-cols-1 gap-3 md:grid-cols-3'>
            {[['operators', 'Operators'], ['places', 'Places'], ['geology', 'Geology']].map(([key, label]) => (
              <Card key={key} className='p-4'>
                <p className='text-xs font-medium uppercase tracking-wider text-muted1'>{label}</p>
                {!profile.related[key].length && <p className='mt-1 text-xs text-muted2'>None found.</p>}
                <ul className='mt-2 space-y-1.5'>
                  {profile.related[key].map((r) => (
                    <li key={r.id} className='text-xs text-ink'>
                      <Link to={`/assets?name=${encodeURIComponent(r.canonical_name)}`} className='font-medium hover:text-coal hover:underline'>
                        {r.canonical_name}
                      </Link>
                      <span className='ml-1.5 font-mono text-[11px] text-muted1 tabular-nums'>{r.shared_docs} docs</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        </section>
      )}

      {!!profile.conflicts.length && (
        <section>
          <div className='flex items-baseline justify-between'>
            <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Conflicts <span className='font-normal text-muted2'>({profile.conflicts.length})</span></h3>
            <Link to={`/conflicts?entity=${encodeURIComponent(profile.entity)}`} className='text-xs font-semibold text-coal hover:underline'>Open in Conflict Radar</Link>
          </div>
          <div className='mt-3 space-y-2'>
            {profile.conflicts.map((c) => (
              <Card key={c.key} className='border-bad/30 bg-bad/5 p-4'>
                <p className='text-xs font-semibold text-ink'>{c.attribute.replace(/_/g, ' ')} · {c.period} <span className='font-mono font-semibold tabular-nums text-bad'>differs by {c.spread_pct}%</span></p>
                <div className='mt-2 space-y-1'>
                  {c.values.map((v, i) => (
                    <p key={i} className='text-xs text-muted0'>
                      <span className='font-mono font-semibold tabular-nums text-ink'>{v.value_raw} {v.unit || ''}</span>
                      {' '}— <ReceiptLink docId={v.doc_id} filename={v.filename} pageNo={v.page_no} sheetNo={v.sheet_no} />
                    </p>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {!!profile.evidence.length && (
        <section>
          <h3 className='text-xs font-semibold uppercase tracking-wider text-muted1'>Evidence <span className='font-normal text-muted2'>(recent facts, every value with its receipt)</span></h3>
          <Table className='mt-3'>
            <TableHead>
              <tr>
                <TableHeader>Metric</TableHeader>
                <TableHeader>Period</TableHeader>
                <TableHeader>Reported</TableHeader>
                <TableHeader>Source</TableHeader>
              </tr>
            </TableHead>
            <TableBody>
              {profile.evidence.map((f, i) => (
                <TableRow key={i}>
                  <TableCell className='py-2.5'>{f.attribute.replace(/_/g, ' ')}</TableCell>
                  <TableCell mono className='py-2.5 text-xs text-muted1 tabular-nums'>{(f.period_norm || '').slice(0, 7)}</TableCell>
                  <TableCell mono className='py-2.5 text-xs font-semibold text-ink tabular-nums'>
                    {f.value_raw} {f.unit || ''}
                    {!f.is_current_version && <Badge variant='neutral' className='ml-2 text-[10px] line-through'>superseded</Badge>}
                  </TableCell>
                  <TableCell className='py-2.5 text-xs'><ReceiptLink docId={f.doc_id} filename={f.display_name || f.filename} pageNo={f.page_no} sheetNo={f.sheet_no} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
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
            <span className='text-xs font-medium text-muted1'>Kind</span>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className='mt-1 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink focus:border-coal focus:outline-none'
            >
              <option value=''>Mines + regions</option>
              <option value='mine'>Mines</option>
              <option value='region'>Regions</option>
            </select>
          </label>
          <label className='w-full min-w-0 flex-1 sm:min-w-[200px]'>
            <span className='text-xs font-medium text-muted1'>Search</span>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder='Filter by name…'
              className='mt-1 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink placeholder:text-muted2 focus:border-coal focus:outline-none'
            />
          </label>
        </div>
      </Rise>

      {!list.length && (
        <EmptyState
          icon={Pickaxe}
          title='No mine or region entities found yet'
          description='Ingest reports mentioning mines, coalfields or projects and they will appear here.'
          className='mt-6'
        />
      )}

      {!!list.length && (
        <div className='mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[280px_minmax(0,1fr)]'>
          <nav className='h-fit rounded-xl border border-seam bg-surface p-2 shadow-card lg:sticky lg:top-4 lg:max-h-[70vh] lg:overflow-y-auto space-y-0.5'>
            {list.map((a) => (
              <button
                key={a.id}
                onClick={() => setParams({ name: a.canonical_name })}
                className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-colors ${
                  shown === a.canonical_name
                    ? 'bg-coal/10 font-semibold text-coal ring-1 ring-coal/20 shadow-xs'
                    : 'text-ink hover:bg-paper'
                }`}
              >
                <Pickaxe className='h-4 w-4 shrink-0 opacity-60' />
                <span className='min-w-0 flex-1 truncate'>{a.canonical_name}</span>
                <span className='font-mono text-[11px] text-muted1 tabular-nums'>{a.n_facts}</span>
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
