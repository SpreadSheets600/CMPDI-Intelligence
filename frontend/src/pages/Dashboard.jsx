import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  MessageCircle, FileChartColumn, TriangleAlert, Files, FileCheck,
  Check, TriangleAlert as Alert, LoaderCircle, ArrowRight,
  Database, Cpu, ShieldCheck, CheckCircle2,
  TrendingUp, TrendingDown, Minus, GitCompareArrows, Tags, Info,
} from 'lucide-react';
import { getJSON } from '../api.js';
import { usePageData } from '../hooks/useData.js';
import { Rise, PageHeader, Loading, ErrorBox } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { AnimatedNumber } from '../components/motion/animated-number.jsx';
import { Spotlight } from '../components/motion/spotlight.jsx';

const QUICK_ACTIONS = [
  {
    href: '/ask',
    Icon: MessageCircle,
    title: 'Ask a Question',
    desc: 'Cited answers, sandboxed analysis & charts',
    badge: 'Interactive',
  },
  {
    href: '/reports',
    Icon: FileChartColumn,
    title: 'Generate a Report',
    desc: 'Comprehensive DOCX reports with receipts',
    badge: 'DOCX Studio',
  },
  {
    href: '/conflicts',
    Icon: TriangleAlert,
    title: 'Investigate Conflicts',
    desc: 'Disagreeing values across sources, explained',
    badge: 'Radar',
  },
  {
    href: '/documents',
    Icon: Files,
    title: 'Explore Documents',
    desc: 'Filter, inspect provenance and compare files',
    badge: 'Library',
  },
];

function HeadlineNumber({ value }) {
  return Number.isFinite(value) ? (
    <AnimatedNumber value={value} className='font-mono text-2xl font-bold tracking-tight text-ink' />
  ) : (
    <span className='font-mono text-2xl font-bold tracking-tight text-ink'>{value}</span>
  );
}

const fy = (iso) => {
  if (!iso || iso.length < 4) return 'n/a';
  const y = Number(iso.slice(0, 4));
  return Number.isFinite(y) ? `${y}–${String(y + 1).slice(2)}` : iso.slice(0, 4);
};

const deltaChip = (delta) => {
  if (delta == null) return <span className='font-mono text-[11px] text-stone-400'>—</span>;
  const cls = delta > 0 ? 'bg-emerald-50 text-emerald-700' : delta < 0 ? 'bg-red-50 text-red-700' : 'bg-paper text-stone-500';
  return (
    <span className={`rounded px-1.5 py-0.5 font-mono text-[11px] font-semibold ${cls}`}>
      {delta > 0 ? `+${delta}%` : `${delta}%`}
    </span>
  );
};

function SignalPanel({ title, linkTo, linkLabel, children }) {
  return (
    <div className='flex flex-col rounded-xl border border-seam bg-white p-4 shadow-card'>
      <div className='mb-2 flex items-center justify-between gap-2'>
        <h3 className='text-[13.5px] font-semibold text-ink'>{title}</h3>
        {linkTo && (
          <Link to={linkTo} className='flex shrink-0 items-center gap-1 text-[12px] font-medium text-coal hover:underline'>
            {linkLabel} <ArrowRight className='h-3 w-3' />
          </Link>
        )}
      </div>
      {children}
    </div>
  );
}

const emptyNote = (text) => (
  <p className='flex items-start gap-1.5 py-2 text-[12.5px] text-stone-500'>
    <Info className='mt-0.5 h-3.5 w-3.5 shrink-0 text-stone-400' />{text}
  </p>
);

// Organizational signals aggregated deterministically from the knowledge
// layer (facts, conflicts, version chains, jobs, tags). Every signal links
// to the screen holding its receipts; a signals failure never breaks the
// dashboard itself.
function Signals() {
  const [state, setState] = useState({ data: null, error: null });
  const [subsidiary, setSubsidiary] = useState('');
  const [subs, setSubs] = useState([]);
  useEffect(() => {
    getJSON('/api/pages/insights')
      .then((d) => setSubs((d.subs || []).map((s) => s.subsidiary).filter(Boolean)))
      .catch(() => {});
  }, []);
  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, error: null }));
    const qs = subsidiary ? `?subsidiary=${encodeURIComponent(subsidiary)}` : '';
    getJSON(`/api/insights/dashboard${qs}`)
      .then((data) => alive && setState({ data, error: null }))
      .catch((e) => alive && setState({ data: null, error: e.message }));
    return () => { alive = false; };
  }, [subsidiary]);
  const { data, error } = state;
  if (error) {
    return (
      <div className='rounded-xl border border-seam bg-white p-4 shadow-card'>
        <p className='text-[12.5px] text-red-700'>Signals unavailable: {error}</p>
      </div>
    );
  }
  if (!data) {
    return (
      <div className='rounded-xl border border-seam bg-white p-4 shadow-card'>
        <p className='flex items-center gap-2 text-[12.5px] text-stone-400'>
          <LoaderCircle className='h-3.5 w-3.5 animate-spin' /> Gathering organizational signals…
        </p>
      </div>
    );
  }

  const newestOf = (docs) => docs.filter((d) => d.is_current_version).slice(-1)[0] || docs.slice(-1)[0];
  const scopeLabel = data.scope && data.scope !== 'corpus' ? data.scope : 'corpus-wide';

  return (
    <div>
      <div className='mb-2 flex flex-wrap items-center justify-between gap-2'>
        <h2 className='text-[13px] font-semibold uppercase tracking-wider text-stone-400'>
          Organizational Signals
        </h2>
        <div className='flex flex-wrap items-center gap-2'>
          <span className='font-mono text-[10.5px] text-stone-400'>
            {data.corpus.metrics} metrics · {data.corpus.fact_points} fact points · {scopeLabel}
          </span>
          <select
            value={subsidiary}
            onChange={(e) => setSubsidiary(e.target.value)}
            aria-label='Filter signals by subsidiary'
            className='rounded-lg border border-seam bg-white px-2 py-1 font-mono text-[11px] text-stone-600 focus:border-coal focus:outline-none'
          >
            <option value=''>All subsidiaries</option>
            {subs.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className='grid grid-cols-1 gap-3 lg:grid-cols-2'>
        <SignalPanel title='Metric Trends' linkTo='/insights' linkLabel='Fact explorer'>
          {data.trends.length === 0
            ? emptyNote('No multi-period metrics yet — ingest dated documents with numeric facts.')
            : (
              <div className='space-y-1.5'>
                {data.trends.slice(0, 5).map((t) => (
                  <Link
                    key={`${t.entity}|${t.attribute}`}
                    to={`/insights?entity=${encodeURIComponent(t.entity)}&attribute=${encodeURIComponent(t.attribute)}`}
                    className='flex items-center justify-between gap-2 rounded-lg border border-seam bg-paper px-3 py-2 transition-colors hover:border-coal/50'
                  >
                    <div className='flex min-w-0 items-center gap-2'>
                      {t.direction === 'up'
                        ? <TrendingUp className='h-4 w-4 shrink-0 text-emerald-700' />
                        : t.direction === 'down'
                          ? <TrendingDown className='h-4 w-4 shrink-0 text-red-700' />
                          : <Minus className='h-4 w-4 shrink-0 text-stone-400' />}
                      <div className='min-w-0'>
                        <p className='truncate text-[12.5px] font-semibold text-ink'>
                          {t.entity} · {String(t.attribute).replace('_', ' ')}
                        </p>
                        <p className='font-mono text-[10.5px] text-stone-400'>
                          {fy(t.periods[0])} → {fy(t.periods[t.periods.length - 1])} · {t.last} MT · {t.n_periods} periods · {t.n_docs} docs
                        </p>
                      </div>
                    </div>
                    {deltaChip(t.delta_pct)}
                  </Link>
                ))}
              </div>
            )}
        </SignalPanel>

        <SignalPanel title='Anomalies to Review' linkTo='/insights' linkLabel='Fact explorer'>
          {data.anomalies.length === 0
            ? emptyNote('No sharp moves, outliers or thin-evidence metrics detected.')
            : (
              <div className='space-y-1.5'>
                {data.anomalies.slice(0, 5).map((a, i) => (
                  <Link
                    key={i}
                    to={`/insights?entity=${encodeURIComponent(a.entity)}&attribute=${encodeURIComponent(a.attribute)}`}
                    className='block rounded-lg border border-seam bg-paper px-3 py-2 transition-colors hover:border-coal/50'
                  >
                    <p className='flex flex-wrap items-center gap-2 text-[12.5px] font-semibold text-ink'>
                      <span className={`rounded-full border px-2 py-0.5 font-mono text-[9.5px] uppercase ${a.severity === 'high' ? 'border-red-200 bg-red-50 text-red-700' : 'border-coalline bg-coalsoft text-coal'}`}>
                        {a.severity === 'high' ? 'high' : 'watch'}
                      </span>
                      {a.title}
                    </p>
                    <p className='mt-0.5 text-[12px] text-stone-500'>{a.detail}</p>
                  </Link>
                ))}
              </div>
            )}
        </SignalPanel>

        <SignalPanel
          title={`Conflicts Needing Review${data.corpus.open_conflicts ? ` (${data.corpus.open_conflicts} open)` : ''}`}
          linkTo='/conflicts'
          linkLabel='Conflict Radar'
        >
          {data.conflicts_top.length === 0
            ? emptyNote('All reported values agree, or nothing has been extracted yet.')
            : (
              <div className='space-y-1.5'>
                {data.conflicts_top.slice(0, 4).map((c) => (
                  <Link
                    key={c.key}
                    to={`/conflicts?entity=${encodeURIComponent(c.entity)}&attribute=${encodeURIComponent(c.attribute)}`}
                    className='flex items-center justify-between gap-2 rounded-lg border border-seam bg-paper px-3 py-2 transition-colors hover:border-coal/50'
                  >
                    <div className='min-w-0'>
                      <p className='truncate text-[12.5px] font-semibold text-ink'>
                        {c.entity} · {String(c.attribute).replace('_', ' ')} · {fy(c.period)}
                      </p>
                      <p className='font-mono text-[10.5px] text-stone-400'>
                        {c.n_values} values · {c.status}
                      </p>
                    </div>
                    <span className='shrink-0 font-mono text-[11px] font-semibold text-red-700'>{c.spread_pct}%</span>
                  </Link>
                ))}
              </div>
            )}
        </SignalPanel>

        <SignalPanel title='Changes & Versions' linkTo='/compare' linkLabel='Compare'>
          {data.changes.version_groups.length === 0 && data.changes.recent_docs.length === 0
            ? emptyNote('No version chains or recent uploads to report.')
            : (
              <div className='space-y-1.5'>
                {data.changes.version_diffs.slice(0, 2).map((d) => (
                  <div key={d.group_id} className='rounded-lg border border-seam bg-paper px-3 py-2'>
                    <p className='flex items-center gap-1.5 text-[12.5px] font-semibold text-ink'>
                      <GitCompareArrows className='h-3.5 w-3.5 shrink-0 text-coal' />
                      <span className='truncate'>{d.a_name} → {d.b_name}</span>
                    </p>
                    <p className='mt-0.5 font-mono text-[10.5px] text-stone-500'>
                      {d.summary.changed} changed · {d.summary.added} added · {d.summary.removed} removed
                    </p>
                  </div>
                ))}
                {data.changes.version_groups.slice(0, 2).map((g) => {
                  const newest = newestOf(g.docs);
                  return newest ? (
                    <Link
                      key={g.group_id}
                      to={`/compare?doc=${newest.id}`}
                      className='block truncate rounded-lg border border-seam bg-paper px-3 py-2 text-[12.5px] text-stone-600 transition-colors hover:border-coal/50 hover:text-coal'
                    >
                      Version chain ({g.docs.length} revisions) — compare from {newest.display_name || newest.filename} →
                    </Link>
                  ) : null;
                })}
                {data.changes.failed_jobs.length > 0 && (
                  <p className='rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[12px] text-red-700'>
                    {data.changes.failed_jobs.length} recent ingestion failure(s) — see Pipeline for reasons.
                  </p>
                )}
              </div>
            )}
        </SignalPanel>

        <SignalPanel title='Coverage Gaps' linkTo='/documents' linkLabel='Library'>
          {data.gaps.length === 0
            ? emptyNote('No gaps detected: summaries present, jobs clean, metrics corroborated.')
            : (
              <div className='space-y-1.5'>
                {data.gaps.slice(0, 5).map((g, i) => (
                  <div key={i} className='rounded-lg border border-seam bg-paper px-3 py-2'>
                    <p className='text-[12.5px] font-semibold text-ink'>{g.title}</p>
                    <p className='mt-0.5 text-[12px] text-stone-500'>{g.detail}</p>
                  </div>
                ))}
              </div>
            )}
        </SignalPanel>

        <SignalPanel title='What the Library Talks About' linkTo='/search' linkLabel='Search'>
          {data.topics.tags.length === 0 && data.topics.clusters.length === 0
            ? emptyNote('No keywords or topic clusters yet.')
            : (
              <div className='space-y-2'>
                {data.topics.tags.length > 0 && (
                  <div className='flex flex-wrap gap-1.5'>
                    {data.topics.tags.slice(0, 10).map((t) => (
                      <Link
                        key={t.keyword}
                        to={`/search?tag=${encodeURIComponent(t.keyword)}`}
                        className='flex items-center gap-1 rounded-full border border-seam bg-paper px-2.5 py-1 font-mono text-[10.5px] text-stone-600 transition-colors hover:border-coal/50 hover:text-coal'
                      >
                        <Tags className='h-3 w-3' />{t.keyword} · {t.n}
                      </Link>
                    ))}
                  </div>
                )}
                {data.topics.clusters.slice(0, 2).map((c, i) => (
                  <p key={i} className='text-[12px] text-stone-500'>
                    <span className='font-semibold text-ink'>{c.label}</span>
                    {' '}({c.n_docs} docs) — {c.keywords.slice(0, 4).join(', ')}
                  </p>
                ))}
              </div>
            )}
        </SignalPanel>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data, error } = usePageData('/api/pages/dashboard');
  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { stats, llm_status } = data;

  const headlineMetrics = [
    {
      href: '/documents',
      value: stats.documents,
      label: 'Documents indexed',
      sublabel: 'Full provenance tracked',
      Icon: Files,
      color: 'text-coal',
    },
    {
      href: '/insights',
      value: stats.facts,
      label: 'Facts with receipts',
      sublabel: 'Grounded in sources',
      Icon: Database,
      color: 'text-emerald-700',
    },
    {
      href: '/conflicts',
      value: data.open_conflicts,
      label: 'Conflicts to investigate',
      sublabel: data.open_conflicts === 0 ? 'All sources aligned' : 'Requires officer review',
      Icon: TriangleAlert,
      color: data.open_conflicts ? 'text-red-700' : 'text-emerald-700',
      isConflict: true,
    },
    {
      href: '/insights#quality',
      value: data.extraction_accuracy,
      label: 'Extraction accuracy',
      sublabel: 'Automated evaluation',
      Icon: CheckCircle2,
      color: 'text-emerald-700',
      isPercent: true,
    },
  ];

  return (
    <div className='space-y-6'>
      {/* ── Page Header ── */}
      <PageHeader
        title='Dashboard'
        subtitle="The state of your workspace at a glance: what the library holds, how reliable the extraction is, and what needs an officer's eye."
      />

      {/* ── Top Metric Cards Grid ── */}
      <Rise delay={0.04}>
        <div className='grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4'>
          {headlineMetrics.map(({ href, value, label, sublabel, Icon, color, isPercent, isConflict }) => (
            <Link
              key={label}
              to={href}
              className='group relative overflow-hidden rounded-xl border border-seam bg-white p-4 shadow-card transition-all duration-200 hover:border-coal/50 hover:shadow-lift'
            >
              <div className='flex items-center justify-between'>
                <span className='flex h-8 w-8 items-center justify-center rounded-lg bg-paper text-stone-500 transition-colors group-hover:bg-coalsoft group-hover:text-coal'>
                  <Icon className='h-4 w-4' />
                </span>
                <span className='font-mono text-[10.5px] text-stone-400 group-hover:text-coal transition-colors'>
                  View →
                </span>
              </div>

              <div className='mt-2.5'>
                <div className={color}>
                  {isPercent && value !== 'run eval' ? (
                    <span className='font-mono text-2xl font-bold tracking-tight'>{value}%</span>
                  ) : (
                    <HeadlineNumber value={value} />
                  )}
                </div>
                <p className='mt-0.5 text-[13px] font-semibold text-ink'>{label}</p>
                <p className='font-mono text-[10.5px] text-stone-400'>{sublabel}</p>
              </div>

              {isConflict && value > 0 && (
                <span className='absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-red-600 animate-pulse' />
              )}
            </Link>
          ))}
        </div>
      </Rise>

      {/* ── Organizational Signals (P1 Insight Dashboard) ── */}
      <Rise delay={0.08}>
        <Signals />
      </Rise>

      {/* ── Quick Action Cards ── */}
      <div>
        <div className='mb-2 flex items-center justify-between'>
          <h2 className='text-[13px] font-semibold uppercase tracking-wider text-stone-400'>
            Quick Actions
          </h2>
        </div>
        <AnimatedGroup preset='blur-slide' className='grid gap-3 sm:grid-cols-2 lg:grid-cols-4'>
          {QUICK_ACTIONS.map(({ href, Icon, title, desc, badge }) => (
            <Link
              key={title}
              to={href}
              className='group relative flex flex-col justify-between rounded-xl border border-seam bg-white p-3.5 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:border-coal/60 hover:shadow-lift'
            >
              <div>
                <div className='flex items-center justify-between'>
                  <span className='flex h-8 w-8 items-center justify-center rounded-lg bg-coalsoft text-coal transition-all duration-200 group-hover:bg-coal group-hover:text-white'>
                    <Icon className='h-4 w-4' />
                  </span>
                  <ArrowRight className='h-3.5 w-3.5 text-stone-400 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-coal' />
                </div>
                <h3 className='mt-2.5 text-[14px] font-semibold text-ink group-hover:text-coal transition-colors'>
                  {title}
                </h3>
                <p className='mt-0.5 text-[12px] leading-relaxed text-stone-500'>{desc}</p>
              </div>

              <div className='mt-3 flex items-center justify-between'>
                <span className='rounded-full border border-seam bg-paper px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-500'>
                  {badge}
                </span>
              </div>
            </Link>
          ))}
        </AnimatedGroup>
      </div>

      {/* ── System Status Cards (Embeddings & Language Model) ── */}
      <div>
        <div className='mb-2 flex items-center justify-between'>
          <h2 className='text-[13px] font-semibold uppercase tracking-wider text-stone-400'>
            Intelligence Engines
          </h2>
          <span className='flex items-center gap-1.5 font-mono text-[10.5px] text-emerald-700'>
            <span className='h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse' />
            100% Offline &amp; Local
          </span>
        </div>

        <div className='grid grid-cols-1 gap-4 lg:grid-cols-2'>
          {/* Embeddings Spotlight Card */}
          <Spotlight className='relative rounded-xl border border-seam bg-white p-4 shadow-card transition-all duration-200 hover:border-coal/40 hover:shadow-lift'>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <span className='flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700'>
                  <Database className='h-3.5 w-3.5' />
                </span>
                <div>
                  <h3 className='text-[14px] font-semibold text-ink'>Vector Embeddings</h3>
                  <p className='text-[11px] text-stone-400'>FAISS index &amp; semantic similarity</p>
                </div>
              </div>
              <span className='rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 font-mono text-[10px] font-semibold text-emerald-700'>
                Active
              </span>
            </div>

            <div className='mt-2.5 rounded-lg border border-seam bg-paper/70 p-2'>
              <p className='font-mono text-[10px] uppercase tracking-wider text-stone-400'>Model ID</p>
              <p className='mt-0.5 font-mono text-[12px] font-semibold text-ink break-all'>
                {data.emb_name}
              </p>
            </div>

            <div className='mt-3 grid grid-cols-3 gap-2 border-t border-seam/60 pt-2.5 text-center'>
              <div className='rounded-lg bg-paper p-1.5'>
                <p className='font-mono text-[15px] font-bold text-ink'>{data.emb_dim}</p>
                <p className='mt-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-400'>Dimensions</p>
              </div>
              <div className='rounded-lg bg-paper p-1.5'>
                <p className='font-mono text-[15px] font-bold text-ink'>
                  <AnimatedNumber value={data.vectors} />
                </p>
                <p className='mt-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-400'>Vectors</p>
              </div>
              <div className='rounded-lg bg-paper p-1.5'>
                <p className='font-mono text-[15px] font-bold text-ink'>{stats.chunks}</p>
                <p className='mt-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-400'>Chunks</p>
              </div>
            </div>

            <p className='mt-2.5 flex items-center gap-1.5 font-mono text-[10px] text-stone-400'>
              <ShieldCheck className='h-3 w-3 text-coal' />
              Dense vectors fused with BM25 keyword rankings
            </p>
          </Spotlight>

          {/* Language Model Spotlight Card */}
          <Spotlight className='relative rounded-xl border border-seam bg-white p-4 shadow-card transition-all duration-200 hover:border-coal/40 hover:shadow-lift'>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <span className='flex h-7 w-7 items-center justify-center rounded-lg bg-coalsoft text-coal'>
                  <Cpu className='h-3.5 w-3.5' />
                </span>
                <div>
                  <h3 className='text-[14px] font-semibold text-ink'>Language Model</h3>
                  <p className='text-[11px] text-stone-400'>On-device analysis &amp; generation</p>
                </div>
              </div>
              <span
                className={`rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold ${
                  llm_status.available
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                    : 'border-coalline bg-coalsoft text-coal'
                }`}
              >
                {llm_status.available ? 'Ready' : 'Evidence Only'}
              </span>
            </div>

            <div className='mt-2.5 rounded-lg border border-seam bg-paper/70 p-2'>
              <p className='font-mono text-[10px] uppercase tracking-wider text-stone-400'>Engine / Model</p>
              <p className='mt-0.5 font-mono text-[12px] font-semibold text-ink break-all'>
                {llm_status.model || 'evidence-only extractive mode'}
              </p>
            </div>

            <div className='mt-3 grid grid-cols-3 gap-2 border-t border-seam/60 pt-2.5 text-center'>
              <div className='rounded-lg bg-paper p-1.5'>
                <p className='font-mono text-[12px] font-bold text-ink mt-0.5'>Grounded</p>
                <p className='mt-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-400'>Receipts</p>
              </div>
              <div className='rounded-lg bg-paper p-1.5'>
                <p className='font-mono text-[12px] font-bold text-ink mt-0.5'>Python</p>
                <p className='mt-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-400'>Sandboxed</p>
              </div>
              <div className='rounded-lg bg-paper p-1.5'>
                <p className='font-mono text-[12px] font-bold text-ink mt-0.5'>0 KB</p>
                <p className='mt-0.5 font-mono text-[9.5px] uppercase tracking-wider text-stone-400'>Cloud Data</p>
              </div>
            </div>

            <p className='mt-2.5 flex items-center gap-1.5 font-mono text-[10px] text-stone-400'>
              <ShieldCheck className='h-3 w-3 text-coal' />
              {llm_status.detail || 'Zero cloud telemetry · Local verification only'}
            </p>
          </Spotlight>
        </div>
      </div>

      {/* ── Recent Documents & Pipeline Activity ── */}
      <Rise delay={0.15}>
        <div className='grid grid-cols-1 gap-4 lg:grid-cols-5'>
          {/* Recent Documents */}
          <div className='rounded-xl border border-seam bg-white shadow-card lg:col-span-3 overflow-hidden'>
            <div className='flex items-center justify-between border-b border-seam px-4 py-2.5'>
              <div className='flex items-center gap-2'>
                <h3 className='text-[14px] font-semibold text-ink'>Recent Documents</h3>
                <span className='rounded-full border border-seam bg-paper px-2 py-0.5 font-mono text-[10px] text-stone-500'>
                  {stats.documents} total
                </span>
              </div>
              <Link to='/documents' className='flex items-center gap-1 text-[12.5px] font-medium text-coal hover:underline'>
                View all <ArrowRight className='h-3 w-3' />
              </Link>
            </div>

            <div className='divide-y divide-seam'>
              {data.recent_docs.length === 0 ? (
                <p className='px-4 py-8 text-center text-sm text-stone-500'>
                  Nothing indexed yet — start by ingesting files in the Pipeline.
                </p>
              ) : (
                data.recent_docs.map((d) => (
                  <Link
                    key={d.id}
                    to={`/doc/${d.id}`}
                    className='group flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-paper/70'
                  >
                    <span className='flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-coalsoft text-coal transition-colors group-hover:bg-coal group-hover:text-white'>
                      <FileCheck className='h-4 w-4' />
                    </span>
                    <div className='min-w-0 flex-1'>
                      <p className='truncate text-[13px] font-semibold text-ink transition-colors group-hover:text-coal'>
                        {d.display_name || d.filename}
                      </p>
                      <p className='font-mono text-[10.5px] text-stone-400'>
                        {d.doc_type}
                        {d.subsidiary ? ` · ${d.subsidiary}` : ''}
                        {!d.has_summary ? ' · summary pending' : ''}
                      </p>
                    </div>
                    {d.content_norm && (
                      <span className='hidden rounded-full border border-coalline bg-coalsoft px-2 py-0.5 font-mono text-[9.5px] text-coal sm:block'>
                        {d.content_norm}
                      </span>
                    )}
                    <span className='text-stone-300 transition-transform group-hover:translate-x-0.5 group-hover:text-coal'>
                      ›
                    </span>
                  </Link>
                ))
              )}
            </div>
          </div>

          {/* Pipeline Activity */}
          <div className='rounded-xl border border-seam bg-white shadow-card lg:col-span-2 overflow-hidden flex flex-col justify-between'>
            <div>
              <div className='flex items-center justify-between border-b border-seam px-4 py-2.5'>
                <div className='flex items-center gap-2'>
                  <h3 className='text-[14px] font-semibold text-ink'>Pipeline Activity</h3>
                  <span className='rounded-full border border-seam bg-paper px-2 py-0.5 font-mono text-[10px] text-stone-500'>
                    {data.jobs.length} jobs
                  </span>
                </div>
                <Link to='/pipeline' className='flex items-center gap-1 text-[12.5px] font-medium text-coal hover:underline'>
                  Pipeline <ArrowRight className='h-3 w-3' />
                </Link>
              </div>

              <div className='divide-y divide-seam'>
                {data.jobs.length === 0 ? (
                  <p className='px-4 py-8 text-center text-sm text-stone-500'>No recent jobs.</p>
                ) : (
                  data.jobs.map((j, i) => (
                    <div key={i} className='flex items-center gap-2.5 px-4 py-2 transition-colors hover:bg-paper/40'>
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md ${
                          j.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700'
                            : j.status === 'failed'
                            ? 'bg-red-50 text-red-700'
                            : 'bg-coalsoft text-coal'
                        }`}
                      >
                        {j.status === 'failed' ? (
                          <Alert className='h-3 w-3' />
                        ) : j.status === 'completed' ? (
                          <Check className='h-3 w-3' />
                        ) : (
                          <LoaderCircle className='h-3 w-3 animate-spin' />
                        )}
                      </span>
                      <p className='min-w-0 flex-1 truncate text-[12.5px] font-medium text-ink'>
                        {j.filename || 'unknown file'}
                      </p>
                      <span
                        className={`rounded px-1.5 py-0.2 font-mono text-[9.5px] uppercase font-semibold ${
                          j.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700'
                            : j.status === 'failed'
                            ? 'bg-red-50 text-red-700'
                            : 'bg-coalsoft text-coal'
                        }`}
                      >
                        {j.stage}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className='flex items-center justify-between border-t border-seam bg-paper/40 px-4 py-2 text-[11.5px] text-stone-500'>
              <span className='font-mono text-[10.5px]'>Storage: {data.storage_gb.toFixed(2)} GB</span>
              {stats.failed ? (
                <Link to='/pipeline' className='font-medium text-red-700 hover:underline'>
                  {stats.failed} failed job(s)
                </Link>
              ) : (
                <span className='flex items-center gap-1 font-mono text-[10.5px] text-emerald-700'>
                  <span className='h-1.5 w-1.5 rounded-full bg-emerald-600' /> Operational
                </span>
              )}
            </div>
          </div>
        </div>
      </Rise>
    </div>
  );
}
