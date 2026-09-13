import { TextEffect } from './motion/text-effect.jsx';
import { AnimatedGroup } from './motion/animated-group.jsx';
import { InView } from './motion/in-view.jsx';
import { TextShimmer } from './motion/text-shimmer.jsx';
import { GlowEffect } from './motion/glow-effect.jsx';

// Page header used by every workspace screen.
// Title animates per-word with the TextEffect preset; subtitle fades in.
export function PageHeader({ title, subtitle, children }) {
  return (
    <div className='flex flex-wrap items-start justify-between gap-3'>
      <div className='min-w-0'>
        <TextEffect as='h1' per='word' preset='fade-in-blur' trigger={true}
          className='text-2xl font-semibold tracking-tight'>
          {title}
        </TextEffect>
        {subtitle && (
          <TextEffect as='p' per='line' preset='fade' delay={0.15}
            className='mt-1 max-w-[70ch] text-[15px] text-stone-500'>
            {subtitle}
          </TextEffect>
        )}
      </div>
      {children}
    </div>
  );
}

// Standard staggered entrance for page content (above the fold).
export function Rise({ delay = 0, className = '', children }) {
  return (
    <AnimatedGroup preset='blur-slide' className={className}>
      <div style={{ animationDelay: `${delay}s` }}>{children}</div>
    </AnimatedGroup>
  );
}

// Scroll-triggered entrance for below-the-fold sections.
export function Reveal({ className = '', children }) {
  return (
    <InView
      className={className}
      variants={{ hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0 } }}
      transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </InView>
  );
}

export function Loading({ label = 'Loading workspace data…' }) {
  return (
    <div className='relative mx-auto mt-16 max-w-md overflow-hidden rounded-2xl border border-seam bg-white p-8 text-center shadow-card'>

      {/* Branded Pulse Icon */}
      <div className='relative mx-auto flex h-14 w-14 items-center justify-center'>
        <span className='absolute inset-0 animate-ping rounded-2xl bg-coal/20 duration-1000' />
        <span className='relative flex h-12 w-12 items-center justify-center rounded-xl bg-coal font-mono text-base font-bold text-white shadow-[0_4px_14px_rgba(234,138,12,0.4)]'>
          C
        </span>
      </div>

      {/* Shimmering label */}
      <div className='mt-5'>
        <TextShimmer as='p' duration={2} className='text-[14px] font-semibold text-ink'>
          {label}
        </TextShimmer>
        <p className='mt-1 font-mono text-[11px] text-stone-400'>
          Offline document intelligence · local verification
        </p>
      </div>

      {/* Subtle Skeleton progress bars */}
      <div className='mx-auto mt-5 max-w-[200px] space-y-2'>
        <div className='h-1.5 w-full overflow-hidden rounded-full bg-paper'>
          <div className='h-full w-2/3 animate-[pulse_1.5s_ease-in-out_infinite] rounded-full bg-coal/50' />
        </div>
        <div className='h-1 w-3/4 mx-auto overflow-hidden rounded-full bg-paper'>
          <div className='h-full w-1/2 animate-[pulse_1.2s_ease-in-out_infinite] rounded-full bg-coal/30' />
        </div>
      </div>
    </div>
  );
}

export function ErrorBox({ message }) {
  return (
    <div className='relative mt-6 overflow-hidden rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13.5px] text-red-700'>
      <GlowEffect colors={['#fecaca', '#fca5a5', '#fecaca']} mode='static' blur='soft' className='opacity-60' />
      <span className='relative'>{message}</span>
    </div>
  );
}
