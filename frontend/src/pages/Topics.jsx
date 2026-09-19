import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { RefreshCw, Shapes, Eye, Files, Tags, CloudOff, FileText } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button, EmptyState } from '../components/ui.jsx';

export default function Topics() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const scope = params.get('scope') || 'corpus';
  const { data, error, reload } = usePageData(`/api/pages/topics?scope=${encodeURIComponent(scope)}`);
  const [busy, setBusy] = useState(false);
  const [cloudV, setCloudV] = useState(0);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const analyze = async () => {
    setBusy(true);
    try {
      await postJSON('/api/topics/refresh', { scope: scope === 'corpus' ? '' : scope });
      reload();
      setCloudV((v) => v + 1);
    } catch { /* ignore */ }
    setBusy(false);
  };

  const changeScope = (value) => {
    navigate(value && value !== 'corpus' ? `/topics?scope=${encodeURIComponent(value)}` : '/topics');
  };

  return (
    <div>
      <PageHeader
        title='Topics'
        subtitle='What the library keeps talking about: keyword index, vocabulary portrait and document clusters. Analysis runs locally on the embeddings — the Knowledge page maps entities and relations instead.'>
        <div className='flex flex-wrap items-center gap-2'>
          <select
            value={scope !== 'corpus' ? scope : ''}
            onChange={(e) => changeScope(e.currentTarget.value || 'corpus')}
            className='rounded-lg border border-seam bg-surface px-3 py-1.5 text-xs text-ink shadow-card focus:border-coal focus:outline-none'
          >
            <option value=''>Corpus-wide</option>
            {data.subs.map((s) => <option key={s.subsidiary} value={`subsidiary:${s.subsidiary}`}>{s.subsidiary}</option>)}
          </select>
          <Button
            variant='primary'
            size='md'
            disabled={busy}
            onClick={analyze}
            className='px-4'
          >
            <RefreshCw className={`h-3.5 w-3.5 ${busy ? 'animate-spin' : ''}`} />
            {busy ? 'Analyzing…' : 'Analyze'}
          </Button>
        </div>
      </PageHeader>

      <Rise delay={0.05}>
        <Card className='mt-6 p-5'>
          <div className='flex items-center gap-2'>
            <Tags className='h-4 w-4 text-coal' />
            <h2 className='text-sm font-semibold text-ink'>
              Keyword index
              <span className='ml-2 font-mono text-[11px] font-normal text-muted1 tabular-nums'>
                {data.top_keywords.length} terms · {data.n_docs} documents
              </span>
            </h2>
          </div>
          {data.top_keywords.length === 0 ? (
            <p className='mt-2 text-[13px] text-muted1'>No keywords extracted yet — ingest documents first.</p>
          ) : (
            <div className='mt-3 flex flex-wrap gap-1.5'>
              {data.top_keywords.map((k) => (
                <Link
                  key={k.keyword}
                  to={`/search?tag=${encodeURIComponent(k.keyword)}`}
                  className='rounded-full border border-seam bg-paper px-2.5 py-1 text-[12px] text-stone-600 transition-colors hover:border-coalline hover:text-coal'
                >
                  #{k.keyword}
                  <span className='ml-1 font-mono text-[10.5px] text-stone-400 tabular-nums'>{k.n_docs}</span>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </Rise>

      <Rise delay={0.08}>
        <Card className='mt-4 p-5 text-center'>
          <div className='mb-3 flex items-center justify-center gap-2 font-mono text-[10.5px] uppercase tracking-wider text-muted1'>
            <Eye className='h-3.5 w-3.5' /> vocabulary portrait · {scope}
          </div>
          {data.cloud_ready ? (
            <img
              key={cloudV}
              src={`/api/topics/cloud?scope=${encodeURIComponent(scope)}&v=${cloudV}`}
              alt={`Word cloud for ${scope}`}
              className='mx-auto max-w-full rounded-lg border border-seam'
            />
          ) : (
            <EmptyState
              icon={CloudOff}
              title='No vocabulary portrait yet'
              description='Click Analyze above and the most frequent terms in this scope render here as a word cloud.'
              className='border-solid'
            />
          )}
        </Card>
      </Rise>

      <h2 className='mt-10 flex items-center gap-2 text-base font-semibold tracking-tight text-ink'>
        <Shapes className='h-4 w-4 text-coal' /> Document clusters
      </h2>
      {data.clusters.length === 0 ? (
        <Rise delay={0.1}>
          <EmptyState
            icon={Shapes}
            title='No clusters for this scope yet'
            description='Click Analyze and the library is grouped by embedding similarity, each cluster labeled with its shared keyphrases.'
            className='mt-4'
          />
        </Rise>
      ) : (
        <div className='mt-4 grid grid-cols-1 gap-4 md:grid-cols-2'>
          {data.clusters.map((t) => (
            <Rise key={t.id}>
              <Card className='flex h-full flex-col p-5'>
                <h3 className='text-sm font-semibold leading-snug text-ink'>{t.label}</h3>
                <div className='mt-2.5 flex flex-wrap gap-1.5'>
                  {t.keywords.slice(0, 8).map((k) => (
                    <Link key={k} to={`/search?tag=${encodeURIComponent(k)}`}>
                      <Badge variant='coal' className='text-xs transition-colors hover:border-coal'>{k}</Badge>
                    </Link>
                  ))}
                </div>
                <div className='mt-4 space-y-1.5 border-t border-seam pt-3'>
                  {(t.docs || []).map((d) => (
                    <Link
                      key={d.id}
                      to={`/doc/${d.id}`}
                      className='flex items-center gap-2 text-[13px] text-stone-600 transition-colors hover:text-coal'
                    >
                      <FileText className='h-3.5 w-3.5 shrink-0 text-stone-400' />
                      <span className='truncate'>{d.filename}</span>
                    </Link>
                  ))}
                </div>
                <p className='mt-3 flex items-center gap-1.5 font-mono text-xs text-muted1 tabular-nums'>
                  <Files className='h-3.5 w-3.5 text-muted1' /> {(t.docs || t.doc_ids).length} document{(t.docs || t.doc_ids).length !== 1 ? 's' : ''}
                </p>
              </Card>
            </Rise>
          ))}
        </div>
      )}
    </div>
  );
}
