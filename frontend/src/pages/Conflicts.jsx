import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ChevronDown } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { getJSON, postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { AnimatedBackground } from '../components/motion/animated-background.jsx';
import { Disclosure, DisclosureTrigger, DisclosureContent } from '../components/motion/disclosure.jsx';

const STATUSES = ['open', 'acknowledged', 'resolved'];

function ConflictCard({ c, onStatus }) {
  const [busy, setBusy] = useState(false);
  const statusColor = c.status === 'resolved' ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : c.status === 'acknowledged' ? 'border-coalline bg-coalsoft text-coal'
    : 'border-red-200 bg-red-50 text-red-700';
  const setStatus = async (status) => {
    setBusy(true);
    try {
      await postJSON('/api/conflicts/status', { key: c.key, status });
      onStatus();
    } catch { setBusy(false); }
  };
  return (
    <article className='rounded-xl border border-seam bg-white p-5 shadow-card'>
      <div className='flex flex-wrap items-center justify-between gap-2'>
        <span className='font-mono text-[11px] uppercase tracking-widest text-stone-400'>conflict #{c.key.slice(0, 8)}</span>
        <span className={`rounded-full border px-2.5 py-0.5 font-mono text-[10.5px] uppercase ${statusColor}`}>{c.status}</span>
      </div>
      <div className='mt-3 grid gap-x-8 gap-y-1 text-[13.5px] sm:grid-cols-2'>
        <div className='flex justify-between gap-3 min-w-0 sm:block'><span className='text-stone-400'>Entity</span><span className='font-semibold sm:ml-2'>{c.entity}</span></div>
        <div className='flex justify-between gap-3 min-w-0 sm:block'><span className='text-stone-400'>Metric</span><span className='font-semibold sm:ml-2'>{String(c.attribute).replace('_', ' ')}</span></div>
        <div className='flex justify-between gap-3 min-w-0 sm:block'><span className='text-stone-400'>Period</span><span className='font-mono sm:ml-2'>{c.period || 'period n/a'}</span></div>
        <div className='flex justify-between gap-3 min-w-0 sm:block'><span className='text-stone-400'>Differ by</span><span className='font-mono sm:ml-2 text-red-700'>{c.spread_pct}%</span></div>
      </div>
      <div className='mt-4 space-y-1.5'>
        {c.values.map((v, i) => (
          <div key={i} className='flex flex-wrap items-center justify-between gap-2 rounded-lg border border-seam bg-paper px-3 py-2'>
            <span className='font-mono text-[15px] font-semibold'>{v.value_raw} {v.unit || ''}</span>
            <span className='flex flex-wrap items-center gap-2 text-[11.5px] text-stone-500'>
              {!v.is_current_version && <span className='rounded-full border border-seam bg-white px-2 py-0.5 line-through'>superseded</span>}
              {v.ocr && <span className='rounded-full border border-coalline bg-coalsoft px-2 py-0.5 text-coal'>OCR</span>}
              {v.low_conf && <span className='rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-red-700'>low confidence</span>}
              <Link className='font-medium text-coal hover:underline'
                    to={`/doc/${v.doc_id}${v.page_no ? `/?page=${v.page_no}` : v.sheet_no != null ? `?sheet=${v.sheet_no}` : ''}`}>
                {v.filename}{v.page_no ? `, page ${v.page_no}` : v.sheet_no != null ? `, sheet ${v.sheet_no}` : ''}
              </Link>
            </span>
          </div>
        ))}
      </div>
      <Disclosure className='mt-4 rounded-lg border border-coalline bg-coalsoft/60 px-3 py-2.5 text-[12.5px]'>
        <DisclosureTrigger className='w-full text-left'>
          <span><strong className='text-coal'>Why flagged:</strong> values differ by {c.spread_pct}% on the same key.</span>
          <ChevronDown className='h-4 w-4 shrink-0 text-coal' />
        </DisclosureTrigger>
        <DisclosureContent>
          <p className='mt-1'><strong className='text-coal'>Potential causes:</strong></p>
          <ul className='mt-0.5 list-disc space-y-0.5 pl-5 text-stone-600'>
            {c.causes.map((x, i) => <li key={i}>{x}</li>)}
          </ul>
        </DisclosureContent>
      </Disclosure>
      <AnimatedBackground defaultValue={c.status} onValueChange={(s) => s && s !== c.status && setStatus(s)}
        className='mt-4 flex flex-wrap items-center gap-1 rounded-lg border border-seam bg-paper p-1'>
        {STATUSES.map((s) => (
          <button key={s} data-id={s} disabled={busy}
                  className={`rounded-md px-3 py-1.5 text-[12.5px] font-semibold capitalize transition-colors ${c.status === s ? 'text-coal' : 'text-stone-500 hover:text-coal'}`}>
            {s === 'open' ? 'Reopen' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </AnimatedBackground>
    </article>
  );
}

export default function Conflicts() {
  const params = Object.fromEntries(new URLSearchParams(window.location.search));
  const { data: filters, error } = usePageData('/api/pages/conflicts-filters');
  const [list, setList] = useState(null);

  const load = useCallback(async () => {
    const q = new URLSearchParams();
    if (params.entity) q.set('entity', params.entity);
    if (params.attribute) q.set('attribute', params.attribute);
    setList(await getJSON('/api/conflicts?' + q));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.entity, params.attribute]);

  useEffect(() => { load(); }, [load]);

  const setFilter = (key) => (e) => {
    const next = new URLSearchParams(window.location.search);
    if (e.target.value) next.set(key, e.target.value); else next.delete(key);
    window.location.search = next.toString();
  };

  if (error) return <ErrorBox message={error} />;
  if (!filters) return <Loading />;

  return (
    <div>
      <PageHeader
        title='Conflict Radar'
        subtitle='Values that disagree on the same entity, metric and period. Nothing is resolved silently: every reported value keeps its receipt, the likely causes are explained, and you decide the status.'>
        <div className='flex flex-wrap items-center gap-2'>
          <select value={params.entity || ''} onChange={setFilter('entity')}
                  className='rounded-lg border border-seamdark bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none'>
            <option value=''>All entities</option>
            {filters.entities.map((e) => <option key={e.n} value={e.n}>{e.n}</option>)}
          </select>
          <select value={params.attribute || ''} onChange={setFilter('attribute')}
                  className='rounded-lg border border-seamdark bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none'>
            <option value=''>All metrics</option>
            {filters.attributes.map((a) => <option key={a.attribute} value={a.attribute}>{a.attribute.replace('_', ' ')}</option>)}
          </select>
        </div>
      </PageHeader>

      <Rise delay={0.05}>
        <div className='mt-6'>
          {list === null ? (
            <Loading />
          ) : list.length === 0 ? (
            <div className='flex flex-col items-center rounded-2xl border border-dashed border-seamdark bg-white px-6 py-14 text-center'>
              <span className='flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700'>
                <ShieldCheck className='h-6 w-6' />
              </span>
              <p className='mt-3 text-sm font-semibold'>No conflicts detected{params.entity ? ' for this filter' : ''}</p>
              <p className='mt-1 text-[13px] text-stone-500'>All reported values agree, or nothing has been extracted yet.</p>
            </div>
          ) : (
            <AnimatedGroup preset='blur-slide' className='space-y-4'>
              {list.map((c) => <ConflictCard key={c.key} c={c} onStatus={load} />)}
            </AnimatedGroup>
          )}
        </div>
      </Rise>
    </div>
  );
}
