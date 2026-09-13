import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useScroll, useTransform, motion } from 'motion/react';
import {
  ArrowRight, ShieldCheck, FileCheck, Database,
  Sparkles, CheckCircle2, ChevronRight,
  Flame, Lock,
} from 'lucide-react';
import { InView } from '../../../components/motion/in-view.jsx';
import { TextEffect } from '../../../components/motion/text-effect.jsx';
import { TextShimmer } from '../../../components/motion/text-shimmer.jsx';
import { Magnetic } from '../../../components/motion/magnetic.jsx';
import { AnimatedNumber } from '../../../components/motion/animated-number.jsx';

const SAMPLE_QUERIES = [
  {
    id: 'production',
    label: 'CIL Production 2023-24',
    prompt: 'What was the total raw coal production of Coal India Limited in FY 2023-24?',
    answer: 'Coal India Limited achieved a record raw coal production of 997.83 MT in FY2023-24, reflecting a 10.1% year-on-year growth over 906.24 MT in the previous fiscal.',
    citation: {
      doc: 'Annual_Report_2024_25.pdf',
      location: 'page 11 · Table 3 · Cell C14',
      value: '997.83 MT',
      confidence: '99.4%',
      grade: 'Grade A',
    },
  },
  {
    id: 'offtake',
    label: 'Subsidiary Offtake',
    prompt: 'Compare coal offtake between Mahanadi Coalfields (MCL) and SECL.',
    answer: 'MCL recorded the highest subsidiary offtake at 198.40 MT, followed by SECL at 182.10 MT. Together they accounted for ~39.8% of total CIL offtake.',
    citation: {
      doc: 'Coal_Directory_2023_24.xlsx',
      location: 'sheet 4 · Row 28 · Col G',
      value: '198.40 MT / 182.10 MT',
      confidence: '98.8%',
      grade: 'Grade A',
    },
  },
  {
    id: 'washeries',
    label: 'Washery Yield & Ash',
    prompt: 'What was the clean coal yield across operational coking coal washeries?',
    answer: 'Operational coking washeries reported an average clean coal yield of 48.2% with clean coal ash controlled below 18.5%, matching metallurgical specifications.',
    citation: {
      doc: 'Washery_Performance_Review.pdf',
      location: 'page 4 · Section 2.1 · Table 1',
      value: '48.2% clean yield',
      confidence: '97.6%',
      grade: 'Grade A',
    },
  },
];

export function Hero({ stats }) {
  const [activeTab, setActiveTab] = useState(0);
  const activeQuery = SAMPLE_QUERIES[activeTab];

  const { scrollY } = useScroll();
  const heroOpacity = useTransform(scrollY, [0, 500], [1, 0.35]);
  const stageY = useTransform(scrollY, [0, 600], [0, 60]);

  return (
    <section
      id='hero'
      className='relative overflow-hidden bg-[#0c0a09] pt-20 pb-24 text-[#f5f5f4]'
      style={{ minHeight: '100dvh' }}
    >
      {/* ── Background Architectural Dot Grid ── */}
      <div
        className='pointer-events-none absolute inset-0 opacity-[0.22]'
        style={{
          backgroundImage:
            'radial-gradient(circle, rgba(234,138,12,0.4) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
        aria-hidden='true'
      />

      {/* ── Deep Amber Core Glow Orb ── */}
      <div
        className='pointer-events-none absolute -top-36 left-1/2 h-[34rem] w-[70rem] -translate-x-1/2 rounded-full blur-[130px]'
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(234,138,12,0.22) 0%, rgba(217,119,6,0.08) 45%, transparent 70%)',
        }}
        aria-hidden='true'
      />

      <motion.div style={{ opacity: heroOpacity }} className='relative mx-auto max-w-6xl px-5 md:px-8'>
        {/* ── Center Header Hierarchy ── */}
        <div className='mx-auto max-w-3xl text-center'>
          {/* Eyebrow badge */}
          <InView
            variants={{ hidden: { opacity: 0, y: -8 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.4 }}
          >
            <div className='inline-flex items-center gap-2 rounded-full border border-stone-800 bg-stone-900/90 px-3.5 py-1.5 backdrop-blur-md shadow-sm'>
              <span className='h-2 w-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)] animate-pulse' />
              <span className='font-mono text-[11px] font-medium tracking-wider text-stone-300 uppercase'>
                Offline Document Intelligence · CMPDI &amp; CIL
              </span>
            </div>
          </InView>

          {/* Main Headline */}
          <div className='mt-6'>
            <TextEffect
              as='h1'
              per='word'
              preset='fade-in-blur'
              delay={0.08}
              speedReveal={1.3}
              className='text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-[4rem] leading-[1.06]'
            >
              Every coal number.
            </TextEffect>
            <TextEffect
              as='h1'
              per='word'
              preset='fade-in-blur'
              delay={0.25}
              speedReveal={1.3}
              className='mt-1 text-4xl font-extrabold tracking-tight text-amber-500 sm:text-5xl md:text-6xl lg:text-[4rem] leading-[1.06]'
            >
              With its verified receipt.
            </TextEffect>
          </div>

          {/* Subtitle */}
          <InView
            variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.5, delay: 0.35 }}
          >
            <p className='mx-auto mt-5 max-w-2xl text-[15px] sm:text-[16px] leading-relaxed text-stone-400'>
              Turn thousands of geological exploration reports, washery workbooks, and parliamentary
              data into an air-gapped factual intelligence layer. Ask questions, compute trends with
              sandboxed Python, and cite exact page and cell coordinates.
            </p>
          </InView>

          {/* CTA Actions Bar */}
          <InView
            variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.5, delay: 0.45 }}
          >
            <div className='mt-8 flex flex-wrap items-center justify-center gap-3.5'>
              <Magnetic intensity={0.25} range={80}>
                <Link
                  to='/dashboard'
                  className='group flex items-center gap-2 rounded-xl bg-amber-500 px-6 py-3 text-[14px] font-semibold text-stone-950 shadow-[0_4px_20px_rgba(245,158,11,0.4)] transition-all hover:bg-amber-400 hover:shadow-[0_6px_25px_rgba(245,158,11,0.5)] active:scale-98'
                >
                  <span>Open the Workspace</span>
                  <ArrowRight className='h-4 w-4 transition-transform group-hover:translate-x-1' />
                </Link>
              </Magnetic>

              <a
                href='#product'
                className='flex items-center gap-2 rounded-xl border border-stone-800 bg-stone-900/80 px-5 py-3 text-[14px] font-medium text-stone-300 transition-colors hover:border-stone-700 hover:bg-stone-800 hover:text-white'
              >
                <span>Interactive Preview</span>
                <ChevronRight className='h-4 w-4 text-stone-500' />
              </a>
            </div>
          </InView>

          {/* Trust Guarantees */}
          <InView
            variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}
            transition={{ duration: 0.6, delay: 0.55 }}
          >
            <div className='mt-8 flex flex-wrap items-center justify-center gap-y-2 gap-x-6 text-[12px] text-stone-400'>
              <span className='flex items-center gap-1.5'>
                <Lock className='h-3.5 w-3.5 text-amber-500' />
                100% Air-Gapped / On-Device
              </span>
              <span className='flex items-center gap-1.5'>
                <ShieldCheck className='h-3.5 w-3.5 text-emerald-500' />
                Cell-Level Audit Provenance
              </span>
              <span className='flex items-center gap-1.5'>
                <Flame className='h-3.5 w-3.5 text-amber-500' />
                Zero Cloud Telemetry
              </span>
            </div>
          </InView>
        </div>

        {/* ── Interactive Command Center Stage ── */}
        <motion.div style={{ y: stageY }} className='relative mt-14'>
          <div className='relative overflow-hidden rounded-2xl border border-stone-800 bg-stone-950/90 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8)] backdrop-blur-xl'>

            {/* Window Titlebar */}
            <div className='flex items-center justify-between border-b border-stone-800/80 bg-stone-900/60 px-4 py-3'>
              <div className='flex items-center gap-2'>
                <span className='h-3 w-3 rounded-full bg-red-500/80' />
                <span className='h-3 w-3 rounded-full bg-yellow-500/80' />
                <span className='h-3 w-3 rounded-full bg-emerald-500/80' />
                <span className='ml-2 font-mono text-[11.5px] text-stone-400'>
                  CMPDI-Intelligence Fact-Engine v1.0
                </span>
              </div>
              <div className='flex items-center gap-2'>
                <span className='rounded-full border border-emerald-500/30 bg-emerald-950/50 px-2 py-0.5 font-mono text-[10px] uppercase font-semibold text-emerald-400'>
                  ● Local &amp; Ready
                </span>
              </div>
            </div>

            {/* Query Selector Tabs */}
            <div className='flex flex-wrap items-center gap-1.5 border-b border-stone-800/60 bg-stone-950/50 p-2.5 sm:px-4'>
              <span className='mr-1 font-mono text-[11px] uppercase tracking-wider text-stone-500'>
                Sample Prompt:
              </span>
              {SAMPLE_QUERIES.map((q, idx) => (
                <button
                  key={q.id}
                  onClick={() => setActiveTab(idx)}
                  className={`rounded-lg px-3 py-1.5 font-mono text-[11.5px] transition-all duration-150 ${activeTab === idx
                      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/40 font-semibold shadow-sm'
                      : 'text-stone-400 hover:bg-stone-900 hover:text-stone-200 border border-transparent'
                    }`}
                >
                  {q.label}
                </button>
              ))}
            </div>

            {/* Workspace Interactive Stage Content */}
            <div className='p-5 sm:p-7'>
              {/* User Prompt Bubble */}
              <div className='flex items-start gap-3'>
                <span className='flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-stone-800 font-mono text-xs font-bold text-stone-300'>
                  Q
                </span>
                <div className='flex-1 rounded-xl border border-stone-800 bg-stone-900/70 px-4 py-2.5 text-[14px] text-stone-200'>
                  {activeQuery.prompt}
                </div>
              </div>

              {/* Verified Output & Side-by-Side Receipt */}
              <div className='mt-5 grid grid-cols-1 gap-5 lg:grid-cols-12'>
                {/* Left: Answer */}
                <div className='lg:col-span-7 flex flex-col justify-between rounded-xl border border-stone-800/80 bg-stone-900/40 p-4 sm:p-5'>
                  <div>
                    <div className='flex items-center gap-2'>
                      <span className='flex h-6 w-6 items-center justify-center rounded-md bg-amber-500/20 text-amber-400'>
                        <Sparkles className='h-3.5 w-3.5' />
                      </span>
                      <span className='font-mono text-[11px] font-semibold uppercase tracking-wider text-amber-400'>
                        Cited Intelligence Response
                      </span>
                    </div>
                    <p className='mt-3 text-[14px] leading-relaxed text-stone-200'>
                      {activeQuery.answer}
                    </p>
                  </div>

                  <div className='mt-4 flex items-center justify-between border-t border-stone-800/60 pt-3 text-[11.5px]'>
                    <span className='flex items-center gap-1.5 text-emerald-400 font-mono'>
                      <CheckCircle2 className='h-3.5 w-3.5' /> Grounded against Library
                    </span>
                    <TextShimmer as='span' duration={2.4} className='font-mono text-[10.5px] text-stone-400'>
                      BM25 + Dense FAISS fusion
                    </TextShimmer>
                  </div>
                </div>

                {/* Right: Live Provenance Receipt Card */}
                <div className='lg:col-span-5 rounded-xl border border-amber-500/30 bg-gradient-to-b from-amber-500/10 via-stone-900/60 to-stone-950 p-4 sm:p-5 shadow-sm'>
                  <div className='flex items-center justify-between'>
                    <span className='font-mono text-[10px] uppercase tracking-wider text-amber-400 font-semibold'>
                      Verified Source Receipt
                    </span>
                    <span className='rounded-full border border-emerald-500/40 bg-emerald-950/60 px-2 py-0.5 font-mono text-[10px] text-emerald-400'>
                      {activeQuery.citation.grade}
                    </span>
                  </div>

                  <div className='mt-3 space-y-2 font-mono text-[11.5px]'>
                    <div className='flex items-center gap-2 text-stone-300'>
                      <FileCheck className='h-4 w-4 text-amber-400 shrink-0' />
                      <span className='truncate font-medium'>{activeQuery.citation.doc}</span>
                    </div>
                    <div className='rounded-lg border border-stone-800 bg-stone-950/70 p-2 text-stone-400 text-[11px]'>
                      <span className='text-stone-500'>Location:</span> {activeQuery.citation.location}
                    </div>
                  </div>

                  <div className='mt-3 flex items-center justify-between border-t border-stone-800/70 pt-2.5'>
                    <div>
                      <p className='text-[10px] uppercase font-mono text-stone-500'>Extracted Figure</p>
                      <p className='font-mono text-[15px] font-bold text-white'>{activeQuery.citation.value}</p>
                    </div>
                    <div className='text-right'>
                      <p className='text-[10px] uppercase font-mono text-stone-500'>Confidence</p>
                      <p className='font-mono text-[13px] font-bold text-emerald-400'>{activeQuery.citation.confidence}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Live Library Stats Bar Below Preview ── */}
          {(stats?.documents || stats?.facts) && (
            <div className='mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-xl border border-stone-800/80 bg-stone-950/60 p-4 backdrop-blur-md'>
              <div className='text-center sm:text-left sm:pl-3'>
                <p className='font-mono text-xl font-bold text-white'>
                  <AnimatedNumber value={stats?.documents ?? 0} />
                </p>
                <p className='font-mono text-[11px] text-stone-400 uppercase tracking-wider mt-0.5'>
                  Documents Indexed
                </p>
              </div>
              <div className='text-center sm:text-left sm:pl-3 border-l border-stone-800/70'>
                <p className='font-mono text-xl font-bold text-emerald-400'>
                  <AnimatedNumber value={stats?.facts ?? 0} />
                </p>
                <p className='font-mono text-[11px] text-stone-400 uppercase tracking-wider mt-0.5'>
                  Facts with Receipts
                </p>
              </div>
              <div className='text-center sm:text-left sm:pl-3 border-l border-stone-800/70'>
                <p className='font-mono text-xl font-bold text-amber-400'>
                  <AnimatedNumber value={stats?.chunks ?? 0} />
                </p>
                <p className='font-mono text-[11px] text-stone-400 uppercase tracking-wider mt-0.5'>
                  Vector Chunks
                </p>
              </div>
              <div className='text-center sm:text-left sm:pl-3 border-l border-stone-800/70'>
                <p className='font-mono text-xl font-bold text-stone-200'>0 KB</p>
                <p className='font-mono text-[11px] text-stone-400 uppercase tracking-wider mt-0.5'>
                  Data to External Cloud
                </p>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </section>
  );
}
