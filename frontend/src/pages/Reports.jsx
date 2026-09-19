import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Landmark, FileChartColumn, Eye, Download } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button, EmptyState } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { MorphingDialog, MorphingDialogTrigger, MorphingDialogContent, MorphingDialogTitle, MorphingDialogSubtitle, MorphingDialogClose } from '../components/motion/morphing-dialog.jsx';

const TEMPLATE_LABELS = {
  agent_run: 'Agent Report',
  analytical: 'Analytical Report',
  comprehensive: 'Comprehensive Analysis',
  parliamentary_reply: 'Parliamentary Draft Reply',
};

export default function Reports() {
  const { data, error, reload } = usePageData('/api/pages/reports');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const templateLabel = (t) =>
    TEMPLATE_LABELS[t] || t.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const generate = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await postJSON('/api/reports/generate', Object.fromEntries(f));
      setNotice('Report generated.');
      reload();
    } catch (err) { setNotice(err.message); }
    setBusy(false);
  };

  const parliamentary = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await postJSON('/api/reports/parliamentary', { question: f.get('question') });
      setNotice('Draft reply is being generated; it will appear below shortly.');
      reload();
    } catch (err) { setNotice(err.message); }
    setBusy(false);
  };

  return (
    <div>
      <PageHeader
        title='Report Studio'
        subtitle='Report generation with receipts: comprehensive analysis from the whole library, template reports, and a parliamentary question-to-draft workflow. Every output goes through review before approval.'
      />

      {notice && <div className='mt-4 rounded-xl border border-ok/30 bg-ok/10 px-4 py-3 text-xs font-medium text-ok'>{notice}</div>}

      <Rise delay={0.05}>
        <Card className='mt-6 border-coalline bg-coalsoft/40 p-5'>
          <div className='flex items-center gap-2'>
            <Landmark className='h-4 w-4 text-coal' />
            <h2 className='text-sm font-semibold text-ink'>Parliamentary Question to Draft</h2>
          </div>
          <p className='mt-1 text-xs text-muted1'>Paste the question; the system retrieves the evidence, drafts the reply and records what it stands on for review.</p>
          <form onSubmit={parliamentary} className='mt-3 flex flex-wrap items-start gap-3'>
            <textarea
              name='question'
              rows='2'
              required
              placeholder='e.g. What was the raw coal production of CIL in 2023-24 and how does it compare with the previous year?'
              className='w-full min-w-0 flex-1 resize-y rounded-lg border border-seam bg-surface px-3.5 py-2.5 text-xs sm:text-sm text-ink placeholder:text-muted2 focus:border-coal focus:outline-none'
            />
            <Button
              type='submit'
              variant='primary'
              size='md'
              disabled={busy}
              className='px-5'
            >
              Generate Draft
            </Button>
          </form>
        </Card>
      </Rise>

      <Rise delay={0.1}>
        <Card className='mt-5 p-5'>
          <div className='flex items-center gap-2'>
            <FileChartColumn className='h-4 w-4 text-coal' />
            <h2 className='text-sm font-semibold text-ink'>Template and Comprehensive Reports</h2>
          </div>
          <form onSubmit={generate} className='mt-3 flex flex-wrap items-center gap-3'>
            <select name='template' className='rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink focus:border-coal focus:outline-none'>
              {data.templates.map((t) => (
                <option key={t} value={t}>{t === 'comprehensive' ? 'Comprehensive Analysis (full extraction + charts)' : templateLabel(t)}</option>
              ))}
            </select>
            <select name='entity' className='rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink focus:border-coal focus:outline-none'>
              <option value=''>Any entity</option>
              {data.entities.map((e) => <option key={e.canonical_name} value={e.canonical_name}>{e.canonical_name}</option>)}
            </select>
            <input
              name='period'
              placeholder='Period, e.g. 2021-22'
              className='rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink placeholder:text-muted2 focus:border-coal focus:outline-none'
            />
            <input
              name='question'
              placeholder='Optional focus or question'
              className='w-full min-w-0 flex-1 rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink placeholder:text-muted2 focus:border-coal focus:outline-none'
            />
            <Button
              type='submit'
              variant='primary'
              size='md'
              disabled={busy}
              className='px-5'
            >
              Generate
            </Button>
          </form>
        </Card>
      </Rise>

      <h2 className='mt-10 text-base font-semibold tracking-tight text-ink'>Generated Reports</h2>
      {data.reports.length === 0 ? (
        <Rise delay={0.12}>
          <EmptyState
            icon={FileChartColumn}
            title='No reports yet'
            description='Generate a comprehensive analysis or paste a parliamentary question above.'
            className='mt-4'
          />
        </Rise>
      ) : (
        <AnimatedGroup preset='blur-slide' className='mt-4 grid grid-cols-1 gap-4 md:grid-cols-2'>
          {data.reports.map((r) => (
            <Card key={r.id} className='flex h-full flex-col p-5'>
              <div className='flex items-start justify-between gap-2'>
                <div className='min-w-0'>
                  <MorphingDialog>
                    <MorphingDialogTrigger className='text-left font-semibold text-ink hover:text-coal text-sm'>
                      {templateLabel(r.template)}
                    </MorphingDialogTrigger>
                    <MorphingDialogContent>
                      <MorphingDialogTitle>{templateLabel(r.template)}</MorphingDialogTitle>
                      <MorphingDialogSubtitle>Report #{r.id} · {(r.created_ts || '').slice(0, 16)} · {r.review_status}</MorphingDialogSubtitle>
                      <p className='mt-3 font-mono text-[11px] uppercase tracking-wider text-muted1'>Parameters</p>
                      <p className='mt-1 break-all font-mono text-xs text-ink'>{r.params_json}</p>
                      <div className='mt-5 flex flex-wrap gap-2'>
                        <Button
                          to={`/reports/${r.id}`}
                          variant='primary'
                          size='sm'
                        >
                          <Eye className='h-3.5 w-3.5' /> Open Review
                        </Button>
                        <Button
                          href={`/reports/${r.id}/download`}
                          variant='secondary'
                          size='sm'
                        >
                          <Download className='h-3.5 w-3.5' /> DOCX
                        </Button>
                      </div>
                      <MorphingDialogClose />
                    </MorphingDialogContent>
                  </MorphingDialog>
                  <p className='mt-0.5 font-mono text-[11px] text-muted1 tabular-nums'>#{r.id} · {(r.created_ts || '').slice(0, 16)}</p>
                </div>
                <Badge
                  variant={r.review_status === 'approved' ? 'ok' : r.review_status === 'returned' ? 'bad' : 'neutral'}
                  className='shrink-0 uppercase text-[10px]'
                >
                  {r.review_status}
                </Badge>
              </div>
              <p className='mt-2 line-clamp-1 font-mono text-xs text-muted1'>{r.params_json}</p>
              <div className='mt-auto flex flex-wrap items-center gap-2 pt-3'>
                <Button
                  to={`/reports/${r.id}`}
                  variant='secondary'
                  size='sm'
                >
                  <Eye className='h-3.5 w-3.5' /> Review
                </Button>
                <Button
                  href={`/reports/${r.id}/download`}
                  variant='ghost'
                  size='sm'
                >
                  <Download className='h-3.5 w-3.5' /> DOCX
                </Button>
              </div>
            </Card>
          ))}
        </AnimatedGroup>
      )}
    </div>
  );
}
