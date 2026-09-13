import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Filter, X, Calendar, FileQuestion, ArrowRight } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { InView } from '../components/motion/in-view.jsx';
import { Magnetic } from '../components/motion/magnetic.jsx';
import { motion } from 'motion/react';

const SUGGESTIONS = [
  'lignite reserves',
  'coking coal washeries',
  'coal offtake 2022-23',
  'geological exploration',
  'subsidiary production',
  'OCR confidence',
];

const selectCls =
  'rounded-lg border border-seam bg-paper px-3 py-1.5 text-[12.5px] text-stone-600 focus:border-coal focus:outline-none transition-colors hover:border-coal/40';

export default function Search() {
  const navigate = useNavigate();
  const params = Object.fromEntries(new URLSearchParams(window.location.search));
  const [input, setInput] = useState(params.q || '');
  const query = new URLSearchParams(
    Object.entries({
      q: params.q || '',
      tag: params.tag || '',
      subsidiary: params.subsidiary || '',
      type: params.type || '',
      from: params.from || '',
      to: params.to || '',
    }).filter(([, v]) => v)
  ).toString();
  const { data, error } = usePageData(`/api/pages/search${query ? `?${query}` : ''}`);
  const activeFilters = params.type || params.subsidiary || params.tag || params.from || params.to;
  const results = data?.results || [];
  const filters = data?.filters || params;

  const submit = (e) => {
    e.preventDefault();
    const next = new URLSearchParams(window.location.search);
    if (input) next.set('q', input);
    else next.delete('q');
    window.location.search = next.toString();
  };

  const select = (key) => (e) => {
    const next = new URLSearchParams(window.location.search);
    if (e.target.value) next.set(key, e.target.value);
    else next.delete(key);
    window.location.search = next.toString();
  };

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  return (
    <div>
      <PageHeader
        title='Search'
        subtitle='BM25 + semantic vectors, fused. Every result links to the exact page or cell it came from.'
      />

      {/* Search bar */}
      <form onSubmit={submit} className='mt-6'>
        <div className='flex items-center gap-2'>
          <label className='relative flex-1'>
            <SearchIcon className='pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400' />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder='Search mines, seams, reserves, production figures…'
              className='w-full rounded-xl border border-seam bg-white py-3 pl-11 pr-4 text-[14.5px] shadow-card placeholder:text-stone-400 focus:border-coal focus:outline-none'
            />
          </label>
          <Magnetic intensity={0.25} range={80}>
            <button
              type='submit'
              className='flex items-center gap-2 rounded-xl bg-coal px-6 py-3 text-[13.5px] font-semibold text-white shadow-card transition-all duration-200 hover:opacity-90 active:scale-95'
            >
              <SearchIcon className='h-4 w-4' /> Search
            </button>
          </Magnetic>
        </div>

        {/* Filter bar */}
        <div className='mt-2.5 flex flex-wrap items-center gap-2 rounded-xl border border-seam bg-white p-2.5 shadow-card'>
          <span className='flex items-center gap-1.5 px-1 font-mono text-[10px] uppercase tracking-wide text-stone-400'>
            <Filter className='h-3 w-3' /> Filters
          </span>
          <select value={filters.type} onChange={select('type')} className={selectCls}>
            <option value=''>Any type</option>
            {data.doc_types.map((t) => (
              <option key={t.doc_type} value={t.doc_type}>{t.doc_type}</option>
            ))}
          </select>
          <select value={filters.subsidiary} onChange={select('subsidiary')} className={selectCls}>
            <option value=''>Any subsidiary</option>
            {data.subs.map((s) => (
              <option key={s.subsidiary} value={s.subsidiary}>{s.subsidiary}</option>
            ))}
          </select>
          <select value={filters.tag} onChange={select('tag')} className={`${selectCls} max-w-[180px]`}>
            <option value=''>Any tag</option>
            {data.tags.map((t) => (
              <option key={t.keyword} value={t.keyword}>{t.keyword} ({t.count})</option>
            ))}
          </select>
          <span className='flex items-center gap-1.5 rounded-lg border border-seam bg-paper px-2.5 py-1.5 text-[12.5px]'>
            <Calendar className='h-3 w-3 text-stone-400' />
            <input
              defaultValue={filters.from}
              name='from'
              placeholder='from'
              size='7'
              onBlur={select('from')}
              className='w-14 bg-transparent font-mono text-[12px] placeholder:text-stone-400 focus:outline-none'
            />
            <span className='text-stone-300'>–</span>
            <input
              defaultValue={filters.to}
              name='to'
              placeholder='to'
              size='7'
              onBlur={select('to')}
              className='w-14 bg-transparent font-mono text-[12px] placeholder:text-stone-400 focus:outline-none'
            />
          </span>
          {activeFilters && (
            <Link
              to='/search'
              className='ml-auto flex items-center gap-1 text-[12px] font-medium text-stone-500 transition-colors hover:text-red-700'
            >
              <X className='h-3.5 w-3.5' /> clear
            </Link>
          )}
        </div>
      </form>

      {/* Suggestion pills */}
      {!results.length && !params.q && (
        <AnimatedGroup preset='fade' className='mt-5 flex flex-wrap items-center gap-2'>
          <span className='font-mono text-[10.5px] uppercase tracking-wide text-stone-400'>Try</span>
          {SUGGESTIONS.map((s) => (
            <Link
              key={s}
              to={`/search?q=${encodeURIComponent(s)}`}
              className='rounded-full border border-seam bg-white px-3.5 py-1.5 text-[13px] text-stone-600 shadow-card transition-all hover:-translate-y-px hover:border-coal hover:text-coal'
            >
              {s}
            </Link>
          ))}
        </AnimatedGroup>
      )}

      {/* Result count */}
      {params.q && (
        <motion.p
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className='mt-5 font-mono text-[11px] uppercase tracking-widest text-stone-400'
        >
          {results.length} result{results.length !== 1 ? 's' : ''} for{' '}
          <span className='text-coal'>&ldquo;{params.q}&rdquo;</span>
        </motion.p>
      )}

      {/* Results */}
      <div className='mt-3 space-y-2.5'>
        {results.map((ev, i) => {
          const docHref = `/doc/${ev.doc_id}${
            ev.page_no
              ? `?page=${ev.page_no}`
              : ev.sheet_no != null
              ? `?sheet=${ev.sheet_no}`
              : ''
          }`;
          return (
            <InView
              key={`${ev.doc_id}-${ev.chunk_id ?? i}`}
              variants={{ hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0 } }}
              transition={{ duration: 0.45, delay: i * 0.04 }}
            >
              <article
                onClick={() => navigate(docHref)}
                className='group relative cursor-pointer overflow-hidden rounded-xl border border-seam bg-white shadow-card transition-all duration-200 hover:border-coal/60 hover:shadow-lift'
              >
                <div
                  className={`absolute inset-y-0 left-0 w-[3.5px] transition-all group-hover:w-[5px] group-hover:bg-coal ${
                    i === 0 ? 'bg-coal' : 'bg-coalline'
                  }`}
                />
                <div className='py-4 pl-6 pr-5'>
                  <div className='flex flex-wrap items-start justify-between gap-3'>
                    <span className='text-[15px] font-semibold text-ink transition-colors group-hover:text-coal'>
                      {ev.doc_title}
                    </span>
                    <div className='flex items-center gap-2'>
                      {ev.score != null && (
                        <span
                          className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wide ${
                            ev.score >= 0.5
                              ? 'border-coal/30 bg-coalsoft text-coal'
                              : 'border-seam bg-paper text-stone-500'
                          }`}
                        >
                          {Math.round(ev.score * 100)}% match
                        </span>
                      )}
                    </div>
                  </div>
                  <p className='mt-1 font-mono text-[11px] text-stone-400'>
                    {ev.page_no ? `page ${ev.page_no}` : ev.sheet_no != null ? `sheet ${ev.sheet_no}` : 'document'}
                    {' · '}{String(ev.content_type || '').toLowerCase()}
                    {ev.subsidiary ? ` · ${ev.subsidiary}` : ''}
                  </p>
                  {ev.text && (
                    <p className='mt-2.5 text-[13.5px] leading-relaxed text-stone-600 transition-colors group-hover:text-stone-800'>
                      {(ev.text || '').slice(0, 500)}
                      {(ev.text || '').length > 500 ? '…' : ''}
                    </p>
                  )}
                  <div className='mt-3 flex flex-wrap items-center justify-between gap-2'>
                    <div className='flex flex-wrap gap-1.5'>
                      {(ev.tags || []).map((t) => (
                        <button
                          key={t}
                          type='button'
                          onClick={(e) => {
                            e.stopPropagation();
                            const next = new URLSearchParams(window.location.search);
                            next.set('tag', t);
                            window.location.search = next.toString();
                          }}
                          className='rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 font-mono text-[10.5px] text-coal transition-colors hover:bg-amber-100 hover:border-coal'
                        >
                          #{t}
                        </button>
                      ))}
                    </div>
                    <span className='flex items-center gap-1 font-mono text-[11.5px] font-semibold text-coal transition-transform group-hover:translate-x-0.5'>
                      Open source <ArrowRight className='h-3.5 w-3.5' />
                    </span>
                  </div>
                </div>
              </article>
            </InView>
          );
        })}

        {/* Empty state */}
        {params.q && !results.length && (
          <InView>
            <div className='mt-6 flex flex-col items-center rounded-2xl border border-dashed border-seamdark bg-white px-6 py-16 text-center'>
              <span className='flex h-14 w-14 items-center justify-center rounded-2xl bg-coalsoft text-coal'>
                <FileQuestion className='h-7 w-7' />
              </span>
              <p className='mt-4 text-[15px] font-semibold'>
                Nothing in the library matches &ldquo;{params.q}&rdquo;
              </p>
              <p className='mt-1.5 max-w-[40ch] text-[13px] text-stone-500'>
                Try fewer words, or relax the filters above.
              </p>
            </div>
          </InView>
        )}
      </div>
    </div>
  );
}
