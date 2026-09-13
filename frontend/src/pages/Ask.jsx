import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { RefreshCw, X, FileText, MessageCircle, Send, ChevronDown, Sparkles } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Loading, ErrorBox } from '../components/ui.jsx';
import { Disclosure, DisclosureTrigger, DisclosureContent } from '../components/motion/disclosure.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { TextShimmer } from '../components/motion/text-shimmer.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';
import { motion, AnimatePresence } from 'motion/react';

const TOOL_LABEL = {
  search_documents: 'Searched Documents',
  get_facts: 'Queried Fact Index',
  run_python: 'Ran Python Analysis',
};

function mdLite(text) {
  const lines = String(text ?? '').split('\n');
  const inline = (s) =>
    s
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="rounded bg-paper px-1 font-mono text-[12.5px]">$1</code>')
      .replace(/\[E(\d+)\]/g, '<sup class="mx-0.5 rounded border border-coalline bg-coalsoft px-1 font-semibold text-coal">E$1</sup>');
  let html = '', inList = false, buf = [];
  const flush = () => { if (buf.length) { html += `<p class="mt-2">${buf.map(inline).join('<br>')}</p>`; buf = []; } };
  const closeList = () => { if (inList) { html += '</ul>'; inList = false; } };
  for (const line of lines) {
    const t = line.trim();
    if (/^#{1,6}\s/.test(t)) { flush(); closeList(); html += `<h3 class="mt-4 text-[15px] font-semibold">${inline(t.replace(/^#+\s/, ''))}</h3>`; }
    else if (/^[-*]\s/.test(t)) { buf.length && flush(); if (!inList) { html += '<ul class="mt-2 list-disc space-y-1 pl-5">'; inList = true; } html += `<li>${inline(t.replace(/^[-*]\s/, ''))}</li>`; }
    else if (t === '') { closeList(); flush(); }
    else { closeList(); buf.push(t); }
  }
  closeList(); flush();
  return { __html: html };
}

function EvidenceCard({ c, i }) {
  const loc = c.page_no ? `page ${c.page_no}` : c.sheet_no ? `sheet ${c.sheet_no}` : 'document';
  const isFact = c.content_type && c.content_type !== 'EVIDENCE';
  return (
    <div className={`rounded-lg border ${isFact ? 'border-emerald-200 bg-emerald-50/50' : 'border-seam bg-paper'} p-3 text-[12.5px]`}>
      <div className='flex items-center justify-between gap-2'>
        <span className={`flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest ${isFact ? 'text-emerald-700' : 'text-stone-400'}`}>
          {isFact ? '✓ verified evidence' : 'supporting evidence'}
          <sup className='rounded border border-coalline bg-coalsoft px-1 font-semibold text-coal'>E{i + 1}</sup>
        </span>
        <Link
          className='flex items-center gap-1 rounded-md border border-coal px-2 py-0.5 text-[11px] font-semibold text-coal transition-colors hover:bg-coal hover:text-white'
          to={`/doc/${c.doc_id}${c.page_no ? `/?page=${c.page_no}` : c.sheet_no ? `?sheet=${c.sheet_no}` : ''}`}
        >
          View Source →
        </Link>
      </div>
      <div className='mt-2 grid grid-cols-[64px_1fr] gap-x-2 gap-y-0.5'>
        <span className='text-stone-400'>Source</span><span className='truncate font-medium text-ink' title={c.doc_title}>{c.doc_title}</span>
        <span className='text-stone-400'>Location</span><span className='font-mono'>{loc}{c.content_type && c.content_type !== 'EVIDENCE' ? ` · ${String(c.content_type).toLowerCase()}` : ''}</span>
        {c.doc_type && <><span className='text-stone-400'>Type</span><span className='font-mono uppercase'>{c.doc_type}</span></>}
        {c.conf && <><span className='text-stone-400'>Confidence</span><span className='font-mono'>{c.conf}%</span></>}
      </div>
      {c.text && !isFact && <p className='mt-2 line-clamp-2 text-stone-500'>{String(c.text).slice(0, 200)}</p>}
    </div>
  );
}

function QualityBadge({ q }) {
  if (!q) return null;
  const color = q.level === 'HIGH' ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : q.level === 'LOW' ? 'border-red-200 bg-red-50 text-red-700'
    : 'border-coalline bg-coalsoft text-coal';
  const mark = (s) => (s === 'ok' ? <span className='text-emerald-600'>✓</span> : s === 'warn' ? <span className='text-coal'>⚠</span> : <span className='text-red-600'>✗</span>);
  return (
    <div className={`mb-3 rounded-lg border ${color} px-3 py-2`}>
      <Disclosure>
        <div className='flex flex-wrap items-center gap-2'>
          <span className='font-mono text-[10.5px] font-bold uppercase tracking-widest'>Evidence Quality: {q.level}</span>
          {q.conflicts > 0 && (
            <Link to='/conflicts' className={`rounded-full border ${color} px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide`}>
              {q.conflicts} conflict{q.conflicts !== 1 ? 's' : ''} →
            </Link>
          )}
          <DisclosureTrigger className='ml-auto font-mono text-[10.5px] uppercase tracking-wide opacity-70'>
            <span className='flex items-center gap-1'>details <ChevronDown className='h-3 w-3' /></span>
          </DisclosureTrigger>
        </div>
        <DisclosureContent className='mt-2 space-y-1 text-left text-[12px] normal-case'>
          {(q.checks || []).map((c, i) => <div key={i} className='flex items-center gap-1.5'>{mark(c[0])}<span>{c[1]}</span></div>)}
        </DisclosureContent>
      </Disclosure>
    </div>
  );
}

function WhyPanel({ w }) {
  if (!w) return null;
  const row = (k, v) => <div className='flex justify-between gap-3'><dt className='text-stone-400'>{k}</dt><dd className='font-mono text-[11.5px] text-stone-600'>{String(v)}</dd></div>;
  return (
    <Disclosure className='mt-3 rounded-lg border border-seam bg-paper px-3 py-2'>
      <DisclosureTrigger className='font-mono text-[10.5px] uppercase tracking-widest text-stone-400'>
        <span>Why this answer?</span><ChevronDown className='h-3.5 w-3.5' />
      </DisclosureTrigger>
      <DisclosureContent>
        <dl className='mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-[12px]'>
          {row('Query type', w.route)}
          {row('Chunks retrieved', w.chunks_retrieved)}
          {row('Documents represented', w.documents_represented)}
          {w.facts_matched !== undefined && row('Facts matched', w.facts_matched)}
          {w.computations !== undefined && row('Computations run', w.computations)}
          {row('Sources cited', w.sources_cited)}
          {row('Conflicts', w.conflicts)}
          {row('LLM', w.llm)}
          {row('Generation', w.generation)}
        </dl>
      </DisclosureContent>
    </Disclosure>
  );
}

function TracePanel({ trace }) {
  if (!trace?.length) return null;
  const n = trace.filter((s) => s.type === 'tool').length;
  return (
    <Disclosure className='mb-3 rounded-lg border border-seam bg-paper px-3 py-2'>
      <DisclosureTrigger className='font-mono text-[10.5px] uppercase tracking-wide text-stone-400'>
        <span>How this was answered · {n} step{n === 1 ? '' : 's'}</span><ChevronDown className='h-3.5 w-3.5' />
      </DisclosureTrigger>
      <DisclosureContent>
        <div className='mt-2 space-y-1.5 border-l-2 border-coalline pl-3'>
          {trace.map((s, i) => s.type === 'thought' ? (
            <p key={i} className='text-[12.5px] leading-relaxed text-stone-500'>{s.text}</p>
          ) : s.type === 'tool' ? (
            <p key={i} className='font-mono text-[11px] uppercase tracking-wide text-stone-400'>{TOOL_LABEL[s.tool] || s.tool}</p>
          ) : null)}
        </div>
      </DisclosureContent>
    </Disclosure>
  );
}

export default function Ask() {
  const [params] = useSearchParams();
  const qs = new URLSearchParams();
  for (const k of ['doc', 'docs', 'q']) if (params.get(k)) qs.set(k, params.get(k));
  const { data, error } = usePageData(`/api/pages/ask${qs.toString() ? `?${qs}` : ''}`);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const historyRef = useRef([]);
  const logRef = useRef(null);
  const inputRef = useRef(null);
  const scopedDocIds = (data?.scoped_docs || []).map((d) => d.id);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages, busy]);

  const send = async (textArg) => {
    const text = (textArg ?? input).trim();
    if (!text || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text }]);
    historyRef.current.push({ role: 'user', content: text });
    setBusy(true);
    try {
      const payload = await postJSON('/api/chat', {
        messages: historyRef.current,
        doc_ids: scopedDocIds,
      });
      setMessages((m) => [...m, { role: 'assistant', payload }]);
      historyRef.current.push({ role: 'assistant', content: payload.answer || '' });
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', error: e.message }]);
    }
    setBusy(false);
    inputRef.current?.focus();
  };

  const downloadReport = async (runRowId, btn) => {
    btn.disabled = true;
    try {
      const { download } = await postJSON('/api/agent/report', { run_id: runRowId });
      window.location.href = download;
    } catch (e) {
      window.alert(e.message);
    }
    btn.disabled = false;
  };

  const seeded = useRef(false);
  useEffect(() => {
    if (!seeded.current && data?.seed_q) {
      seeded.current = true;
      send(data.seed_q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const scoped = data.scoped_docs;
  const pills = scoped.length
    ? ['What was the production reported here?', 'What mines are mentioned?', 'Summarize the key findings.', 'What reserves are reported?']
    : ['raw coal production of CIL in 2023-24', 'compare production across subsidiaries', 'generate charts for this data', 'what does the library say about washeries?'];

  return (
    <div className='flex h-[calc(100dvh-7rem)] flex-col'>

      {/* Header */}
      <div className='flex shrink-0 items-center justify-between gap-3 border-b border-seam pb-3'>
        <div className='flex items-center gap-2.5'>
          <span className='flex h-8 w-8 items-center justify-center rounded-lg bg-coalsoft text-coal'>
            <MessageCircle className='h-[18px] w-[18px]' />
          </span>
          <div>
            <h1 className='text-[15px] font-semibold leading-none tracking-tight'>Ask</h1>
            <p className='mt-0.5 text-[12px] text-stone-400'>Cited answers · fact index · analytical agent</p>
          </div>
        </div>
        <button
          title='New conversation'
          onClick={() => { historyRef.current = []; setMessages([]); window.location.href = '/ask'; }}
          className='flex shrink-0 items-center gap-1.5 rounded-lg border border-seam px-3 py-1.5 text-[12px] font-medium text-stone-500 transition-colors hover:border-coal hover:text-coal'
        >
          <RefreshCw className='h-3.5 w-3.5' /> New chat
        </button>
      </div>

      {/* Scoped docs banner */}
      <AnimatePresence>
        {scoped.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className='mt-2 flex shrink-0 flex-wrap items-center gap-2 rounded-xl border border-coalline bg-coalsoft px-4 py-2 text-[12.5px]'
          >
            <span className='font-mono text-[10px] uppercase tracking-widest text-coal'>Scoped to</span>
            {scoped.map((d) => (
              <span key={d.id} className='inline-flex items-center gap-1.5 rounded-full border border-coalline bg-white px-2.5 py-0.5 text-[11.5px] text-stone-600'>
                <FileText className='h-3 w-3 text-coal' /> {d.display_name || d.filename}
              </span>
            ))}
            <Link to='/ask' className='ml-auto flex items-center gap-1 text-[12px] font-medium text-coal hover:underline'>
              <X className='h-3.5 w-3.5' /> clear
            </Link>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Message log */}
      <div ref={logRef} className='mt-4 flex-1 space-y-4 overflow-y-auto pr-1' aria-live='polite'>

        {messages.length === 0 && !busy && (
          <div className='mx-auto flex max-w-lg flex-col items-center pt-10 text-center'>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', bounce: 0.4, duration: 0.6 }}
              className='flex h-16 w-16 items-center justify-center rounded-2xl bg-coalsoft text-coal'
            >
              <Sparkles className='h-8 w-8' />
            </motion.div>
            <h2 className='mt-5 text-[16px] font-semibold'>Ask anything about your documents</h2>
            <p className='mt-1.5 max-w-[38ch] text-[13.5px] text-stone-500'>
              Factual questions get cited answers. Analytical questions get computed results and charts.
            </p>
            <AnimatedGroup preset='fade' className='mt-6 flex flex-wrap justify-center gap-2'>
              {pills.map((p) => (
                <button
                  key={p}
                  onClick={() => send(p)}
                  className='rounded-full border border-seam bg-white px-3.5 py-1.5 text-[12.5px] text-stone-600 shadow-card transition-all hover:-translate-y-px hover:border-coal hover:text-coal'
                >
                  {p}
                </button>
              ))}
            </AnimatedGroup>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((m, i) =>
            m.role === 'user' ? (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className='flex justify-end'
              >
                <div className='max-w-[75%] rounded-2xl rounded-br-sm bg-coal px-4 py-3 text-[14px] leading-relaxed text-white shadow-card'>
                  {m.text}
                </div>
              </motion.div>
            ) : m.error ? (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className='flex'
              >
                <div className='max-w-[85%] rounded-2xl rounded-tl-sm border border-red-200 bg-red-50 px-4 py-3'>
                  <p className='text-[13.5px] text-red-700'>{m.error}</p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className='flex gap-3'
              >
                <div className='mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-coalsoft text-coal'>
                  <Sparkles className='h-3.5 w-3.5' />
                </div>
                <div className='min-w-0 flex-1 rounded-2xl rounded-tl-sm border border-seam bg-white p-4 shadow-card'>
                  <TracePanel trace={m.payload.trace} />
                  <QualityBadge q={m.payload.quality} />
                  <div
                    className='text-[14px] leading-relaxed text-stone-700'
                    dangerouslySetInnerHTML={mdLite(m.payload.abstained ? m.payload.answer || 'Insufficient evidence.' : m.payload.answer || '')}
                  />
                  {(m.payload.charts || []).map((src) => (
                    <div key={src} className='mt-4'>
                      <img src={src} className='max-h-[420px] w-auto rounded-xl border border-seam shadow-card' alt='Chart' />
                    </div>
                  ))}
                  {(m.payload.citations || []).length > 0 && (
                    <div className='mt-4 border-t border-seam pt-3'>
                      <p className='font-mono text-[10px] uppercase tracking-widest text-stone-400'>source coverage</p>
                      <div className='mt-1.5 grid gap-2 sm:grid-cols-2'>
                        {m.payload.citations.map((c, ci) => <EvidenceCard key={ci} c={c} i={ci} />)}
                      </div>
                    </div>
                  )}
                  <WhyPanel w={m.payload.why} />
                  {m.payload.mode === 'agent' && m.payload.run_row_id && (
                    <button
                      onClick={(e) => downloadReport(m.payload.run_row_id, e.currentTarget)}
                      className='mt-3 flex items-center gap-2 rounded-lg border border-coal px-3 py-1.5 text-[12.5px] font-semibold text-coal transition-colors hover:bg-coal hover:text-white'
                    >
                      Generate DOCX Report
                    </button>
                  )}
                  {(m.payload.alternatives || []).length > 0 && (
                    <div className='mt-3 rounded-lg border border-coalline bg-coalsoft px-3 py-2.5 text-[12.5px] text-stone-600'>
                      <strong className='text-coal'>Also reported elsewhere:</strong>{' '}
                      {m.payload.alternatives.map((a) => (
                        <span key={a.filename}>
                          <span className='font-mono'>{String(a.fact_values?.[0]?.value_raw ?? '')}</span> ({a.filename})
                        </span>
                      )).reduce((acc, x) => [acc, ', '], [])}
                    </div>
                  )}
                </div>
              </motion.div>
            )
          )}
        </AnimatePresence>

        {/* Typing indicator */}
        {busy && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className='flex gap-3'
          >
            <div className='mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-coalsoft text-coal'>
              <Sparkles className='h-3.5 w-3.5' />
            </div>
            <div className='flex items-center gap-3 rounded-2xl rounded-tl-sm border border-seam bg-white px-4 py-3 shadow-card'>
              <span className='flex gap-1'>
                {[0, 1, 2].map((n) => (
                  <span key={n} className='h-1.5 w-1.5 animate-bounce rounded-full bg-coal' style={{ animationDelay: `${n * 150}ms` }} />
                ))}
              </span>
              <TextShimmer as='span' duration={2} className='text-[13px] text-stone-500'>
                Looking through the library…
              </TextShimmer>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input bar */}
      <form
        onSubmit={(e) => { e.preventDefault(); send(); }}
        className='mt-3 shrink-0'
      >
        <div className='relative flex items-end gap-2 rounded-2xl border border-seam bg-white p-2 shadow-card transition-colors focus-within:border-coal/60'>
          <textarea
            ref={inputRef}
            rows='1'
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
            }}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder='Ask about production, reserves, offtake… or request charts and analysis'
            className='flex-1 resize-none bg-transparent py-1.5 pl-2 pr-2 text-[14px] leading-relaxed placeholder:text-stone-400 focus:outline-none'
          />
          <Magnetic intensity={0.35} range={60}>
            <button
              type='submit'
              title='Send (Enter)'
              disabled={busy || !input.trim()}
              className='flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-coal text-white transition-all hover:opacity-90 active:scale-95 disabled:opacity-30'
            >
              <Send className='h-4 w-4' />
            </button>
          </Magnetic>
        </div>
        <p className='mt-1.5 text-center font-mono text-[10.5px] uppercase tracking-widest text-stone-400'>
          Answers cite sources · figures resolve from the fact index
        </p>
      </form>
    </div>
  );
}
