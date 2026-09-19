import { useRef, useState } from 'react';
import { Upload, Package, Info, File as FileIcon, TriangleAlert as Alert, LoaderCircle, CheckCircle2 } from 'lucide-react';
import { usePageData, usePolling } from '../hooks/useData.js';
import { uploadFiles } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, SectionTitle, Badge, Button } from '../components/ui.jsx';
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
          <Card
            key={j.id || i}
            className={`p-4 ${failed ? 'border-red-200 bg-red-50/60' : ''}`}
          >
            <div className='flex items-baseline justify-between gap-4 overflow-hidden'>
              <span className='min-w-0 truncate text-sm font-semibold text-ink'>{j.filename || 'unknown file'}</span>
              <span className={`flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide ${failed ? 'text-red-700' : j.status === 'completed' ? 'text-emerald-700' : 'text-coal'}`}>
                {failed ? <Alert className='h-3.5 w-3.5' /> : running
                  ? <LoaderCircle className='h-3.5 w-3.5 animate-spin' /> : <CheckCircle2 className='h-3.5 w-3.5' />}
                {failed ? 'failed' : j.stage}
                {stats.pages_done && stats.pages_total ? ` · pages ${stats.pages_done}/${stats.pages_total}` : ''}
              </span>
            </div>
            <div className='mt-2.5 flex flex-wrap items-center gap-1 text-[10px] font-mono uppercase tracking-wide'>
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
          </Card>
        );
      })}
    </AnimatedGroup>
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
          <SectionTitle title='Queued For Ingestion' />
          <AnimatedGroup preset='fade' className='mt-3 space-y-3'>
            {ingested.map((r, i) => (
              <Card key={i} className='flex items-center justify-between px-5 py-4'>
                <span className='text-sm font-semibold text-ink'>{r.filename}</span>
                {r.error
                  ? <Badge variant='bad'>rejected: {r.error}</Badge>
                  : r.duplicate
                    ? <Badge variant='neutral'>duplicate of existing document</Badge>
                    : <Badge variant='ok'>queued</Badge>}
              </Card>
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
              <p className='mt-5 text-[16px] font-semibold text-ink'>{busy ? 'Ingesting files…' : 'Drag & drop files here'}</p>
              <p className='mt-1 text-[13.5px] text-stone-500'>or click to browse — ingestion starts automatically</p>
              <div className='mt-5 flex flex-wrap items-center justify-center gap-1.5'>
                {chips.map((t) => (
                  <Badge key={t} variant='neutral'>{t}</Badge>
                ))}
              </div>
            </div>
          </div>
          <div className='mt-3 flex flex-wrap gap-1.5'>
            {files.map((n) => (
              <Badge key={n} variant='coal' icon={FileIcon}>{n}</Badge>
            ))}
          </div>
          <div className='mt-4 flex flex-wrap items-center justify-between gap-3'>
            <Button variant='ghost' size='sm' icon={Package} onClick={loadDemo} disabled={busy} title='Generate and ingest a curated demonstration corpus'>
              No files handy? Load the demonstration dataset
            </Button>
            <p className='flex items-center gap-1.5 text-[13px] text-stone-500'>
              <Info className='h-4 w-4 shrink-0 text-stone-400' />
              Duplicates are rejected by SHA-256. Revised reports join version chains automatically.
            </p>
          </div>
        </div>
      </Rise>

      <AnimatedGroup preset='blur-slide' className='mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4'>
        {statCards.map(([label, value]) => (
          <Card key={label} className='flex items-center gap-3 px-4 py-3.5'>
            <div>
              <AnimatedNumber value={value} className='font-mono tabular-nums text-[20px] font-semibold leading-none tracking-tight text-ink' />
              <div className='mt-1 text-[12px] text-stone-500'>{label}</div>
            </div>
          </Card>
        ))}
      </AnimatedGroup>

      <Rise delay={0.15}>
        <div className='mt-8'>
          <SectionTitle
            title='Recent Jobs'
            badge={
              <span className='flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-stone-400'>
                <span className='h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600'></span> live
              </span>
            }
          />
          <JobStrip />
        </div>
      </Rise>
    </div>
  );
}
