import { useState } from 'react';
import { useScroll, useMotionValueEvent, motion } from 'motion/react';
import { ArrowRight } from 'lucide-react';
import { Magnetic } from '../../../components/motion/magnetic.jsx';
import { TextLoop } from '../../../components/motion/text-loop.jsx';

const NAV_LINKS = [
  ['#product', 'Product'],
  ['#pipeline', 'How it works'],
  ['#capabilities', 'Capabilities'],
  ['#faq', 'FAQ'],
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, 'change', (v) => {
    setScrolled(v > 16);
  });

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'border-b border-seam bg-paper/90 backdrop-blur-xl shadow-[0_1px_0_rgb(var(--c-seam)/0.6)]'
          : 'border-b border-transparent bg-transparent'
      }`}
    >
      <div className='mx-auto flex h-[60px] max-w-6xl items-center gap-8 px-5 md:px-8'>
        {/* Logo */}
        <a href='/' className='group flex items-center gap-3' aria-label='CMPDI Intelligence home'>
          <span className='flex h-[30px] w-[30px] items-center justify-center rounded-md bg-coal font-mono text-[13px] font-bold text-white transition-transform duration-300 group-hover:rotate-[-8deg]'>
            C
          </span>
          <span className='hidden text-[14.5px] font-semibold tracking-tight sm:block'>
            CMPDI&nbsp;
            <span className='text-stone-500 font-normal'>Intelligence</span>
          </span>
        </a>

        {/* Nav links */}
        <nav className='ml-auto hidden items-center gap-1 md:flex' aria-label='Page sections'>
          {NAV_LINKS.map(([to, label]) => (
            <a
              key={to}
              href={to}
              className='rounded-md px-3 py-1.5 text-[13px] font-medium text-stone-500 transition-colors hover:bg-seam/60 hover:text-ink'
            >
              {label}
            </a>
          ))}
        </nav>

        {/* Status pill */}
        <span className='hidden items-center gap-1.5 rounded-full border border-seam px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest text-stone-500 md:flex'>
          <TextLoop interval={3.5} className='overflow-hidden'>
            <span>Offline</span>
            <span>No cloud</span>
            <span>Air-gapped</span>
          </TextLoop>
          <span className='h-1.5 w-1.5 rounded-full bg-emerald-600 shadow-[0_0_6px_rgb(16_185_129/0.8)]' />
        </span>

        <Magnetic intensity={0.25} range={80}>
          <a
            href='/dashboard'
            className='flex items-center gap-1.5 rounded-lg bg-coal px-4 py-2 text-[13px] font-semibold text-white transition-all duration-200 hover:opacity-90 active:scale-95'
          >
            Open workspace <ArrowRight className='h-3.5 w-3.5' />
          </a>
        </Magnetic>
      </div>
    </header>
  );
}
