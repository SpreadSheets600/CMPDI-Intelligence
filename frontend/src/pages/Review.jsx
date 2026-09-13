import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Check, Files, TriangleAlert, ScanText, Download } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, Loading, ErrorBox } from '../components/ui.jsx';
import { AnimatedNumber } from '../components/motion/animated-number.jsx';
import { ScrollProgress } from '../components/motion/scroll-progress.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from '../components/motion/dialog.jsx';

export default function Review() {
  const { rid } = useParams();
  const { data, error } = usePageData(`/api/pages/review/${rid}`);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { report, sources, stats, conflict_counts: conflictCounts } = data;
  const docsUsed = new Set(sources.map((s) => s.doc_id)).size;
  const ocrCount = sources.filter((s) => s.ocr).length;

  const act = async (status) => {
    setBusy(true);
    try {
      await postJSON(`/api/reports/${report.id}/review`, { status, note });
      window.location.reload();
    } catch { setBusy(false); }
  };

  const statusBadge =
    report.review_status === 'approved' ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : report.review_status === 'returned' ? 'border-red-200 bg-red-50 text-red-700'
    : 'border-seam bg-paper text-stone-500';

  return (
    <div>
      <ScrollProgress />
      <Rise>
        <div className='flex flex-wrap items-start justify-between gap-3'>
          <div>
            <h1 className='text-2xl font-semibold tracking-tight'>Report Review</h1>
            <p className='mt-1 text-[15px] text-stone-500'>
              {String(report.template).replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())} · generated {(report.created_ts || '').slice(0, 16)}
            </p>
          </div>
          <span className={`rounded-full border px-3 py-1 font-mono text-[11px] uppercase ${statusBadge}`}>{report.review_status}</span>
        </div>
      </Rise>

      <Rise delay={0.05}>
        <div className='mt-6 grid grid-cols-1 gap-3 sm:grid-cols-4'>
          {[
            [Check, 'Sources cited', sources.length],
            [Files, 'Documents used', docsUsed],
            [TriangleAlert, 'Open conflicts', conflictCounts.detected || 0],
            [ScanText, 'OCR sources', ocrCount],
          ].map(([Icon, label, value]) => (
            <div key={label} className='flex items-center gap-3 rounded-xl border border-seam bg-white px-4 py-3.5 shadow-card'>
              <span className='flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-coalsoft text-coal'><Icon className='h-[18px] w-[18px]' /></span>
              <div>
                <AnimatedNumber value={value} className='font-mono text-[20px] font-semibold leading-none' />
                <div className='mt-1 text-[12px] text-stone-500'>{label}</div>
              </div>
            </div>
          ))}
        </div>
      </Rise>

      {stats && (
        <Rise delay={0.08}>
          <div className='mt-4 rounded-xl border border-coalline bg-coalsoft/60 p-4 text-[13.5px]'>
            <p className='font-mono text-[10.5px] font-bold uppercase tracking-widest text-coal'>Retrieval (parliamentary draft)</p>
            <div className='mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5'>
              <div><AnimatedNumber value={stats.documents_searched} className='font-mono text-[17px] font-semibold' /><span className='ml-1.5 text-stone-500'>docs searched</span></div>
              <div><AnimatedNumber value={stats.relevant_passages} className='font-mono text-[17px] font-semibold' /><span className='ml-1.5 text-stone-500'>passages</span></div>
              <div><AnimatedNumber value={stats.facts_used} className='font-mono text-[17px] font-semibold' /><span className='ml-1.5 text-stone-500'>facts used</span></div>
              <div><AnimatedNumber value={stats.conflicts} className='font-mono text-[17px] font-semibold' /><span className='ml-1.5 text-stone-500'>conflicts</span></div>
              <div><span className='font-mono text-[17px] font-semibold'>{stats.quality}</span><span className='ml-1.5 text-stone-500'>evidence quality</span></div>
            </div>
          </div>
        </Rise>
      )}

      {report.review_note && (
        <div className='mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13.5px] text-red-700'>
          <strong>Returned for revision:</strong> {report.review_note}
        </div>
      )}

      <Rise delay={0.12}>
        <div className='mt-6 overflow-hidden rounded-xl border border-seam bg-white shadow-card'>
          <div className='border-b border-seam bg-paper px-5 py-3 text-[13.5px] font-semibold'>Every source, verified</div>
          <div className='divide-y divide-seam'>
            {sources.length === 0 ? (
              <p className='px-5 py-8 text-center text-sm text-stone-500'>No provenance recorded for this report.</p>
            ) : sources.map((s) => (
              <div key={s.ref} className='flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-[13.5px]'>
                <span className='flex items-center gap-2'>
                  <span className='rounded border border-coalline bg-coalsoft px-1.5 py-0.5 font-mono text-[10.5px] font-semibold text-coal'>[{s.ref}]</span>
                  <span className='font-medium'>{s.filename}</span>
                  {s.current_version
                    ? <span className='rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10.5px] text-emerald-700'>current version</span>
                    : <span className='rounded-full border border-seam bg-paper px-2 py-0.5 text-[10.5px] text-stone-400 line-through'>superseded</span>}
                  {s.ocr && <span className='rounded-full border border-coalline bg-coalsoft px-2 py-0.5 text-[10.5px] text-coal'>OCR</span>}
                </span>
                <Link className='text-[12.5px] font-medium text-coal hover:underline'
                      to={`/doc/${s.doc_id}${s.page_no ? `?page=${s.page_no}` : s.sheet_no != null ? `?sheet=${s.sheet_no}` : ''}`}>
                  Open source →
                </Link>
              </div>
            ))}
          </div>
        </div>
      </Rise>

      <Rise delay={0.16}>
        <div className='mt-6 flex flex-wrap items-center gap-3'>
          <Magnetic intensity={0.25} range={90}>
            <button onClick={() => act('approved')} disabled={busy}
                    className='flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:opacity-50'>
              <Check className='h-4 w-4' /> Approve Report
            </button>
          </Magnetic>
          <Dialog>
            <DialogTrigger className='rounded-lg border border-seam px-4 py-2.5 text-sm font-semibold text-stone-600 transition-colors hover:border-red-300 hover:text-red-700 disabled:opacity-50'>
              Return for Revision
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Return this report?</DialogTitle>
                <DialogDescription>
                  Tell the drafting officer what needs revision. The report stays in the library with your note attached.
                </DialogDescription>
              </DialogHeader>
              <input value={note} onChange={(e) => setNote(e.target.value)} placeholder='Reason for returning...'
                     className='mt-4 w-full rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm focus:border-coal focus:outline-none' />
              <div className='mt-4 flex justify-end gap-2'>
                <DialogClose className='rounded-lg border border-seam px-4 py-2 text-sm font-medium text-stone-500 transition-colors hover:border-coal hover:text-coal'>
                  Cancel
                </DialogClose>
                <button onClick={() => act('returned')} disabled={busy || !note.trim()}
                        className='rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:opacity-50'>
                  Confirm Return
                </button>
              </div>
            </DialogContent>
          </Dialog>
          <a href={`/reports/${report.id}/download`}
             className='flex items-center gap-2 rounded-lg border border-seam px-4 py-2.5 text-sm font-semibold text-stone-600 transition-colors hover:border-coal hover:text-coal'>
            <Download className='h-4 w-4' /> DOCX
          </a>
        </div>
      </Rise>
    </div>
  );
}
