import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Check, Files, TriangleAlert, ScanText, Download } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button } from '../components/ui.jsx';
import { AnimatedNumber } from '../components/motion/animated-number.jsx';
import { ScrollProgress } from '../components/motion/scroll-progress.jsx';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from '../components/motion/dialog.jsx';

export default function Review() {
  const { rid } = useParams();
  const { data, error } = usePageData(`/api/pages/review/${rid}`);
  const [note, setNote] = useState('');
  const [operator, setOperator] = useState(() => localStorage.getItem('cmpdi-operator') || '');
  const [busy, setBusy] = useState(false);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { report, sources, stats, conflict_counts: conflictCounts } = data;
  const docsUsed = new Set(sources.map((s) => s.doc_id)).size;
  const ocrCount = sources.filter((s) => s.ocr).length;

  const act = async (status) => {
    setBusy(true);
    try {
      localStorage.setItem('cmpdi-operator', operator);
      await postJSON(`/api/reports/${report.id}/review`, { status, note, operator });
      window.location.reload();
    } catch { setBusy(false); }
  };

  const statusVariant =
    report.review_status === 'approved' ? 'ok'
    : report.review_status === 'returned' ? 'bad'
    : 'neutral';

  return (
    <div>
      <ScrollProgress />
      <Rise>
        <PageHeader
          title='Report Review'
          subtitle={`${String(report.template).replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())} · generated ${(report.created_ts || '').slice(0, 16)}`}
        >
          <Badge variant={statusVariant} className='uppercase text-[11px]'>{report.review_status}</Badge>
        </PageHeader>
      </Rise>

      <Rise delay={0.05}>
        <div className='mt-6 grid grid-cols-1 gap-3 sm:grid-cols-4'>
          {[
            [Check, 'Sources cited', sources.length],
            [Files, 'Documents used', docsUsed],
            [TriangleAlert, 'Open conflicts', conflictCounts.detected || 0],
            [ScanText, 'OCR sources', ocrCount],
          ].map(([Icon, label, value]) => (
            <Card key={label} className='flex items-center gap-3 p-4'>
              <span className='flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-coalsoft text-coal'>
                <Icon className='h-4 w-4' />
              </span>
              <div>
                <AnimatedNumber value={value} className='font-mono text-xl font-semibold leading-none tabular-nums text-ink' />
                <div className='mt-1 text-xs text-muted1'>{label}</div>
              </div>
            </Card>
          ))}
        </div>
      </Rise>

      {stats && (
        <Rise delay={0.08}>
          <Card className='mt-4 border-coalline bg-coalsoft/50 p-4'>
            <p className='font-mono text-[10.5px] font-bold uppercase tracking-wider text-coal'>Retrieval (parliamentary draft)</p>
            <div className='mt-2.5 grid grid-cols-2 gap-2 sm:grid-cols-5 text-xs'>
              <div>
                <AnimatedNumber value={stats.documents_searched} className='font-mono text-base font-semibold tabular-nums text-ink' />
                <span className='ml-1.5 text-muted1'>docs searched</span>
              </div>
              <div>
                <AnimatedNumber value={stats.relevant_passages} className='font-mono text-base font-semibold tabular-nums text-ink' />
                <span className='ml-1.5 text-muted1'>passages</span>
              </div>
              <div>
                <AnimatedNumber value={stats.facts_used} className='font-mono text-base font-semibold tabular-nums text-ink' />
                <span className='ml-1.5 text-muted1'>facts used</span>
              </div>
              <div>
                <AnimatedNumber value={stats.conflicts} className='font-mono text-base font-semibold tabular-nums text-ink' />
                <span className='ml-1.5 text-muted1'>conflicts</span>
              </div>
              <div>
                <span className='font-mono text-base font-semibold text-ink'>{stats.quality}</span>
                <span className='ml-1.5 text-muted1'>evidence quality</span>
              </div>
            </div>
          </Card>
        </Rise>
      )}

      {report.review_note && (
        <div className='mt-4 rounded-xl border border-bad/30 bg-bad/10 px-4 py-3 text-xs text-bad'>
          <strong>Returned for revision:</strong> {report.review_note}
        </div>
      )}
      {(report.reviewed_by || report.review_rounds > 0) && (
        <p className='mt-3 text-[12.5px] text-stone-500'>
          Decided by {report.reviewed_by || 'an officer'}
          {report.review_rounds > 0 && ` · returned ${report.review_rounds} time${report.review_rounds === 1 ? '' : 's'}`}
        </p>
      )}

      <Rise delay={0.12}>
        <Card className='mt-6 overflow-hidden p-0'>
          <div className='border-b border-seam bg-paper/60 px-5 py-3 text-xs font-semibold text-ink uppercase tracking-wider'>
            Every source, verified
          </div>
          <div className='divide-y divide-seam bg-surface'>
            {sources.length === 0 ? (
              <p className='px-5 py-8 text-center text-xs text-muted1'>No provenance recorded for this report.</p>
            ) : sources.map((s) => (
              <div key={s.ref} className='flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-xs'>
                <span className='flex flex-wrap items-center gap-2'>
                  <span className='rounded border border-coalline bg-coalsoft px-1.5 py-0.5 font-mono text-[10.5px] font-semibold text-coal'>[{s.ref}]</span>
                  <span className='font-medium text-ink'>{s.filename}</span>
                  {s.current_version
                    ? <Badge variant='ok' className='text-[10px]'>current version</Badge>
                    : <Badge variant='neutral' className='text-[10px] line-through'>superseded</Badge>}
                  {s.ocr && <Badge variant='coal' className='text-[10px]'>OCR</Badge>}
                </span>
                <Link
                  className='font-mono text-xs font-semibold text-coal hover:underline'
                  to={`/doc/${s.doc_id}${s.page_no ? `?page=${s.page_no}` : s.sheet_no != null ? `?sheet=${s.sheet_no}` : ''}`}
                >
                  Open source →
                </Link>
              </div>
            ))}
          </div>
        </Card>
      </Rise>

      <Rise delay={0.16}>
        <div className='mt-6 flex flex-wrap items-center gap-3'>
          <input value={operator} onChange={(e) => setOperator(e.target.value)} placeholder='Reviewing officer…'
                 className='rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm shadow-card focus:border-coal focus:outline-none' />
          <Magnetic intensity={0.25} range={90}>
            <button onClick={() => act('approved')} disabled={busy}
                    className='flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:opacity-50'>
              <Check className='h-4 w-4' /> Approve Report
            </button>
          </Magnetic>
          <Dialog>
            <DialogTrigger className='rounded-lg border border-seam bg-surface px-4 py-2.5 text-xs font-semibold text-ink shadow-card transition-colors hover:border-bad hover:text-bad disabled:opacity-50'>
              Return for Revision
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Return this report?</DialogTitle>
                <DialogDescription>
                  Tell the drafting officer what needs revision. The report stays in the library with your note attached.
                </DialogDescription>
              </DialogHeader>
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder='Reason for returning...'
                className='mt-4 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink placeholder:text-muted2 focus:border-coal focus:outline-none'
              />
              <div className='mt-4 flex justify-end gap-2'>
                <DialogClose className='rounded-lg border border-seam bg-surface px-3.5 py-1.5 text-xs font-medium text-muted0 transition-colors hover:border-coal hover:text-coal'>
                  Cancel
                </DialogClose>
                <Button
                  variant='danger'
                  size='sm'
                  onClick={() => act('returned')}
                  disabled={busy || !note.trim()}
                >
                  Confirm Return
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Button
            variant='secondary'
            size='md'
            href={`/reports/${report.id}/download`}
          >
            <Download className='h-4 w-4' /> DOCX
          </Button>
          <a href={`/reports/${report.id}/audit`}
             className='flex items-center gap-2 rounded-lg border border-seam px-4 py-2.5 text-sm font-semibold text-stone-600 transition-colors hover:border-coal hover:text-coal'>
            <Download className='h-4 w-4' /> Audit JSON
          </a>
        </div>
      </Rise>
    </div>
  );
}
