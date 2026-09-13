import { Link } from 'react-router-dom';
import {
  MessageCircle, FileChartColumn, TriangleAlert,
  ChartColumn, Network, Shapes, ScanText, Check,
} from 'lucide-react';
import { InView } from '../../../components/motion/in-view.jsx';
import { TextEffect } from '../../../components/motion/text-effect.jsx';
import { Tilt } from '../../../components/motion/tilt.jsx';
import { Spotlight } from '../../../components/motion/spotlight.jsx';
import { motion } from 'motion/react';

// ─── Bento layout ────────────────────────────────────────────────────────────
// Row 1: Ask hero (col-span-4, row-span-2) │ Report studio (col-span-2)
//                                          │ Conflict radar (col-span-2)
// Row 2: Insights (col-span-2) │ Knowledge (col-span-2) │ Topics (col-span-2)
// Row 3: Full-width "built for real paperwork" bar

const FEATURE_CARDS = [
  {
    title: 'Report studio',
    Icon: FileChartColumn,
    text: 'DOCX reports assembled from the library — real Word tables, charts from actual figures, per-item sources appendix. Human review decides approve or return.',
    cardCls: 'border-seam bg-white',
    iconCls: 'bg-coalsoft text-coal',
    col: 'md:col-span-2',
  },
  {
    title: 'Conflict radar',
    Icon: TriangleAlert,
    text: 'When documents disagree on the same figure, every value is shown side by side with its receipt — status tracked open to resolved.',
    cardCls: 'border-sideline bg-side',
    iconCls: 'bg-sidecard text-sidemute',
    titleCls: 'text-sidetext',
    textCls: 'text-sidemute',
    col: 'md:col-span-2',
  },
  {
    title: 'Insights',
    Icon: ChartColumn,
    text: 'Any reported metric plotted per year — every bar links to the document it came from.',
    cardCls: 'border-seam bg-white',
    iconCls: 'bg-coalsoft text-coal',
    col: 'md:col-span-2',
  },
  {
    title: 'Knowledge tree',
    Icon: Network,
    text: 'Documents, tags and entities as a navigable force-directed graph of your corpus.',
    cardCls: 'border-coalline bg-coalsoft',
    iconCls: 'bg-coal text-white',
    textCls: 'text-stone-600',
    col: 'md:col-span-2',
  },
  {
    title: 'Topics & tags',
    Icon: Shapes,
    text: 'Word clouds, keyphrases and document clusters computed locally, fed back into search and filters.',
    cardCls: 'border-seam bg-white',
    iconCls: 'bg-coalsoft text-coal',
    col: 'md:col-span-2',
  },
];

const CHECK_ITEMS = [
  'lakh / crore aware', 'MT · GCV · % units',
  'April-start fiscal years', 'OCR confidence quarantine',
  'revised-report chains', 'SHA-256 duplicate rejection',
];

// Stagger variant for each grid cell — replaces AnimatedGroup so we can
// apply col-span directly on the motion element.
const cellVariants = {
  hidden: { opacity: 0, y: 14, filter: 'blur(6px)' },
  show:   { opacity: 1, y: 0,  filter: 'blur(0px)' },
};

export function Capabilities() {
  return (
    <section id='capabilities' className='py-24 md:py-28'>
      <div className='mx-auto max-w-6xl px-5 md:px-8'>

        {/* Header */}
        <InView className='flex flex-wrap items-end justify-between gap-6'>
          <TextEffect
            as='h2'
            per='word'
            preset='fade-in-blur'
            className='max-w-[22ch] text-3xl font-bold tracking-[-0.025em] md:text-[2.6rem]'
          >
            One workspace that reads the library for you.
          </TextEffect>
          <Link
            to='/dashboard'
            className='flex items-center gap-1.5 text-[13.5px] font-semibold text-coal transition-opacity hover:opacity-70'
          >
            Try it now →
          </Link>
        </InView>

        {/* Bento grid — stagger applied per-cell so col-span survives */}
        <motion.div
          initial='hidden'
          whileInView='show'
          viewport={{ once: true, amount: 0.1 }}
          transition={{ staggerChildren: 0.07 }}
          className='mt-10 grid gap-3 md:grid-cols-6'
        >
          {/* ── Ask: hero cell (col-span-4, row-span-2) ── */}
          <motion.div
            variants={cellVariants}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className='md:col-span-4 md:row-span-2'
          >
            <Tilt rotationFactor={3} className='h-full'>
              <div className='group h-full rounded-2xl border border-seam bg-white p-7 transition-all duration-300 hover:shadow-lift'>
                <div className='flex h-11 w-11 items-center justify-center rounded-xl bg-coal text-white transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105'>
                  <MessageCircle className='h-5 w-5' />
                </div>
                <h3 className='mt-5 text-xl font-semibold tracking-tight'>
                  Ask, with grounded answers
                </h3>
                <p className='mt-3 max-w-[52ch] text-[14px] leading-relaxed text-stone-500'>
                  One chat over the whole library. Numbers resolve against a fact index
                  for exact values; when a question needs analysis, a tool-calling agent
                  runs sandboxed Python over the real data — comparisons, shares and
                  trends are computed, never guessed. Every claim carries its citation,
                  and when evidence is weak the system abstains instead of inventing.
                </p>
                <div className='mt-6 flex flex-wrap gap-2'>
                  {[
                    '"raw coal production of CIL in 2023-24?"',
                    '"compare offtake across subsidiaries"',
                    '"chart the GCV trend since 2019"',
                  ].map((t) => (
                    <span
                      key={t}
                      className='rounded-full border border-coalline bg-coalsoft px-3 py-1.5 font-mono text-[10.5px] text-coal'
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </Tilt>
          </motion.div>

          {/* ── Small feature cells ── */}
          {FEATURE_CARDS.map(({ title, Icon, text, cardCls, iconCls, col, textCls, titleCls }) => (
            <motion.div
              key={title}
              variants={cellVariants}
              transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
              className={col}
            >
              <Tilt rotationFactor={5} className='h-full'>
                <Spotlight
                  className={`group h-full rounded-2xl border p-5 transition-all duration-300 hover:shadow-lift ${cardCls}`}
                >
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105 ${iconCls}`}
                  >
                    <Icon className='h-[18px] w-[18px]' />
                  </div>
                  <h3 className={`mt-4 text-[15px] font-semibold tracking-tight ${titleCls ?? ''}`}>
                    {title}
                  </h3>
                  <p className={`mt-1.5 text-[13px] leading-relaxed ${textCls ?? 'text-stone-500'}`}>
                    {text}
                  </p>
                </Spotlight>
              </Tilt>
            </motion.div>
          ))}

          {/* ── Full-width "built for real paperwork" bar ── */}
          <motion.div
            variants={cellVariants}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className='md:col-span-6'
          >
            <Tilt rotationFactor={2} className='h-full'>
              <div className='h-full rounded-2xl border border-coalline bg-coalsoft p-6 transition-all duration-300 hover:shadow-lift'>
                <div className='flex flex-wrap items-start gap-x-12 gap-y-5'>
                  <div className='max-w-[54ch]'>
                    <div className='flex h-10 w-10 items-center justify-center rounded-xl bg-coal text-white'>
                      <ScanText className='h-[18px] w-[18px]' />
                    </div>
                    <h3 className='mt-4 text-[15px] font-semibold tracking-tight'>
                      Built for real paperwork, not demo data
                    </h3>
                    <p className='mt-1.5 text-[13.5px] leading-relaxed text-stone-600'>
                      Indian number formats, lakh/crore and MT units, fiscal years starting
                      April, OCR with confidence quarantine, automatic version chains for
                      revised reports, SHA-256 duplicate rejection — tested against live
                      reports from coal.gov.in.
                    </p>
                  </div>
                  <div className='grid flex-1 grid-cols-2 gap-x-6 gap-y-2 self-center font-mono text-[11.5px] text-stone-600'>
                    {CHECK_ITEMS.map((line) => (
                      <span key={line} className='flex items-center gap-2'>
                        <Check className='h-3.5 w-3.5 shrink-0 text-coal' />
                        {line}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </Tilt>
          </motion.div>
        </motion.div>

      </div>
    </section>
  );
}
