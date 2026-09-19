import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Search, X, Tags, FileText, Table2, ScanText, ExternalLink, Trash2,
  FolderOpen, Upload, MessageCircle, Files,
} from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button, EmptyState } from '../components/ui.jsx';
import { AnimatedGroup } from '../components/motion/animated-group.jsx';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from '../components/motion/dialog.jsx';

function DeleteDialog({ name, onConfirm }) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className='rounded-md p-1.5 text-stone-400 transition-colors hover:bg-red-50 hover:text-red-700'>
        <span title='Delete'><Trash2 className='h-4 w-4' /></span>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete this document?</DialogTitle>
          <DialogDescription>
            “{name}” and all its extracted data — pages, tables, chunks, facts — will be removed. This cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div className='mt-5 flex justify-end gap-2'>
          <DialogClose asChild>
            <Button variant='ghost' size='sm'>Keep it</Button>
          </DialogClose>
          <Button
            variant='danger'
            size='sm'
            onClick={() => { setOpen(false); onConfirm(); }}
          >
            Delete
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function Documents() {
  const [filters, setFilters] = useState(() => ({
    q: new URLSearchParams(window.location.search).get('q') || '',
    type: new URLSearchParams(window.location.search).get('type') || '',
    subsidiary: new URLSearchParams(window.location.search).get('subsidiary') || '',
  }));
  const tag = new URLSearchParams(window.location.search).get('tag') || '';
  const qs = new URLSearchParams(Object.entries(filters).filter(([, v]) => v)).toString();
  const { data, error, reload } = usePageData(`/api/pages/documents${qs ? `?${qs}` : ''}${tag ? `${qs ? '&' : '?'}tag=${encodeURIComponent(tag)}` : ''}`);
  const [picked, setPicked] = useState([]);
  const navigate = useNavigate();

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { docs, kw_map: kwMap, type_counts: typeCounts, subsidiaries, doc_types: docTypes } = data;
  const setFilter = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));

  const del = async (d) => {
    await postJSON(`/api/documents/${d.id}/delete`);
    setPicked((p) => p.filter((x) => x !== d.id));
    reload();
  };

  const toggle = (id) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const clearFilters = () => {
    setFilters({ q: '', type: '', subsidiary: '' });
    navigate('/documents');
  };
  const hasFilters = !!(filters.q || filters.type || filters.subsidiary || tag);

  const inputCls = 'rounded-lg border border-seam bg-white px-3 py-2 text-sm shadow-card focus:border-coal focus:outline-none';

  return (
    <div>
      <PageHeader
        title='Documents'
        subtitle='Your indexed library. Version chains are detected automatically; superseded revisions stay searchable but never answer questions by default.'
      />

      <Rise delay={0.05}>
        <div className='mt-6 flex flex-wrap items-center gap-2'>
          <label className='relative w-full min-w-0 flex-1 sm:max-w-xs'>
            <Search className='pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400' />
            <input value={filters.q} onChange={setFilter('q')}
                   onKeyDown={(e) => e.key === 'Enter' && navigate(`/documents?${qs}`)}
                   placeholder='Search by name...'
                   className='w-full rounded-lg border border-seam bg-white py-2 pl-9 pr-3 text-sm shadow-card placeholder:text-stone-400 focus:border-coal focus:outline-none' />
          </label>
          <select value={filters.type} onChange={(e) => { setFilter('type')(e); setTimeout(() => navigate(`/documents?${new URLSearchParams({ ...filters, type: e.target.value }).filter(([, v]) => v)}`), 0); }} className={inputCls}>
            <option value=''>All types</option>
            {docTypes.map((t) => (
              <option key={t.doc_type} value={t.doc_type}>{t.doc_type} ({typeCounts[t.doc_type] || 0})</option>
            ))}
          </select>
          <select value={filters.subsidiary} onChange={(e) => { setFilter('subsidiary')(e); setTimeout(() => navigate(`/documents?${new URLSearchParams({ ...filters, subsidiary: e.target.value }).filter(([, v]) => v)}`), 0); }} className={inputCls}>
            <option value=''>All subsidiaries</option>
            {subsidiaries.map((s) => (
              <option key={s.subsidiary} value={s.subsidiary}>{s.subsidiary}</option>
            ))}
          </select>
          {(filters.q || filters.type || filters.subsidiary || tag) && (
            <button
              type='button'
              onClick={clearFilters}
              className='flex items-center gap-1.5 rounded-lg border border-seam px-3 py-2 text-[12.5px] font-medium text-stone-500 transition-colors hover:border-red-300 hover:text-red-700'
            >
              <X className='h-3.5 w-3.5' /> Clear
            </button>
          )}
        </div>
      </Rise>

      {tag && (
        <Rise delay={0.08}>
          <div className='mt-4'>
            <span className='inline-flex items-center gap-2 rounded-full border border-coalline bg-coalsoft px-3 py-1.5 text-[12.5px] text-coal'>
              <Tags className='h-3.5 w-3.5' /> filtered by tag
              <Link to='/documents' className='ml-1 text-coal/70 hover:text-coal'><X className='h-3.5 w-3.5' /></Link>
            </span>
          </div>
        </Rise>
      )}

      {/* floating selection bar */}
      <div className={`fixed bottom-6 left-1/2 z-40 -translate-x-1/2 items-center gap-3 rounded-full border border-sideline bg-side px-5 py-2.5 text-sidetext shadow-lift ${picked.length ? 'flex' : 'hidden'}`}>
        <span className='text-[13px] font-mono tabular-nums'><strong>{picked.length}</strong> selected</span>
        <Button
          to={`/ask?docs=${picked.join(',')}`}
          size='sm'
          icon={MessageCircle}
        >
          Ask Across Selection
        </Button>
      </div>

      {docs.length === 0 ? (
        <Rise delay={0.1}>
          <div className='mt-8'>
            {hasFilters ? (
              <EmptyState
                icon={Search}
                title='No documents match these filters'
                description='Try a shorter search term, another type or subsidiary — or clear the filters to browse the whole library.'
                action={
                  <Button variant='secondary' onClick={clearFilters} icon={X}>
                    Clear filters
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={FolderOpen}
                title='Your library is empty'
                description='Drop PDFs, scans, Word, Excel or CSV files into the pipeline and they will be parsed, indexed and appear here within seconds.'
                action={
                  <Button to='/pipeline' icon={Upload}>
                    Go to Pipeline
                  </Button>
                }
              />
            )}
          </div>
        </Rise>
      ) : (
        <AnimatedGroup preset='blur-slide' className='mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3'>
          {docs.map((d) => {
            const isDoc = ['pdf', 'digital_pdf', 'docx'].includes(d.doc_type);
            const isSheet = ['xlsx', 'csv'].includes(d.doc_type);
            return (
              <Card
                key={d.id}
                as='article'
                interactive
                className='group relative flex h-full flex-col p-5'
              >
                <label title='Select for comparison or scoped ask'
                       className='absolute right-3 top-3 z-10 cursor-pointer rounded-md border border-seam bg-white/90 p-1.5 opacity-0 transition-opacity group-hover:opacity-100 max-md:opacity-100'>
                  <input type='checkbox' checked={picked.includes(d.id)} onChange={() => toggle(d.id)}
                         className='h-3.5 w-3.5 accent-[rgb(var(--c-coal))]' />
                </label>
                <div className='flex items-start gap-3'>
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${isDoc ? 'bg-coalsoft text-coal' : isSheet ? 'bg-emerald-50 text-emerald-700' : 'bg-paper text-stone-500'}`}>
                    {isDoc ? <FileText className='h-5 w-5' /> : isSheet ? <Table2 className='h-5 w-5' /> : <ScanText className='h-5 w-5' />}
                  </span>
                  <div className='min-w-0 flex-1'>
                    <Link to={`/doc/${d.id}`}
                          className='line-clamp-2 font-medium leading-snug text-ink transition-colors hover:text-coal'>{d.display_name || d.filename}</Link>
                    <p className='mt-0.5 truncate font-mono text-[11px] text-stone-400' title={d.filename}>{d.filename}</p>
                  </div>
                </div>

                <div className='flex-1'>
                  <div className='mt-3.5 flex flex-wrap items-center gap-1.5'>
                    <Badge variant='coal'>
                      {d.content_norm || d.doc_type}
                    </Badge>
                    {d.subsidiary && (
                      <Badge variant='neutral'>
                        {d.subsidiary}
                      </Badge>
                    )}
                    {d.doc_date_raw && (
                      <Badge variant='neutral' className='font-mono'>
                        {d.doc_date_raw}
                      </Badge>
                    )}
                  </div>

                  {(kwMap[d.id] || []).length > 0 && (
                    <div className='mt-2.5 flex flex-wrap items-center gap-1.5'>
                      {kwMap[d.id].slice(0, 3).map((kw) => (
                        <Link
                          key={kw}
                          to={`/search?tag=${encodeURIComponent(kw)}`}
                          className='rounded-full border border-seam bg-paper px-2 py-0.5 text-[10.5px] text-stone-500 transition-colors hover:border-coalline hover:text-coal'
                        >
                          #{kw}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>

                <div className='mt-5 flex items-center justify-between gap-2 border-t border-seam pt-3.5'>
                  <div className='flex items-center gap-3 font-mono tabular-nums text-[11px] text-stone-400'>
                    {!!d.page_count && (
                      <span className='flex items-center gap-1' title='pages'>
                        <Files className='h-3 w-3' />
                        {d.page_count}
                      </span>
                    )}
                    {!!d.ocr_pages && <span title='OCR pages'>OCR {d.ocr_pages}</span>}
                    {d.version_group_id && !d.is_current_version ? (
                      <Badge variant='neutral' className='line-through text-[10px]'>
                        superseded
                      </Badge>
                    ) : d.status === 'failed' ? (
                      <Badge variant='bad' className='text-[10px]'>
                        failed
                      </Badge>
                    ) : null}
                  </div>
                  <div className='flex items-center gap-1 opacity-0 transition-opacity duration-200 group-hover:opacity-100 max-md:opacity-100'>
                    <Link
                      to={`/doc/${d.id}`}
                      title='Open'
                      className='rounded-md p-1.5 text-stone-400 transition-colors hover:bg-coalsoft hover:text-coal'
                    >
                      <ExternalLink className='h-4 w-4' />
                    </Link>
                    <DeleteDialog name={d.display_name || d.filename} onConfirm={() => del(d)} />
                  </div>
                </div>
              </Card>
            );
          })}
        </AnimatedGroup>
      )}
    </div>
  );
}
