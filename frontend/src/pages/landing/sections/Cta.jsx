import { ArrowRight, Package, ShieldCheck, HardDrive, CircleCheck } from 'lucide-react';
import { InView } from '../../../components/motion/in-view.jsx';
import { TextEffect } from '../../../components/motion/text-effect.jsx';
import { GlowEffect } from '../../../components/motion/glow-effect.jsx';
import { Magnetic } from '../../../components/motion/magnetic.jsx';

export function Cta() {
  const loadDemo = async (e) => {
    e.preventDefault();
    await fetch('/api/pipeline/demo', { method: 'POST' });
    window.location.href = '/pipeline';
  };

  return (
    <section className='relative overflow-hidden bg-side text-sidetext'>
      {/* Subtle top scallop border */}
      <div
        className='h-4 bg-[radial-gradient(circle_at_8px_-4px,transparent_8px,rgb(var(--s-bg))_8.5px)] bg-[length:16px_16px] bg-repeat-x'
        style={{ backgroundImage: 'radial-gradient(circle at 8px -4px, transparent 8px, rgb(var(--s-bg)) 8.5px)', backgroundSize: '16px 16px' }}
        aria-hidden='true'
      />

      {/* Glow */}
      <div
        className='pointer-events-none absolute -top-40 left-1/2 h-80 w-[50rem] -translate-x-1/2 rounded-full blur-3xl opacity-40'
        style={{ background: 'radial-gradient(ellipse at center, rgba(var(--c-coal)/0.5), transparent 70%)' }}
        aria-hidden='true'
      />

      <div className='relative mx-auto max-w-5xl px-5 py-24 text-center md:px-8 md:py-28'>
        <TextEffect
          as='h2'
          per='word'
          preset='fade-in-blur'
          className='mx-auto max-w-[22ch] text-4xl font-bold leading-[1.04] tracking-[-0.03em] text-sidetext md:text-[3.2rem]'
        >
          Stop hunting through PDFs. Start reading the library.
        </TextEffect>

        <InView
          variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <p className='mx-auto mt-6 max-w-[54ch] text-[15px] leading-relaxed text-sidemute'>
            Set up takes minutes and everything stays on this machine. Drop in your own
            reports — or generate the demonstration corpus first and see receipts,
            conflicts and reports working end to end.
          </p>
        </InView>

        <InView
          variants={{ hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0 } }}
          transition={{ duration: 0.55, delay: 0.35 }}
        >
          <div className='mt-10 flex flex-wrap items-center justify-center gap-4'>
            <Magnetic intensity={0.3} range={120}>
              <span className='relative inline-flex'>
                <GlowEffect
                  colors={['#d97706', '#fbbf24', '#d97706']}
                  mode='breathe'
                  blur='medium'
                  duration={3.4}
                  className='rounded-full'
                />
                <a
                  href='/dashboard'
                  className='group relative inline-flex items-center gap-2.5 overflow-hidden rounded-full bg-coal px-10 py-4 text-[1rem] font-semibold text-white transition-transform duration-200 hover:-translate-y-px active:translate-y-0'
                >
                  Open the Workspace
                  <span
                    className='pointer-events-none absolute inset-y-[-30%] left-0 w-[40%] -translate-x-[200%] skew-x-[-18deg] bg-gradient-to-r from-transparent via-white/30 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-[360%]'
                    aria-hidden='true'
                  />
                  <ArrowRight className='h-[18px] w-[18px] transition-transform duration-200 group-hover:translate-x-0.5' />
                </a>
              </span>
            </Magnetic>

            <form onSubmit={loadDemo}>
              <button
                type='submit'
                className='flex items-center gap-2 rounded-full border border-sideline px-7 py-4 text-[1rem] font-semibold text-sidetext transition-all duration-200 hover:border-coal/40 hover:bg-coal/10 hover:text-coal active:scale-95'
              >
                <Package className='h-[17px] w-[17px]' />
                Load the demo corpus
              </button>
            </form>
          </div>

          <p className='mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 font-mono text-[10px] uppercase tracking-widest text-sidemute'>
            <span className='flex items-center gap-1.5'>
              <ShieldCheck className='h-3.5 w-3.5 text-coal' /> no cloud, no API calls
            </span>
            <span className='flex items-center gap-1.5'>
              <HardDrive className='h-3.5 w-3.5 text-coal' /> one machine, one database
            </span>
            <span className='flex items-center gap-1.5'>
              <CircleCheck className='h-3.5 w-3.5 text-coal' /> every answer you can audit
            </span>
          </p>
        </InView>
      </div>
    </section>
  );
}
