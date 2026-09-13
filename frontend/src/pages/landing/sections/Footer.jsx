import { ShieldCheck } from 'lucide-react';

const FOOTER_COLS = [
  [
    'Product',
    [
      ['/dashboard', 'Dashboard'],
      ['/pipeline', 'Ingest'],
      ['/ask', 'Ask'],
      ['/reports', 'Reports'],
      ['/settings', 'Settings'],
    ],
  ],
  [
    'Library tools',
    [
      ['/documents', 'Documents'],
      ['/search', 'Search'],
      ['/insights', 'Insights'],
      ['/conflicts', 'Conflict Radar'],
      ['/knowledge', 'Knowledge Tree'],
    ],
  ],
  [
    'Trust',
    [
      ['#faq', 'Questions & answers'],
      ['#pipeline', 'How evidence works'],
      ['/compare', 'Compare documents'],
      ['/ask', 'Analytical agent'],
    ],
  ],
];

export function Footer() {
  return (
    <footer className='border-t border-sideline bg-side text-sidetext'>
      <div className='mx-auto max-w-6xl px-5 pb-10 pt-14 md:px-8'>
        <div className='grid gap-10 md:grid-cols-12'>
          {/* Brand col */}
          <div className='md:col-span-5'>
            <a href='/' className='flex items-center gap-2.5' aria-label='CMPDI Intelligence home'>
              <span className='flex h-7 w-7 items-center justify-center rounded-md bg-coal font-mono text-[12px] font-bold text-white'>
                C
              </span>
              <span className='text-[15px] font-semibold tracking-tight'>
                CMPDI&nbsp;<span className='text-sidemute font-normal'>Intelligence</span>
              </span>
            </a>
            <p className='mt-4 max-w-[44ch] text-[13px] leading-relaxed text-sidemute'>
              An offline document-intelligence workspace for coal, mining and geology
              reporting. Every number, answer and report carries a receipt back to its
              exact source.
            </p>
            <p className='mt-5 inline-flex items-center gap-1.5 rounded-full border border-sideline px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-sidemute'>
              <ShieldCheck className='h-3 w-3 text-coal' />
              fully offline · no telemetry
            </p>
          </div>

          {/* Nav cols */}
          {FOOTER_COLS.map(([title, links]) => (
            <nav key={title} className='md:col-span-2' aria-label={title}>
              <p className='font-mono text-[10px] uppercase tracking-widest text-sidemute'>
                {title}
              </p>
              <ul className='mt-4 space-y-2.5 text-[13px]'>
                {links.map(([to, label]) => (
                  <li key={to}>
                    <a
                      href={to}
                      className='text-sidetext/80 transition-colors hover:text-coal'
                    >
                      {label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        {/* Bottom bar */}
        <div className='mt-12 flex flex-wrap items-center justify-between gap-3 border-t border-sideline pt-6 font-mono text-[10px] uppercase tracking-widest text-sidemute'>
          <span>© 2026 CMPDI Intelligence · SIH26023</span>
          <span>built for the desk where the reports land</span>
        </div>
      </div>
    </footer>
  );
}
