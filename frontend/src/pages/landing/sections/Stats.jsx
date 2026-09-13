import { InView } from '../../../components/motion/in-view.jsx';
import { AnimatedNumber } from '../../../components/motion/animated-number.jsx';
import { InfiniteSlider } from '../../../components/motion/infinite-slider.jsx';

const FORMATS = [
  'Digital PDF', 'Scanned PDF + OCR', 'Word documents', 'Excel workbooks',
  'Multi-sheet CSV', 'Parliamentary replies', 'Image-only pages', 'SHA-256 dedupe',
  'Version chains', 'Indian number formats',
];

export function Stats({ stats }) {
  const items = [
    { label: 'Documents indexed', value: stats?.documents ?? null },
    { label: 'Facts with receipts', value: stats?.facts ?? null },
    { label: 'Searchable chunks', value: stats?.chunks ?? null },
    { label: 'Bytes to the cloud', value: 0 },
  ];

  return (
    <section className='border-y border-seam bg-white'>
      {/* Stat grid */}
      <div className='mx-auto grid max-w-6xl grid-cols-2 gap-y-8 px-5 py-10 md:grid-cols-4 md:px-8 md:py-12'>
        {items.map(({ label, value }, i) => (
          <InView
            key={label}
            variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className='px-4 text-center'
          >
            <div className='font-mono text-3xl font-semibold tracking-tight tabular-nums text-ink md:text-4xl'>
              {value === 0 ? (
                <span className='text-coal'>0</span>
              ) : value == null ? (
                <span className='text-stone-300'>—</span>
              ) : (
                <AnimatedNumber value={value} />
              )}
            </div>
            <div className='mt-1.5 text-[12px] text-stone-500'>{label}</div>
          </InView>
        ))}
      </div>

      {/* Format ticker */}
      <div className='overflow-hidden border-t border-seam py-3'>
        <InfiniteSlider gap={48} speed={55} speedOnHover={12}>
          {FORMATS.map((f) => (
            <span
              key={f}
              className='flex items-center gap-10 font-mono text-[10.5px] uppercase tracking-[0.18em] text-stone-400'
            >
              <span className='whitespace-nowrap'>{f}</span>
              <span className='text-coal/60'>·</span>
            </span>
          ))}
        </InfiniteSlider>
      </div>
    </section>
  );
}
