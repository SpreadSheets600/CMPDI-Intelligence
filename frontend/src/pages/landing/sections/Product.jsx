import { ChartColumn, CircleCheck, ExternalLink } from 'lucide-react';
import { motion } from 'motion/react';
import { InView } from '../../../components/motion/in-view.jsx';
import { TextEffect } from '../../../components/motion/text-effect.jsx';
import { Tilt } from '../../../components/motion/tilt.jsx';
import { Spotlight } from '../../../components/motion/spotlight.jsx';

const SOURCES = [
  { name: 'Annual Report 2024-25', loc: 'page 11 · table 3', conf: '98%', grade: 'A' },
  { name: 'Coal Directory 2023-24', loc: 'sheet 4 · row 12', conf: '96%', grade: 'A' },
  { name: 'MCL Performance Review', loc: 'page 34', conf: '91%', grade: 'B' },
];

const BARS = [38, 52, 44, 66, 58, 80, 100];

export function Product() {
  return (
    <section id='product' className='relative py-24 md:py-32'>
      <div className='mx-auto max-w-6xl px-5 md:px-8'>
        {/* Section header — left-aligned asymmetric layout */}
        <InView className='max-w-2xl'>
          <TextEffect
            as='h2'
            per='word'
            preset='fade-in-blur'
            className='text-3xl font-bold tracking-[-0.025em] md:text-[2.6rem]'
          >
            Ask the library. Get the answer and its paper trail.
          </TextEffect>
          <p className='mt-4 max-w-[58ch] text-[15px] leading-relaxed text-stone-500'>
            One question. Grounded numbers. Every figure linked to the page,
            table and cell where it was printed.
          </p>
        </InView>

        <InView
          variants={{ hidden: { opacity: 0, y: 28 }, visible: { opacity: 1, y: 0 } }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className='relative mx-auto mt-12 max-w-4xl'
        >
          {/* Outer glow */}
          <div
            className='absolute -inset-8 rounded-[2rem] opacity-60 blur-2xl'
            style={{ background: 'radial-gradient(ellipse at center, rgba(var(--c-coal)/0.08), transparent 70%)' }}
            aria-hidden='true'
          />

          <Tilt rotationFactor={2.5}>
            {/* Browser chrome */}
            <div className='relative rounded-2xl border border-seam bg-white shadow-lift overflow-hidden'>
              {/* Title bar */}
              <div className='flex items-center gap-2 border-b border-seam bg-paper px-4 py-3'>
                <span className='h-2.5 w-2.5 rounded-full bg-seam' />
                <span className='h-2.5 w-2.5 rounded-full bg-seam' />
                <span className='h-2.5 w-2.5 rounded-full bg-coal/50' />
                <span className='ml-3 flex-1 rounded-md border border-seam bg-white px-2.5 py-1 font-mono text-[10.5px] text-stone-400'>
                  cmpdi-intel · 127.0.0.1/ask
                </span>
                <span className='flex items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-wide text-emerald-700'>
                  <span className='h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600' />
                  offline
                </span>
              </div>

              {/* Chat body */}
              <div className='p-6 md:p-8'>
                {/* User message */}
                <div className='flex justify-end'>
                  <p className='max-w-[46ch] rounded-2xl rounded-br-sm bg-side px-4 py-3 text-[14px] text-sidetext'>
                    Raw coal production of CIL in 2023-24 — and how did offtake move across subsidiaries?
                  </p>
                </div>

                {/* AI response */}
                <div className='mt-5 max-w-[62ch]'>
                  <p className='text-[14.5px] leading-relaxed text-stone-600'>
                    Coal India Limited reported raw coal production of{' '}
                    <strong className='font-mono text-ink'>997.83 MT</strong>
                    <a
                      href='#'
                      onClick={(e) => e.preventDefault()}
                      className='mx-1 inline-flex items-center gap-1 rounded-md border border-coalline bg-coalsoft px-2 py-0.5 align-middle font-mono text-[10.5px] text-coal transition-colors hover:bg-coal hover:text-white'
                    >
                      FY2023-24 · p.11
                    </a>
                    , against an offtake of{' '}
                    <strong className='font-mono text-ink'>957.11 MT</strong>
                    <a
                      href='#'
                      onClick={(e) => e.preventDefault()}
                      className='mx-1 inline-flex items-center gap-1 rounded-md border border-coalline bg-coalsoft px-2 py-0.5 align-middle font-mono text-[10.5px] text-coal transition-colors hover:bg-coal hover:text-white'
                    >
                      Coal Directory · sheet 4
                    </a>
                    . Mahanadi Coalfields led subsidiary offtake
                    <a
                      href='#'
                      onClick={(e) => e.preventDefault()}
                      className='ml-1 inline-flex items-center gap-1 rounded-md border border-coalline bg-coalsoft px-2 py-0.5 align-middle font-mono text-[10.5px] text-coal transition-colors hover:bg-coal hover:text-white'
                    >
                      p.34
                    </a>
                    .
                  </p>

                  {/* Source cards */}
                  <div className='mt-5 grid gap-2.5 sm:grid-cols-3'>
                    {SOURCES.map((src) => (
                      <Spotlight
                        key={src.name}
                        className='rounded-xl border border-seam bg-paper p-3 transition-colors hover:border-coalline'
                      >
                        <div className='flex items-center justify-between'>
                          <span className='font-mono text-[9px] uppercase tracking-wide text-stone-400'>
                            source
                          </span>
                          <span className='flex h-4.5 w-4.5 items-center justify-center rounded bg-coalsoft font-mono text-[9px] font-semibold text-coal'>
                            {src.grade}
                          </span>
                        </div>
                        <p className='mt-1 text-[12px] font-semibold leading-snug'>{src.name}</p>
                        <p className='mt-0.5 font-mono text-[10px] text-stone-400'>
                          {src.loc} · {src.conf}
                        </p>
                        <p className='mt-1.5 flex items-center gap-1 text-[10.5px] font-medium text-coal'>
                          <ExternalLink className='h-2.5 w-2.5' /> View source
                        </p>
                      </Spotlight>
                    ))}
                  </div>

                  {/* Metadata pills */}
                  <div className='mt-3.5 flex flex-wrap items-center gap-2'>
                    <span className='rounded-full border border-coalline bg-coalsoft px-3 py-1 font-mono text-[10px] text-coal'>
                      Why this answer?
                    </span>
                    <span className='rounded-full border border-seam px-3 py-1 font-mono text-[10px] text-stone-500'>
                      3 sources · 2 independent documents
                    </span>
                    <span className='rounded-full border border-seam px-3 py-1 font-mono text-[10px] text-stone-500'>
                      no conflicts on this figure
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Tilt>

          {/* Floating chart badge */}
          <motion.div
            animate={{ y: [0, -9, 0] }}
            transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
            className='absolute -bottom-10 -left-2 hidden w-52 rounded-xl border border-seam bg-white p-3.5 shadow-lift md:block lg:-left-14'
          >
            <p className='flex items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-wide text-stone-400'>
              <ChartColumn className='h-3 w-3 text-coal' /> computed, not guessed
            </p>
            <div className='mt-2.5 flex h-16 items-end gap-1' aria-hidden='true'>
              {BARS.map((h, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-t transition-all ${i === BARS.length - 1 ? 'bg-coal' : 'border border-coalline bg-coalsoft'}`}
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
            <p className='mt-2 font-mono text-[10px] text-stone-500'>offtake trend</p>
          </motion.div>

          {/* Floating weak-evidence badge */}
          <motion.div
            animate={{ y: [0, -7, 0] }}
            transition={{ duration: 9, repeat: Infinity, ease: 'easeInOut', delay: 1.4 }}
            className='absolute -top-8 -right-2 hidden rounded-xl border border-seam bg-white px-3.5 py-2.5 shadow-lift md:block lg:-right-12'
          >
            <p className='flex items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-wide text-stone-400'>
              <CircleCheck className='h-3 w-3 text-emerald-600' /> weak evidence
            </p>
            <p className='mt-1 max-w-[22ch] text-[12px] font-semibold text-ink'>
              "I can't support that from the library."
            </p>
          </motion.div>
        </InView>
      </div>
    </section>
  );
}
