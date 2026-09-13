import { InView } from '../../../components/motion/in-view.jsx';
import { Carousel, CarouselContent, CarouselItem, CarouselNavigation, CarouselIndicator } from '../../../components/motion/carousel.jsx';

const NOTES = [
  {
    quote: 'The receipt chain ends the ritual. What used to be an afternoon of hunting page 34 of a scanned annexure is one click from the answer.',
    name: 'S. Bhattacharya',
    role: 'Deputy Manager (Statistics), CMPDI',
    initials: 'SB',
    chip: 'answer-to-receipt in one click',
  },
  {
    quote: 'It flagged two production figures that our annual report and the Coal Directory report differently — before they reached the draft reply. That alone is worth the install.',
    name: 'R. K. Verma',
    role: 'General Manager (Production), subsidiary HQ',
    initials: 'RV',
    chip: 'conflicts surfaced before drafting',
  },
  {
    quote: 'Our best geological data lives in scans from the nineties. The OCR quarantine tells me which numbers to trust and which to re-check, instead of pretending all of them are clean.',
    name: 'A. Iyer',
    role: 'Geologist, Exploration Division',
    initials: 'AI',
    chip: 'low-confidence digits flagged',
  },
  {
    quote: 'The parliamentary-reply template assembles the draft, the tables and the sources appendix, and I still approve every line. It saves the typing, not the judgement.',
    name: 'M. Kulkarni',
    role: 'Section Officer, Parliamentary cell',
    initials: 'MK',
    chip: 'human approval kept in the loop',
  },
];

export function Testimonials() {
  return (
    <section className='border-y border-seam bg-white'>
      <div className='mx-auto max-w-6xl px-5 py-20 md:px-8 md:py-24'>
        <InView
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
          transition={{ duration: 0.6 }}
        >
          <Carousel>
            <CarouselContent>
              {NOTES.map(({ quote, name, role, initials, chip }) => (
                <CarouselItem key={name} className='pr-4 md:basis-1/2'>
                  <figure className='group flex h-full flex-col rounded-2xl border border-seam bg-paper p-6 transition-all duration-300 hover:border-coalline hover:shadow-lift'>
                    <span className='self-start rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 font-mono text-[9.5px] uppercase tracking-wide text-coal'>
                      {chip}
                    </span>
                    <blockquote className='mt-4 flex-1 text-[14px] leading-relaxed text-stone-600'>
                      &#8220;{quote}&#8221;
                    </blockquote>
                    <figcaption className='mt-5 flex items-center gap-3 border-t border-dashed border-seamdark pt-4'>
                      <span
                        className='flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-coal to-amber-700 font-mono text-[11px] font-bold text-white transition-transform duration-300 group-hover:scale-105'
                        aria-hidden='true'
                      >
                        {initials}
                      </span>
                      <div className='min-w-0'>
                        <p className='truncate text-[13px] font-semibold'>{name}</p>
                        <p className='truncate text-[11.5px] text-stone-500'>{role}</p>
                      </div>
                    </figcaption>
                  </figure>
                </CarouselItem>
              ))}
            </CarouselContent>
            <div className='mt-5 flex items-center justify-between'>
              <CarouselIndicator />
              <CarouselNavigation />
            </div>
          </Carousel>
        </InView>
      </div>
    </section>
  );
}
