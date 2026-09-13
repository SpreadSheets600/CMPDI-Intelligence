import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Landmark, FileChartColumn, Eye, Download } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { Tilt } from '../components/motion/tilt.jsx';
import { Spotlight } from '../components/motion/spotlight.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';
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

      {notice && <div className='mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-[13.5px] text-emerald-700'>{notice}</div>}

      <Rise delay={0.05}>
        <Spotlight className='mt-6 rounded-xl border border-coalline bg-coalsoft/50 p-5 shadow-card'>
          <div className='flex items-center gap-2'>
            <Landmark className='h-4 w-4 text-coal' />
            <h2 className='text-[15px] font-semibold'>Parliamentary Question to Draft</h2>
          </div>
          <p className='mt-1 text-[13.5px] text-stone-500'>Paste the question; the system retrieves the evidence, drafts the reply and records what it stands on for review.</p>
          <form onSubmit={parliamentary} className='mt-3 flex flex-wrap items-start gap-3'>
            <textarea name='question' rows='2' required
                      placeholder='e.g. What was the raw coal production of CIL in 2023-24 and how does it compare with the previous year?'
                      className='w-full min-w-0 flex-1 resize-y rounded-lg border border-seamdark bg-white px-3.5 py-2.5 text-[14px] focus:border-coal focus:outline-none'></textarea>
            <Magnetic intensity={0.25} range={90}>
              <button disabled={busy}
                      className='rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-colors hover:bg-amber-500 disabled:opacity-50'>
                Generate Draft
              </button>
            </Magnetic>
          </form>
        </Spotlight>
      </Rise>

      <Rise delay={0.1}>
        <div className='mt-5 rounded-xl border border-seam bg-white p-5 shadow-card'>
          <div className='flex items-center gap-2'>
            <FileChartColumn className='h-4 w-4 text-coal' />
            <h2 className='text-[15px] font-semibold'>Template and Comprehensive Reports</h2>
          </div>
          <form onSubmit={generate} className='mt-3 flex flex-wrap items-center gap-3'>
            <select name='template' className='rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm focus:border-coal focus:outline-none'>
              {data.templates.map((t) => (
                <option key={t} value={t}>{t === 'comprehensive' ? 'Comprehensive Analysis (full extraction + charts)' : templateLabel(t)}</option>
              ))}
            </select>
            <select name='entity' className='rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm focus:border-coal focus:outline-none'>
              <option value=''>Any entity</option>
              {data.entities.map((e) => <option key={e.canonical_name} value={e.canonical_name}>{e.canonical_name}</option>)}
            </select>
            <input name='period' placeholder='Period, e.g. 2021-22'
                   className='rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm focus:border-coal focus:outline-none' />
            <input name='question' placeholder='Optional focus or question'
                   className='w-full min-w-0 flex-1 rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm focus:border-coal focus:outline-none' />
            <Magnetic intensity={0.25} range={90}>
              <button type='submit' disabled={busy}
                      className='rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-colors hover:bg-amber-500 disabled:opacity-50'>Generate</button>
            </Magnetic>
          </form>
        </div>
      </Rise>

      <h2 className='mt-10 text-lg font-semibold tracking-tight'>Generated Reports</h2>
      {data.reports.length === 0 ? (
        <Rise delay={0.12}>
          <div className='mt-4 flex flex-col items-center rounded-2xl border border-dashed border-seamdark bg-white px-6 py-14 text-center'>
            <span className='flex h-12 w-12 items-center justify-center rounded-xl bg-coalsoft text-coal'><FileChartColumn className='h-6 w-6' /></span>
            <p className='mt-3 text-sm font-semibold'>No reports yet</p>
            <p className='mt-1 text-[13px] text-stone-500'>Generate a comprehensive analysis or paste a parliamentary question above.</p>
          </div>
        </Rise>
      ) : (
        <AnimatedGroup preset='blur-slide' className='mt-4 grid grid-cols-1 gap-4 md:grid-cols-2'>
          {data.reports.map((r) => (
            <Tilt key={r.id} rotationFactor={3}>
              <article className='flex h-full flex-col rounded-xl border border-seam bg-white p-5 shadow-card transition-colors duration-300 hover:border-coal hover:shadow-lift'>
                <div className='flex items-start justify-between gap-2'>
                  <div className='min-w-0'>
                    <MorphingDialog>
                      <MorphingDialogTrigger className='text-left font-semibold hover:text-coal'>
                        {templateLabel(r.template)}
                      </MorphingDialogTrigger>
                      <MorphingDialogContent>
                        <MorphingDialogTitle>{templateLabel(r.template)}</MorphingDialogTitle>
                        <MorphingDialogSubtitle>Report #{r.id} · {(r.created_ts || '').slice(0, 16)} · {r.review_status}</MorphingDialogSubtitle>
                        <p className='mt-3 font-mono text-[11.5px] text-stone-500'>Parameters</p>
                        <p className='mt-1 break-all font-mono text-[12px]'>{r.params_json}</p>
                        <div className='mt-5 flex flex-wrap gap-2'>
                          <Link to={`/reports/${r.id}/review`}
                                className='flex items-center gap-1.5 rounded-lg bg-coal px-4 py-2 text-[12.5px] font-semibold text-white transition-colors hover:bg-amber-500'>
                            <Eye className='h-3.5 w-3.5' /> Open Review
                          </Link>
                          <a href={`/reports/${r.id}/download`}
                             className='flex items-center gap-1.5 rounded-lg border border-seam px-4 py-2 text-[12.5px] font-medium text-stone-500 transition-colors hover:border-coal hover:text-coal'>
                            <Download className='h-3.5 w-3.5' /> DOCX
                          </a>
                        </div>
                        <MorphingDialogClose />
                      </MorphingDialogContent>
                    </MorphingDialog>
                    <p className='mt-0.5 font-mono text-[11.5px] text-stone-400'>#{r.id} · {(r.created_ts || '').slice(0, 16)}</p>
                  </div>
                  <span className={`shrink-0 rounded-full border px-2.5 py-0.5 font-mono text-[10.5px] uppercase ${r.review_status === 'approved' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : r.review_status === 'returned' ? 'border-red-200 bg-red-50 text-red-700' : 'border-seam bg-paper text-stone-500'}`}>
                    {r.review_status}
                  </span>
                </div>
                <p className='mt-2 line-clamp-1 font-mono text-[11.5px] text-stone-400'>{r.params_json}</p>
                <div className='mt-auto flex flex-wrap items-center gap-2 pt-3'>
                  <Link to={`/reports/${r.id}/review`}
                        className='flex items-center gap-1.5 rounded-lg border border-coal px-3 py-1.5 text-[12.5px] font-semibold text-coal transition-colors hover:bg-coal hover:text-white'>
                    <Eye className='h-3.5 w-3.5' /> Review
                  </Link>
                  <a href={`/reports/${r.id}/download`}
                     className='flex items-center gap-1.5 rounded-lg border border-seam px-3 py-1.5 text-[12.5px] font-medium text-stone-500 transition-colors hover:border-coal hover:text-coal'>
                    <Download className='h-3.5 w-3.5' /> DOCX
                  </a>
                </div>
              </article>
            </Tilt>
          ))}
        </AnimatedGroup>
      )}
    </div>
  );
}
