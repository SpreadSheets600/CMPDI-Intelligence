import { useState } from 'react';
import { RefreshCw, Shapes, Eye, Files } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button, EmptyState } from '../components/ui.jsx';
import { Carousel, CarouselContent, CarouselItem, CarouselNavigation, CarouselIndicator } from '../components/motion/carousel.jsx';

export default function Topics() {
  const scope = new URLSearchParams(window.location.search).get('scope') || 'corpus';
  const { data, error, reload } = usePageData(`/api/pages/topics?scope=${encodeURIComponent(scope)}`);
  const [busy, setBusy] = useState(false);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const analyze = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await postJSON('/api/topics/refresh', { scope: e.currentTarget.scope.value });
      reload();
    } catch { /* ignore */ }
    setBusy(false);
  };

  return (
    <div>
      <PageHeader
        title='Topics'
        subtitle='Recurring keywords, themes and document clusters across the library. Analysis runs locally on the embeddings.'>
        <form onSubmit={analyze} className='flex flex-wrap items-center gap-2'>
          <select
            name='scope'
            defaultValue={scope !== 'corpus' ? scope : ''}
            className='rounded-lg border border-seam bg-surface px-3 py-1.5 text-xs text-ink shadow-card focus:border-coal focus:outline-none'
          >
            <option value=''>Corpus-wide</option>
            {data.subs.map((s) => <option key={s.subsidiary} value={`subsidiary:${s.subsidiary}`}>{s.subsidiary}</option>)}
          </select>
          <Button
            type='submit'
            variant='primary'
            size='md'
            disabled={busy}
            className='px-4'
          >
            <RefreshCw className='h-3.5 w-3.5' /> Analyze
          </Button>
        </form>
      </PageHeader>

      <Rise delay={0.05}>
        <Card className='mt-8 p-5 text-center'>
          <div className='mb-3 flex items-center justify-center gap-2 font-mono text-[10.5px] uppercase tracking-wider text-muted1'>
            <Eye className='h-3.5 w-3.5' /> word cloud · {scope}
          </div>
          <img
            src={`/api/topics/cloud?scope=${encodeURIComponent(scope)}`}
            alt={`Word cloud for ${scope}`}
            className='mx-auto max-w-full rounded-lg border border-seam'
          />
        </Card>
      </Rise>

      <h2 className='mt-10 flex items-center gap-2 text-base font-semibold tracking-tight text-ink'>
        <Shapes className='h-4 w-4 text-coal' /> Clusters
      </h2>
      {data.clusters.length === 0 ? (
        <Rise delay={0.08}>
          <EmptyState
            icon={Shapes}
            title='No cluster analysis yet'
            description='Pick a scope above and click Analyze; clustering runs on the local embeddings.'
            className='mt-4'
          />
        </Rise>
      ) : (
        <Rise delay={0.08}>
          <Carousel className='mt-4'>
            <CarouselContent>
              {data.clusters.map((t) => (
                <CarouselItem key={t.id} className='pr-4'>
                  <Card className='p-5'>
                    <h3 className='text-sm font-semibold text-ink'>{t.label}</h3>
                    <div className='mt-2.5 flex flex-wrap gap-1.5'>
                      {t.keywords.map((k) => (
                        <Badge key={k} variant='coal' className='text-xs'>
                          {k}
                        </Badge>
                      ))}
                    </div>
                    <div className='mt-4 flex items-center justify-between'>
                      <p className='flex items-center gap-1.5 font-mono text-xs text-muted1 tabular-nums'>
                        <Files className='h-3.5 w-3.5 text-muted1' /> {t.doc_ids.length} document{t.doc_ids.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </Card>
                </CarouselItem>
              ))}
            </CarouselContent>
            <div className='mt-3 flex items-center justify-between'>
              <CarouselIndicator />
              <CarouselNavigation />
            </div>
          </Carousel>
        </Rise>
      )}
    </div>
  );
}
