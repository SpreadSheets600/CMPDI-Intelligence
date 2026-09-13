import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePageData } from '../hooks/useData.js';
import { getJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { Accordion, AccordionAnimatedItem } from '../components/motion/accordion.jsx';
import { TransitionPanel } from '../components/motion/transition-panel.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';
import { TextShimmer } from '../components/motion/text-shimmer.jsx';

const fmt = (v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
const keyLine = (k) => `${k.entity} · ${String(k.attribute).replace('_', ' ')} · ${k.period || 'period n/a'}`;

export default function Compare() {
  const [params] = useSearchParams();
  const { data, error } = usePageData(`/api/pages/compare${params.get('doc') ? `?doc=${params.get('doc')}` : ''}`);
  const [docA, setDocA] = useState(params.get('doc') || '');
  const [docB, setDocB] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const run = async () => {
    setErr('');
    if (!docA || !docB || docA === docB) { setErr('Pick two different documents.'); setResult(null); return; }
    setBusy(true);
    try {
      setResult(await getJSON(`/api/compare?a=${docA}&b=${docB}`));
    } catch (e) {
      setErr(e.message); setResult(null);
    }
    setBusy(false);
  };

  const selectCls = 'mt-1 w-full rounded-lg border border-seamdark bg-white px-3 py-2 text-sm focus:border-coal focus:outline-none';
  const changeRow = (c) => (
    <div key={keyLine(c)} className='flex flex-wrap items-center justify-between gap-2 rounded-lg border border-seam bg-paper px-3 py-2 text-[13px]'>
      <span>{keyLine(c)}</span>
      <span className='font-mono'>{fmt(c.old)} → <strong>{fmt(c.new)}</strong>
        <span className={c.delta_pct > 0 ? 'text-emerald-700' : 'text-red-700'}> ({c.delta_pct > 0 ? '+' : ''}{c.delta_pct}%)</span>
      </span>
    </div>
  );
  const listRow = (row, label) => (
    <div key={keyLine(row.k || row)} className='flex flex-wrap items-center justify-between gap-2 rounded-lg border border-seam bg-paper px-3 py-2 text-[13px]'>
      <span>{keyLine(row.k || row)}</span>
      <span className='font-mono text-stone-500'>{label} {fmt(row.v ?? row.new ?? row.old)}</span>
    </div>
  );
  const sectionRow = (s) => (
    <div key={s.path} className='rounded-lg border border-seam bg-paper px-3 py-2 text-[13px]'>
      <p className='font-mono text-[11px] text-stone-400'>{s.path}</p>
      <p className='mt-0.5 line-clamp-2 text-stone-600'>{s.excerpt}</p>
    </div>
  );

  const docOptions = data.docs.map((d) => (
    <option key={d.id} value={d.id}>{d.display_name || d.filename}{d.doc_date_raw ? ` · ${d.doc_date_raw}` : ''}</option>
  ));

  // 0 = idle/error, 1 = comparing, 2 = result
  const panelIndex = busy ? 1 : result && !result.error ? 2 : 0;

  const sections = result && !result.error ? [
    result.fact_changes.length > 0 && { title: `Changed Numerical Facts (${result.fact_changes.length})`, body: <div className='space-y-1.5'>{result.fact_changes.map(changeRow)}</div> },
    result.added_facts.length > 0 && { title: `Facts Only in Document B (${result.added_facts.length})`, body: <div className='space-y-1.5'>{result.added_facts.map((f) => listRow(f, 'new'))}</div> },
    result.removed_facts.length > 0 && { title: `Facts Only in Document A (${result.removed_facts.length})`, body: <div className='space-y-1.5'>{result.removed_facts.map((f) => listRow(f, 'old'))}</div> },
    result.new_sections.length > 0 && { title: `New Sections (${result.new_sections.length})`, body: <div className='space-y-1.5'>{result.new_sections.map(sectionRow)}</div> },
    result.removed_sections.length > 0 && { title: `Removed Sections (${result.removed_sections.length})`, body: <div className='space-y-1.5'>{result.removed_sections.map(sectionRow)}</div> },
  ].filter(Boolean) : [];

  return (
    <div>
      <PageHeader
        title='Compare Documents'
        subtitle='Pick any two documents and see exactly what changed: every numerical fact that moved, and sections added or removed. Version chains suggest the natural pair.'
      />

      <Rise delay={0.05}>
        <div className='mt-6 rounded-xl border border-seam bg-white p-4 shadow-card'>
          <div className='flex flex-wrap items-end gap-3'>
            <label className='w-full min-w-0 flex-1 sm:min-w-[220px]'>
              <span className='text-[12px] font-medium text-stone-500'>Document A</span>
              <select value={docA} onChange={(e) => setDocA(e.target.value)} className={selectCls}>
                <option value=''>Choose...</option>
                {docOptions}
              </select>
            </label>
            {data.suggested && (
              <div className='pb-2 text-[13px] text-stone-500'>
                previous revision:{' '}
                <button type='button' onClick={() => setDocB(data.suggested.id)} className='font-medium text-coal hover:underline'>
                  {data.suggested.display_name || data.suggested.filename}
                </button>
              </div>
            )}
          </div>
          <div className='mt-3 flex flex-wrap items-end gap-3'>
            <label className='w-full min-w-0 flex-1 sm:min-w-[220px]'>
              <span className='text-[12px] font-medium text-stone-500'>Document B</span>
              <select value={docB} onChange={(e) => setDocB(e.target.value)} className={selectCls}>
                <option value=''>Choose...</option>
                {docOptions}
              </select>
            </label>
            <Magnetic intensity={0.25} range={90}>
              <button type='button' onClick={run} disabled={busy}
                      className='rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-colors hover:bg-amber-500 disabled:opacity-50'>
                Compare
              </button>
            </Magnetic>
          </div>
        </div>
      </Rise>

      <div className='mt-6'>
        <TransitionPanel activeIndex={panelIndex}>
          <div>{err && <p className='text-[13.5px] text-red-700'>{err}</p>}</div>
          <div><TextShimmer as='p' duration={1.6} className='text-[13.5px]'>Comparing documents…</TextShimmer></div>
          <div>
            {result && !result.error && (
              <div>
                <div className='grid gap-3 sm:grid-cols-2'>
                  {['a', 'b'].map((k) => (
                    <div key={k} className={`rounded-xl border ${k === 'b' ? 'border-coalline bg-coalsoft/50' : 'border-seam'} bg-white p-4 shadow-card`}>
                      <p className='font-mono text-[10px] uppercase tracking-widest text-stone-400'>document {k}</p>
                      <p className='mt-1 font-semibold'>{result[k].name || result[k].filename}</p>
                      <p className='mt-0.5 text-[12.5px] text-stone-500'>{result[k].date || 'period n/a'} · {result[k].facts} facts · {result[k].sections} sections</p>
                    </div>
                  ))}
                </div>
                <div className='mt-4 flex flex-wrap gap-2'>
                  {[['changed facts', result.summary.changed], ['facts only in A', result.summary.removed], ['facts only in B', result.summary.added], ['new sections', result.summary.new_sections], ['removed sections', result.summary.removed_sections]].map(([l, n]) => (
                    <span key={l} className='rounded-full border border-seam bg-white px-3 py-1 font-mono text-[11.5px] text-stone-600'>{l}: <strong>{n}</strong></span>
                  ))}
                </div>
                {sections.length > 0 ? (
                  <Accordion className='mt-6 space-y-3'>
                    {sections.map((s) => (
                      <AccordionAnimatedItem key={s.title} value={s.title} title={s.title}>
                        {s.body}
                      </AccordionAnimatedItem>
                    ))}
                  </Accordion>
                ) : (
                  <p className='mt-8 rounded-xl border border-seam bg-white px-6 py-10 text-center text-sm text-stone-500'>No numerical or structural changes detected between these documents.</p>
                )}
              </div>
            )}
          </div>
        </TransitionPanel>
      </div>
    </div>
  );
}
