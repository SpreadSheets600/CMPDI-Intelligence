import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePageData } from '../hooks/useData.js';
import { getJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button } from '../components/ui.jsx';
import { Accordion, AccordionAnimatedItem } from '../components/motion/accordion.jsx';
import { TransitionPanel } from '../components/motion/transition-panel.jsx';
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

  const selectCls = 'mt-1 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink focus:border-coal focus:outline-none transition-colors';
  const changeRow = (c) => (
    <div key={keyLine(c)} className='flex flex-wrap items-center justify-between gap-2 rounded-xl border border-seam bg-paper/50 px-3.5 py-2.5 text-xs'>
      <span className='text-ink'>{keyLine(c)}</span>
      <div className='flex items-center gap-2 font-mono tabular-nums text-xs'>
        <span className='text-muted1'>{fmt(c.old)}</span>
        <span className='text-muted2'>→</span>
        <strong className='text-ink font-semibold'>{fmt(c.new)}</strong>
        <Badge variant={c.delta_pct > 0 ? 'ok' : 'bad'} className='ml-1 text-[10px]'>
          {c.delta_pct > 0 ? '+' : ''}{c.delta_pct}%
        </Badge>
      </div>
    </div>
  );
  const listRow = (row, label) => (
    <div key={keyLine(row.k || row)} className='flex flex-wrap items-center justify-between gap-2 rounded-xl border border-seam bg-paper/50 px-3.5 py-2.5 text-xs'>
      <span className='text-ink'>{keyLine(row.k || row)}</span>
      <span className='font-mono tabular-nums text-muted1'>{label} <strong className='text-ink font-semibold'>{fmt(row.v ?? row.new ?? row.old)}</strong></span>
    </div>
  );
  const sectionRow = (s) => (
    <div key={s.path} className='rounded-xl border border-seam bg-paper/50 px-3.5 py-2.5 text-xs'>
      <p className='font-mono text-[11px] text-muted1'>{s.path}</p>
      <p className='mt-0.5 line-clamp-2 text-ink'>{s.excerpt}</p>
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
        <Card className='mt-6 p-4'>
          <div className='flex flex-wrap items-end gap-3'>
            <label className='w-full min-w-0 flex-1 sm:min-w-[220px]'>
              <span className='text-xs font-medium text-muted1'>Document A</span>
              <select value={docA} onChange={(e) => setDocA(e.target.value)} className={selectCls}>
                <option value=''>Choose...</option>
                {docOptions}
              </select>
            </label>
            {data.suggested && (
              <div className='pb-2 text-xs text-muted1'>
                previous revision:{' '}
                <button type='button' onClick={() => setDocB(data.suggested.id)} className='font-medium text-coal hover:underline'>
                  {data.suggested.display_name || data.suggested.filename}
                </button>
              </div>
            )}
          </div>
          <div className='mt-3 flex flex-wrap items-end gap-3'>
            <label className='w-full min-w-0 flex-1 sm:min-w-[220px]'>
              <span className='text-xs font-medium text-muted1'>Document B</span>
              <select value={docB} onChange={(e) => setDocB(e.target.value)} className={selectCls}>
                <option value=''>Choose...</option>
                {docOptions}
              </select>
            </label>
            <Button
              type='button'
              variant='primary'
              size='md'
              onClick={run}
              disabled={busy}
              className='px-6'
            >
              Compare
            </Button>
          </div>
        </Card>
      </Rise>

      <div className='mt-6'>
        <TransitionPanel activeIndex={panelIndex}>
          <div>{err && <p className='text-xs font-medium text-bad'>{err}</p>}</div>
          <div>
            <Card className='p-8 text-center'>
              <TextShimmer as='p' duration={1.6} className='text-xs text-muted1'>Comparing documents…</TextShimmer>
            </Card>
          </div>
          <div>
            {result && !result.error && (
              <div>
                <div className='grid gap-3 sm:grid-cols-2'>
                  {['a', 'b'].map((k) => (
                    <Card key={k} className={`p-4 ${k === 'b' ? 'border-coalline bg-coalsoft/40' : ''}`}>
                      <p className='font-mono text-[10px] uppercase tracking-wider text-muted1'>document {k}</p>
                      <p className='mt-1 font-semibold text-ink text-sm'>{result[k].name || result[k].filename}</p>
                      <p className='mt-0.5 font-mono text-xs text-muted1 tabular-nums'>{result[k].date || 'period n/a'} · {result[k].facts} facts · {result[k].sections} sections</p>
                    </Card>
                  ))}
                </div>
                <div className='mt-4 flex flex-wrap gap-2'>
                  {[['changed facts', result.summary.changed], ['facts only in A', result.summary.removed], ['facts only in B', result.summary.added], ['new sections', result.summary.new_sections], ['removed sections', result.summary.removed_sections]].map(([l, n]) => (
                    <Badge key={l} variant='neutral' className='font-mono tabular-nums text-xs py-1 px-3'>
                      {l}: <strong className='text-ink font-semibold'>{n}</strong>
                    </Badge>
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
                  <Card className='mt-8 p-10 text-center text-sm text-muted1'>
                    No numerical or structural changes detected between these documents.
                  </Card>
                )}
              </div>
            )}
          </div>
        </TransitionPanel>
      </div>
    </div>
  );
}
