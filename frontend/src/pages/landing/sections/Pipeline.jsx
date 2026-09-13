import { Upload, ScanText, Database, MessageCircle } from 'lucide-react';
import { InView } from '../../../components/motion/in-view.jsx';
import { TextEffect } from '../../../components/motion/text-effect.jsx';
import { AnimatedGroup } from '../../../components/motion/animated-group.jsx';

const STEPS = [
  {
    num: '01',
    name: 'Ingest',
    Icon: Upload,
    text: 'PDFs, Word, Excel, CSV and scans land in a content-addressed store, deduplicated by SHA-256.',
  },
  {
    num: '02',
    name: 'Extract',
    Icon: ScanText,
    text: 'OCR, ruled-table detection and section structure become one canonical model per document.',
  },
  {
    num: '03',
    name: 'Index',
    Icon: Database,
    text: 'Chunks, embeddings, tags and a numeric fact index — all stored in local SQLite + FAISS.',
  },
  {
    num: '04',
    name: 'Answer',
    Icon: MessageCircle,
    text: 'Chat, charts and DOCX reports that cite the page, table and cell they came from.',
  },
];

export function Pipeline() {
  return (
    <section id='pipeline' className='bg-side text-sidetext'>
      <div className='mx-auto max-w-6xl px-5 py-24 md:px-8 md:py-28'>
        {/* Header row: left heading + right subtext — different from centered pattern above */}
        <InView className='grid gap-8 md:grid-cols-2 md:items-end'>
          <TextEffect
            as='h2'
            per='word'
            preset='fade-in-blur'
            className='text-3xl font-bold tracking-[-0.025em] text-sidetext md:text-[2.6rem]'
          >
            From file to citation, in one unbroken chain.
          </TextEffect>
          <p className='text-[14.5px] leading-relaxed text-sidemute md:max-w-[44ch]'>
            Nothing downstream ever touches the raw file. The stored original is
            the source of truth; every index is rebuildable from it — so a receipt
            is never a promise, it is a path you can walk.
          </p>
        </InView>

        {/* Step cards */}
        <div className='relative mt-14'>
          {/* Connecting dashed line */}
          <InView
            variants={{ hidden: { scaleX: 0 }, visible: { scaleX: 1 } }}
            transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            className='absolute left-0 right-0 top-[44px] hidden origin-left border-t border-dashed border-sideline md:block'
            aria-hidden='true'
          >
            <span />
          </InView>

          <AnimatedGroup
            preset='blur-slide'
            as='ol'
            className='grid gap-4 md:grid-cols-4'
          >
            {STEPS.map(({ num, name, Icon, text }) => (
              <li
                key={num}
                className='group relative rounded-2xl border border-sideline bg-sidecard/40 p-6 transition-all duration-300 hover:border-coal/40 hover:bg-sidecard/80 hover:shadow-[0_8px_24px_-6px_rgb(0_0_0/0.35)]'
              >
                <div className='flex items-center justify-between'>
                  <span className='flex h-[44px] w-[44px] items-center justify-center rounded-xl bg-side text-sidemute ring-1 ring-sideline transition-all duration-300 group-hover:bg-coal group-hover:text-white group-hover:ring-coal'>
                    <Icon className='h-5 w-5' />
                  </span>
                  <span className='font-mono text-[10px] font-semibold tracking-widest text-sideline'>
                    {num}
                  </span>
                </div>
                <p className='mt-5 text-[15px] font-semibold text-sidetext'>{name}</p>
                <p className='mt-2 text-[13px] leading-relaxed text-sidemute'>{text}</p>
              </li>
            ))}
          </AnimatedGroup>
        </div>
      </div>
    </section>
  );
}
