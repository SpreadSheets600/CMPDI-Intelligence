import { useRef, useState } from 'react';
import { Upload, Package, Info, File as FileIcon, TriangleAlert as Alert, LoaderCircle } from 'lucide-react';
import { usePageData, usePolling } from '../hooks/useData.js';
import { uploadFiles } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { AnimatedNumber } from '../components/motion/animated-number.jsx';

const STAGES = ['uploaded', 'classifying', 'extracting', 'ocr', 'normalizing',
  'chunking', 'embedding', 'indexing', 'summarizing', 'completed'];

function JobStrip() {
  const jobs = usePolling('/api/jobs', 2500);
  const [open, setOpen] = useState({});
  if (!jobs) return <div className='mt-4 space-y-3' aria-live='polite' />;
  return (
    <AnimatedGroup preset='blur-slide' className='mt-4 space-y-3' aria-live='polite'>
      {jobs.map((j, i) => {
        const failed = j.status === 'failed';
        const running = j.status === 'running';
        const idx = STAGES.indexOf(j.stage);
        let stats = {};
        try { stats = JSON.parse(j.stats_json || '{}'); } catch { stats = {}; }
        const pageTexts = stats.page_texts || {};
        const pageSums = stats.page_summaries || {};
        const pageNos = Array.from(new Set([...Object.keys(pageTexts), ...Object.keys(pageSums)]))
          .sort((a, b) => Number(a) - Number(b));
        const isOpen = !!open[j.id];
        return (
          <div key={j.id || i}
            className={`relative overflow-hidden rounded-xl border p-4 shadow-card ${failed ? 'border-red-200 bg-red-50/60' : 'border-seam bg-white'}`}>
            <div className='flex items-baseline justify-between gap-4 overflow-hidden'>
              <span className='min-w-0 truncate text-sm font-semibold'>{j.filename || 'unknown file'}</span>
              <span className={`flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide ${failed ? 'text-red-700' : j.status === 'completed' ? 'text-emerald-700' : 'text-coal'}`}>
                {failed ? <Alert className='h-3.5 w-3.5' /> : running
                  ? <LoaderCircle2 /> : <CircleCheck />}
                {failed ? 'failed' : j.stage}
                {stats.pages_done && stats.pages_total ? ` · pages ${stats.pages_done}/${stats.pages_total}` : ''}
              </span>
            </div>
            <div className='mt-2 flex flex-wrap items-center gap-1 text-[10px] font-mono uppercase tracking-wide'>
              {STAGES.map((s, si) => {
                const mine = STAGES.indexOf(s);
                const cls = failed && s === j.stage
                  ? 'bg-red-600 text-white border-red-600'
                  : s === j.stage ? 'bg-coal text-white border-coal'
                    : mine < idx ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-seam text-stone-400';
                return (
                  <span key={s} className='flex items-center gap-1'>
                    {si > 0 && <span className='text-stone-300'>›</span>}
                    <span className={`rounded border px-1.5 py-0.5 ${cls}`}>{s}</span>
                  </span>
                );
              })}
            </div>
            {j.error && <div className='mt-2 font-mono text-xs text-red-700'>{j.error.split('\n')[0]}</div>}
            {pageNos.length > 0 && (
              <div className='mt-3 rounded-lg border border-seam bg-paper px-3 py-2'>
                <button onClick={() => setOpen((o) => ({ ...o, [j.id]: !o[j.id] }))}
                        className='font-mono text-[11px] uppercase tracking-wide text-coal hover:underline'>
                  {isOpen ? 'Hide' : 'Show'} per-page OCR + summaries ({pageNos.length})
                </button>
                {isOpen && (
                  <div className='mt-2 max-h-64 space-y-2 overflow-auto'>
                    {pageNos.map((pn) => (
                      <div key={pn} className='rounded-md border border-seam bg-white px-3 py-2'>
                        <p className='font-mono text-[10px] uppercase tracking-wide text-stone-400'>Page {pn}</p>
                        {pageSums[pn] && <p className='mt-1 text-[12.5px] leading-relaxed text-stone-700'><span className='font-semibold text-coal'>Summary: </span>{pageSums[pn]}</p>}
                        {pageTexts[pn] && <p className='mt-1 font-mono text-[11px] leading-relaxed text-stone-500'><span className='font-semibold'>OCR: </span>{pageTexts[pn].slice(0, 400)}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </AnimatedGroup>
  );
}

function LoaderCircle2() {
  return <LoaderCircle className='h-3.5 w-3.5 animate-spin' />;
}
function CircleCheck() {
  return (
    <svg className='h-3.5 w-3.5' fill='none' viewBox='0 0 24 24' strokeWidth='2' stroke='currentColor'>
      <circle cx='12' cy='12' r='10' /><path d='m9 12 2 2 4-4' />
    </svg>
  );
}

export default function Pipeline() {
  const { data, error, reload } = usePageData('/api/pages/pipeline');
  const [files, setFiles] = useState([]);
  const [hot, setHot] = useState(false);
  const [busy, setBusy] = useState(false);
  const [ingested, setIngested] = useState(null);
  const inputRef = useRef(null);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { stats } = data;

  const submit = async (fileList) => {
    const picked = Array.from(fileList || []);
    if (!picked.length || busy) return;
    setFiles(picked.map((f) => f.name));
    setBusy(true);
    try {
      const res = await uploadFiles(picked);
      setIngested(res.results);
      reload();
    } catch (err) {
      setIngested([{ filename: "upload", error: err.message }]);
    }
    setBusy(false);
    if (inputRef.current) inputRef.current.value = "";
  };

  const loadDemo = async () => {
    setBusy(true);
    try {
      await fetch('/api/pipeline/demo', { method: 'POST' });
      reload();
    } catch { /* ignore */ }
    setBusy(false);
  };

  const chips = ['PDF', 'Scanned PDF', 'DOCX', 'XLSX', 'CSV', 'Images'];
  const statCards = [
    ['Documents', stats.documents],
    ['Chunks Indexed', stats.chunks],
    ['Facts With Receipts', stats.facts],
    ['Extracted Tags', stats.tags],
  ];

  return (
    <div>
      <PageHeader
        title='Pipeline'
        subtitle='Drop in digital or scanned PDFs, DOCX, XLSX, CSV and images. Everything is parsed, chunked, embedded, summarized and indexed on this machine.'
      />

      {ingested && (
        <Rise className='mt-6'>
          <h2 className='text-lg font-semibold'>Queued For Ingestion</h2>
          <AnimatedGroup preset='fade' className='mt-3 space-y-3'>
            {ingested.map((r, i) => (
              <div key={i} className='flex items-center justify-between rounded-xl border border-seam bg-white px-5 py-4 shadow-card'>
                <span className='text-sm font-semibold'>{r.filename}</span>
                {r.error
                  ? <span className='rounded-full border border-red-200 bg-red-50 px-3 py-1 font-mono text-[11px] text-red-700'>rejected: {r.error}</span>
                  : r.duplicate
                    ? <span className='rounded-full border border-seam bg-paper px-3 py-1 font-mono text-[11px] text-stone-500'>duplicate of existing document</span>
                    : <span className='rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-mono text-[11px] text-emerald-700'>queued</span>}
              </div>
            ))}
          </AnimatedGroup>
        </Rise>
      )}

      <Rise delay={0.05} className='mt-6'>
        <div>
          <div
            className={`dropzone relative overflow-hidden rounded-2xl border-2 border-dashed border-seamdark bg-white px-6 py-14 text-center shadow-card hover:border-coal ${hot ? 'dropzone-hot' : ''}`}
            onDragEnter={(e) => { e.preventDefault(); setHot(true); }}
            onDragOver={(e) => { e.preventDefault(); setHot(true); }}
            onDragLeave={(e) => { e.preventDefault(); setHot(false); }}
            onDrop={(e) => {
              e.preventDefault(); setHot(false);
              if (e.dataTransfer.files.length) submit(e.dataTransfer.files);
            }}
          >
            {busy}
            <input ref={inputRef} type='file' name='files' multiple
              onChange={(e) => submit(e.target.files)}
              className='absolute inset-0 h-full w-full cursor-pointer opacity-0'
              accept='.pdf,.docx,.xlsx,.xls,.csv,.txt,.png,.jpg,.jpeg,.tif,.tiff' title='Choose files to ingest' />
            <div className='pointer-events-none'>
              <div className='mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-coalsoft text-coal transition-transform duration-300 hover:scale-105'>
                <Upload className='h-8 w-8' />
              </div>
              <p className='mt-5 text-[16px] font-semibold'>{busy ? 'Ingesting files…' : 'Drag & drop files here'}</p>
              <p className='mt-1 text-[13.5px] text-stone-500'>or click to browse — ingestion starts automatically</p>
              <div className='mt-5 flex flex-wrap items-center justify-center gap-1.5'>
                {chips.map((t) => (
                  <span key={t} className='rounded-full border border-seam bg-paper px-2.5 py-0.5 font-mono text-[10.5px] uppercase tracking-wide text-stone-400'>{t}</span>
                ))}
              </div>
            </div>
          </div>
          <div className='mt-3 flex flex-wrap gap-1.5'>
            {files.map((n) => (
              <span key={n} className='inline-flex items-center gap-1.5 rounded-full border border-coalline bg-coalsoft px-3 py-1 text-[12px] text-coal'>
                <FileIcon className='h-3 w-3' />{n}
              </span>
            ))}
          </div>
          <div className='mt-4 flex flex-wrap items-center justify-between gap-3'>
            <button type='button' onClick={loadDemo} disabled={busy} title='Generate and ingest a curated demonstration corpus'
              className='flex items-center gap-1.5 text-[12.5px] font-medium text-stone-500 transition-colors hover:text-coal disabled:opacity-50'>
              <Package className='h-3.5 w-3.5 text-stone-400' /> No files handy? Load the demonstration dataset
            </button>
            <p className='flex items-center gap-1.5 text-[13px] text-stone-500'>
              <Info className='h-4 w-4 shrink-0 text-stone-400' />
              Duplicates are rejected by SHA-256. Revised reports join version chains automatically.
            </p>
          </div>
        </div>
      </Rise>

      <AnimatedGroup preset='blur-slide' className='mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4'>
        {statCards.map(([label, value]) => (
          <div key={label} className='flex items-center gap-3 rounded-xl border border-seam bg-white px-4 py-3.5 shadow-card'>
            <div>
              <AnimatedNumber value={value} className='font-mono text-[20px] font-semibold leading-none tracking-tight' />
              <div className='mt-1 text-[12px] text-stone-500'>{label}</div>
            </div>
          </div>
        ))}
      </AnimatedGroup>

      <Rise delay={0.15}>
        <div className='mt-8 flex items-center justify-between'>
          <h2 className='text-lg font-semibold tracking-tight'>Recent Jobs</h2>
          <span className='flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-stone-400'>
            <span className='h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600'></span> live
          </span>
        </div>
        <JobStrip />
      </Rise>
    </div>
  );
}
