import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Filter, X, Calendar, FileQuestion, ArrowRight, Hash, Building2, MapPin, Gauge, BookOpen } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { PageHeader, Loading, ErrorBox, Card, Badge, Button, EmptyState } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { InView } from '../components/motion/in-view.jsx';
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
  'rounded-lg border border-seam bg-surface px-3 py-1.5 text-xs text-ink focus:border-coal focus:outline-none transition-colors hover:border-coal/40';

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
  const facts = data?.facts || [];
  const entities = data?.entities || [];
  const locations = data?.locations || [];
  const metrics = data?.metrics || [];
  const reference = data?.reference || [];
  const filters = data?.filters || params;

  const orgTotal = facts.length + entities.length + locations.length + metrics.length + reference.length;
  const factHref = (f) => `/doc/${f.doc_id}${f.page_no ? `?page=${f.page_no}` : f.sheet_no != null ? `?sheet=${f.sheet_no}` : ''}`;

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
        subtitle='Organization-wide: documents, numeric facts, entities, locations, metrics and reference context. Every value links to its receipt.'
      />

      {/* Search bar */}
      <form onSubmit={submit} className='mt-6'>
        <div className='flex items-center gap-2'>
          <label className='relative flex-1'>
            <SearchIcon className='pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted1' />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder='Search mines, seams, reserves, production figures…'
              className='w-full rounded-xl border border-seam bg-surface py-3 pl-11 pr-4 text-sm shadow-card placeholder:text-muted2 focus:border-coal focus:outline-none'
            />
          </label>
          <Button type='submit' variant='primary' size='md' className='py-3 px-6'>
            <SearchIcon className='h-4 w-4' /> Search
          </Button>
        </div>

        {/* Filter bar */}
        <div className='mt-2.5 flex flex-wrap items-center gap-2 rounded-xl border border-seam bg-surface p-2.5 shadow-card'>
          <span className='flex items-center gap-1.5 px-1 font-mono text-[10px] uppercase tracking-wide text-muted1'>
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
          <span className='flex items-center gap-1.5 rounded-lg border border-seam bg-paper px-2.5 py-1.5 text-xs'>
            <Calendar className='h-3 w-3 text-muted1' />
            <input
              defaultValue={filters.from}
              name='from'
              placeholder='from'
              size='7'
              onBlur={select('from')}
              className='w-14 bg-transparent font-mono text-xs placeholder:text-muted2 focus:outline-none'
            />
            <span className='text-muted2'>–</span>
            <input
              defaultValue={filters.to}
              name='to'
              placeholder='to'
              size='7'
              onBlur={select('to')}
              className='w-14 bg-transparent font-mono text-xs placeholder:text-muted2 focus:outline-none'
            />
          </span>
          {activeFilters && (
            <Link
              to='/search'
              className='ml-auto flex items-center gap-1 text-xs font-medium text-bad hover:underline'
            >
              <X className='h-3.5 w-3.5' /> clear
            </Link>
          )}
        </div>
      </form>

      {/* Suggestion pills */}
      {!results.length && !params.q && (
        <AnimatedGroup preset='fade' className='mt-5 flex flex-wrap items-center gap-2'>
          <span className='font-mono text-[10.5px] uppercase tracking-wide text-muted1'>Try</span>
          {SUGGESTIONS.map((s) => (
            <Link
              key={s}
              to={`/search?q=${encodeURIComponent(s)}`}
              className='rounded-full border border-seam bg-surface px-3.5 py-1.5 text-xs text-muted0 shadow-card transition-all hover:border-coal hover:text-coal'
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
          className='mt-5 font-mono text-[11px] uppercase tracking-widest text-muted1'
        >
          <span className='tabular-nums'>{results.length}</span> document result{results.length !== 1 ? 's' : ''}
          {orgTotal > 0 && <span> · <span className='tabular-nums'>{orgTotal}</span> organization hit{orgTotal !== 1 ? 's' : ''}</span>} for{' '}
          <span className='text-coal font-semibold'>&ldquo;{params.q}&rdquo;</span>
        </motion.p>
      )}

      {/* Organization-wide sections */}
      {params.q && orgTotal > 0 && (
        <div className='mt-4 space-y-4'>
          {!!facts.length && (
            <section>
              <h3 className='flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted1'>
                <Hash className='h-3.5 w-3.5 text-coal' /> Facts
                <span className='font-mono text-[11px] font-normal text-muted1'>({facts.length} numeric values with receipts)</span>
              </h3>
              <div className='mt-2 grid grid-cols-1 gap-2.5 sm:grid-cols-2'>
                {facts.map((f) => (
                  <Card
                    key={f.id}
                    interactive
                    onClick={() => navigate(factHref(f))}
                    className='p-4 text-left'
                  >
                    <p className='font-mono text-base font-semibold tabular-nums text-ink'>
                      {f.value_raw} {f.unit || ''}
                    </p>
                    <p className='mt-0.5 text-xs text-muted0'>
                      {(f.entity || f.entity_text || '—')} · {String(f.attribute || '').replace(/_/g, ' ')} · {f.period_label || '—'}
                    </p>
                    <p className='mt-1 font-mono text-[11px] text-muted1'>
                      {f.filename}{f.page_no ? `, page ${f.page_no}` : f.sheet_no != null ? `, sheet ${f.sheet_no}` : ''}
                      {f.flags?.includes('low_confidence') ? ' · low OCR confidence' : ''}
                    </p>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {!!entities.length && (
            <section>
              <h3 className='flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted1'>
                <Building2 className='h-3.5 w-3.5 text-coal' /> Entities
                <span className='font-mono text-[11px] font-normal text-muted1'>({entities.length})</span>
              </h3>
              <div className='mt-2 flex flex-wrap gap-2'>
                {entities.map((e) => (
                  <Link
                    key={e.id}
                    to={`/assets?name=${encodeURIComponent(e.canonical_name)}`}
                    className='flex items-center rounded-xl border border-seam bg-surface px-3.5 py-2 shadow-card transition-all hover:border-coal'
                  >
                    <span className='text-xs font-semibold text-ink'>{e.canonical_name}</span>
                    <Badge variant='coal' className='ml-2 text-[10px]'>
                      {e.kind}
                    </Badge>
                    <span className='ml-2 font-mono text-[11px] text-muted1 tabular-nums'>{e.n_docs} docs · {e.n_facts} facts</span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {!!locations.length && (
            <section>
              <h3 className='flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted1'>
                <MapPin className='h-3.5 w-3.5 text-coal' /> Locations
                <span className='font-mono text-[11px] font-normal text-muted1'>({locations.length})</span>
              </h3>
              <div className='mt-2 flex flex-wrap gap-2'>
                {locations.map((e) => (
                  <Link
                    key={e.id}
                    to={`/assets?name=${encodeURIComponent(e.canonical_name)}`}
                    className='flex items-center rounded-xl border border-seam bg-surface px-3.5 py-2 shadow-card transition-all hover:border-coal'
                  >
                    <span className='text-xs font-semibold text-ink'>{e.canonical_name}</span>
                    <span className='ml-2 font-mono text-[11px] text-muted1 tabular-nums'>{e.type} · {e.n_docs} docs</span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {!!metrics.length && (
            <section>
              <h3 className='flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted1'>
                <Gauge className='h-3.5 w-3.5 text-coal' /> Metrics
                <span className='font-mono text-[11px] font-normal text-muted1'>({metrics.length})</span>
              </h3>
              <div className='mt-2 grid grid-cols-1 gap-2.5 sm:grid-cols-2'>
                {metrics.map((m) => (
                  <Card key={m.attribute} className='p-4'>
                    <p className='text-xs font-semibold text-ink'>{m.label}</p>
                    <p className='mt-0.5 font-mono text-[11px] text-muted1 tabular-nums'>{m.n_facts} facts · {m.n_entities} entities</p>
                    {m.sample && (
                      <Link
                        to={factHref(m.sample)}
                        className='mt-2 block font-mono text-xs text-coal hover:underline'
                      >
                        e.g. {m.sample.entity}: {m.sample.value_raw} {m.sample.unit || ''} — {m.sample.filename}
                      </Link>
                    )}
                  </Card>
                ))}
              </div>
            </section>
          )}

          {!!reference.length && (
            <section>
              <h3 className='flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted1'>
                <BookOpen className='h-3.5 w-3.5 text-coal' /> External context
                <span className='font-mono text-[11px] font-normal text-muted1'>({reference.length} · reference, not evidence)</span>
              </h3>
              <div className='mt-2 space-y-2'>
                {reference.map((r, i) => (
                  <Card key={i} className='bg-paper/40 p-3.5'>
                    <p className='text-xs text-ink'>
                      <Link to={`/assets?name=${encodeURIComponent(r.entity)}`} className='font-semibold hover:text-coal hover:underline'>
                        {r.entity}
                      </Link>
                      <span className='text-muted1'> · {r.label}: </span>
                      <span className='font-medium font-mono tabular-nums'>{r.value}{r.unit ? ` ${r.unit}` : ''}</span>
                    </p>
                    <p className='mt-0.5 font-mono text-[11px] text-muted1'>
                      {r.as_of ? `${r.as_of} · ` : ''}{r.source} · origin: reference
                    </p>
                  </Card>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {/* Documents header */}
      {params.q && (
        <h3 className='mt-6 text-xs font-semibold uppercase tracking-wider text-muted1'>
          Documents <span className='font-mono text-[11px] font-normal text-muted1'>({results.length} · BM25 + vectors)</span>
        </h3>
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
              transition={{ duration: 0.35, delay: i * 0.03 }}
            >
              <Card
                interactive
                onClick={() => navigate(docHref)}
                className='group relative p-0 overflow-hidden'
              >
                <div
                  className={`absolute inset-y-0 left-0 w-[3.5px] transition-all group-hover:w-[5px] group-hover:bg-coal ${
                    i === 0 ? 'bg-coal' : 'bg-seamdark'
                  }`}
                />
                <div className='py-4 pl-6 pr-5'>
                  <div className='flex flex-wrap items-start justify-between gap-3'>
                    <span className='text-sm font-semibold text-ink transition-colors group-hover:text-coal'>
                      {ev.doc_title}
                    </span>
                    <div className='flex items-center gap-2'>
                      {ev.score != null && (
                        <Badge
                          variant={ev.score >= 0.5 ? 'coal' : 'neutral'}
                          className='font-mono tabular-nums text-[10px]'
                        >
                          {Math.round(ev.score * 100)}% match
                        </Badge>
                      )}
                    </div>
                  </div>
                  <p className='mt-1 font-mono text-[11px] text-muted1'>
                    {ev.page_no ? `page ${ev.page_no}` : ev.sheet_no != null ? `sheet ${ev.sheet_no}` : 'document'}
                    {' · '}{String(ev.content_type || '').toLowerCase()}
                    {ev.subsidiary ? ` · ${ev.subsidiary}` : ''}
                  </p>
                  {ev.text && (
                    <p className='mt-2.5 text-xs leading-relaxed text-muted0 transition-colors group-hover:text-ink'>
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
                          className='rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 font-mono text-[10.5px] text-coal transition-colors hover:border-coal'
                        >
                          #{t}
                        </button>
                      ))}
                    </div>
                    <span className='flex items-center gap-1 font-mono text-xs font-semibold text-coal transition-transform group-hover:translate-x-0.5'>
                      Open source <ArrowRight className='h-3.5 w-3.5' />
                    </span>
                  </div>
                </div>
              </Card>
            </InView>
          );
        })}

        {/* Empty state */}
        {params.q && !results.length && !orgTotal && (
          <InView>
            <EmptyState
              icon={FileQuestion}
              title={`Nothing in the library matches "${params.q}"`}
              description='Try fewer words, or relax the filters above.'
              action={
                <Button
                  variant='secondary'
                  size='sm'
                  onClick={() => {
                    setInput('');
                    window.location.href = '/search';
                  }}
                >
                  Clear search
                </Button>
              }
              className='mt-6'
            />
          </InView>
        )}
      </div>
    </div>
  );
}
