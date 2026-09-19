import { useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { Pencil, MessageCircle, ExternalLink, Trash2, RefreshCw, ChevronDown } from 'lucide-react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, PageHeader, Loading, ErrorBox, Card, Badge, Button, Table, TableHead, TableBody, TableRow, TableHeader, TableCell } from '../components/ui.jsx';
import { Disclosure, DisclosureTrigger, DisclosureContent } from '../components/motion/disclosure.jsx';
import { AnimatedBackground } from '../components/motion/animated-background.jsx';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from '../components/motion/dialog.jsx';
import { MorphingPopover, MorphingPopoverTrigger, MorphingPopoverContent } from '../components/motion/morphing-popover.jsx';
import { ScrollProgress } from '../components/motion/scroll-progress.jsx';

export default function Viewer() {
  const { docId: _paramDocId } = useParams();
  const pathDocId = window.location.pathname.split('/').filter(Boolean)[1];
  const docId = _paramDocId || pathDocId || '';
  const [params, setParams] = useSearchParams();
  const page = params.get('page') ? Number(params.get('page')) : null;
  const sheet = params.get('sheet') ? Number(params.get('sheet')) : null;
  const qs = new URLSearchParams();
  if (page) qs.set('page', page);
  if (sheet) qs.set('sheet', sheet);
  const { data, error } = usePageData(`/api/pages/doc/${docId}${qs.toString() ? `?${qs}` : ''}`);
  const [name, setName] = useState('');

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { doc, pages, sheets, elements, tables, reading_elements: reading, kw_list: kwList } = data;
  const title = doc.display_name || doc.filename;
  const isPdf = ['pdf', 'digital_pdf', 'mixed_pdf', 'scanned_pdf'].includes(doc.doc_type);
  const isSheet = ['xlsx', 'csv'].includes(doc.doc_type);
  const activePage = page || (isPdf && pages.length ? pages[0].page_no : null);
  const pinfo = pages.find((p) => p.page_no === activePage);
  const maxRow = tables.length ? Math.max(...tables.flatMap((t) => t.rows.map((r) => r.row_idx))) : -1;

  const doRename = async (e) => {
    e.preventDefault();
    await postJSON(`/api/documents/${doc.id}/rename`, { display_name: name });
    window.location.reload();
  };
  const doDelete = async () => {
    await postJSON(`/api/documents/${doc.id}/delete`);
    window.location.href = '/documents';
  };
  const doSummarize = async () => {
    await postJSON(`/api/documents/${doc.id}/summarize`);
    window.location.reload();
  };

  return (
    <div>
      <ScrollProgress />
      <Rise>
        <PageHeader
          title={title}
          subtitle={`${doc.filename} · ${doc.sha256.slice(0, 16)}…`}
        >
          <div className='relative flex flex-wrap items-center gap-2'>
            <MorphingPopover>
              <MorphingPopoverTrigger asChild>
                <Button variant='ghost' size='sm' icon={Pencil}>
                  Rename
                </Button>
              </MorphingPopoverTrigger>
              <MorphingPopoverContent className='right-0 w-72'>
                <form onSubmit={doRename} className='flex gap-2 p-1'>
                  <input value={name} onChange={(e) => setName(e.target.value)} maxLength={200} required autoFocus
                         placeholder={title}
                         className='min-w-0 flex-1 rounded-lg border border-seam bg-paper px-2.5 py-1.5 text-sm focus:border-coal focus:outline-none' />
                  <Button type='submit' size='sm'>Save</Button>
                </form>
              </MorphingPopoverContent>
            </MorphingPopover>
            <Button to={`/ask?doc=${doc.id}`} variant='ghost' size='sm' icon={MessageCircle}>
              Ask About This Document
            </Button>
            <Button href={`/documents/${doc.id}/original`} target='_blank' rel='noreferrer' variant='ghost' size='sm' icon={ExternalLink}>
              Open Original
            </Button>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant='danger-ghost' size='sm' icon={Trash2}>
                  Delete
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete this document?</DialogTitle>
                  <DialogDescription>
                    “{title}” and all its extracted data will be removed. This cannot be undone.
                  </DialogDescription>
                </DialogHeader>
                <div className='mt-5 flex justify-end gap-2'>
                  <DialogClose asChild>
                    <Button variant='ghost' size='sm'>Keep it</Button>
                  </DialogClose>
                  <Button variant='danger' size='sm' onClick={doDelete}>
                    Delete
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </PageHeader>
      </Rise>

      <Rise delay={0.04}>
        <div className='mt-3 flex flex-wrap gap-2'>
          <Badge variant='coal'>{doc.doc_type}</Badge>
          {doc.content_norm && (
            <Badge variant='neutral' title='The normalized representation this file became inside the intelligence layer'>
              normalized: {doc.content_norm}
            </Badge>
          )}
          {doc.subsidiary && <Badge variant='neutral'>{doc.subsidiary}</Badge>}
          {doc.doc_date_raw && <Badge variant='neutral' className='font-mono'>{doc.doc_date_raw}</Badge>}
          {doc.version_group_id && (doc.is_current_version
            ? <Badge variant='ok'>current version</Badge>
            : <Badge variant='neutral' className='line-through'>superseded</Badge>)}
        </div>
      </Rise>

      <Rise delay={0.08}>
        <Card className='mt-5 p-5'>
          <div className='flex items-center justify-between gap-3'>
            <h2 className='text-[15px] font-semibold text-ink'>Summary</h2>
            <Button variant='ghost' size='sm' icon={RefreshCw} onClick={doSummarize}>
              {doc.summary ? 'Regenerate' : 'Generate Summary'}
            </Button>
          </div>
          {doc.summary ? (
            <p className='mt-2 max-w-[85ch] text-[14px] leading-relaxed text-stone-700'>{doc.summary}</p>
          ) : (
            <p className='mt-2 text-[13.5px] text-stone-500'>No summary yet. It becomes part of the searchable index, so plain-language queries can find this document even when the words never appear in it.</p>
          )}
          {kwList.length > 0 && (
            <div className='mt-3 flex flex-wrap gap-1.5'>
              {kwList.map((kw) => (
                <Link key={kw} to={`/search?tag=${encodeURIComponent(kw)}`} className='rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 text-[11.5px] text-coal hover:bg-amber-100'>#{kw}</Link>
              ))}
            </div>
          )}
        </Card>
      </Rise>

      <Rise delay={0.12}>
        <Disclosure className='mt-4 rounded-xl border border-seam bg-white shadow-card'>
          <DisclosureTrigger className='px-5 py-3.5 text-[14px] font-semibold'>
            <span>Metadata &amp; Provenance</span><ChevronDown className='h-4 w-4 text-stone-400' />
          </DisclosureTrigger>
          <DisclosureContent>
            <dl className='grid grid-cols-1 gap-x-10 gap-y-2 border-t border-seam px-5 py-4 text-[13px] sm:grid-cols-2'>
              {[
                ['Original file', doc.filename],
                ['File type', <span className='font-mono'>{doc.doc_type}</span>],
                ['Normalized representation', doc.content_norm || '-'],
                ['Document ID (SHA-256)', <span className='font-mono text-[12px]'>{doc.sha256.slice(0, 24)}…</span>],
                ['Pages', <span className='font-mono'>{doc.page_count || '-'}</span>],
                ['OCR pages', <span className='font-mono'>{doc.ocr_pages || '-'}</span>],
                ['Processing status', <span className='font-mono'>{doc.status}</span>],
                ['Ingested', <span className='font-mono'>{doc.upload_ts}</span>],
                ['Source of truth', <span className='font-mono text-[12px]'>data/files/{doc.sha256.slice(0, 12)}…/original.{doc.filename.split('.').pop()}</span>],
              ].map(([k, v]) => (
                <div key={k} className='flex justify-between gap-4'><dt className='text-stone-500'>{k}</dt><dd className='text-right'>{v}</dd></div>
              ))}
            </dl>
          </DisclosureContent>
        </Disclosure>
      </Rise>

      {isPdf && pages.length > 0 && pages.some((p) => p.summary) && (
        <Rise delay={0.1}>
          <div className='mt-4 rounded-xl border border-seam bg-white p-5 shadow-card'>
            <h2 className='text-[15px] font-semibold'>Page Summaries</h2>
            <p className='mt-1 text-[12.5px] text-stone-500'>Each page summarized by the configured LLM and indexed for search. Attached to the document summary above.</p>
            <div className='mt-3 space-y-2.5'>
              {pages.filter((p) => p.summary).map((p) => (
                <div key={p.page_no} className='border-l-2 border-coalline pl-3'>
                  <button onClick={() => setParams({ page: String(p.page_no) })}
                          className='font-mono text-[11px] font-semibold uppercase tracking-wide text-coal hover:underline'>
                    Page {p.page_no}
                  </button>
                  <p className='mt-0.5 text-[13.5px] leading-relaxed text-stone-700'>{p.summary}</p>
                </div>
              ))}
            </div>
          </div>
        </Rise>
      )}

      {isPdf && pages.length > 0 && (
        <Rise delay={0.14}>
          <div className='mt-6 flex flex-wrap items-center gap-1'>
            <span className='mr-1 font-mono text-[11px] uppercase tracking-wide text-stone-400'>page</span>
            <AnimatedBackground defaultValue={String(activePage)} className='flex flex-wrap items-center gap-1'
              transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}>
              {pages.map((p) => (
                <button key={p.page_no} data-id={String(p.page_no)} onClick={() => setParams({ page: String(p.page_no) })}
                        className={`rounded-md border px-2.5 py-1 font-mono text-[12px] transition-colors ${activePage === p.page_no ? 'border-coal text-coal' : 'border-seam bg-white text-stone-600 hover:border-coal hover:text-coal'}`}
                        title={p.ocr_used ? 'OCR' : 'digital text'}>{p.page_no}</button>
              ))}
            </AnimatedBackground>
          </div>
          <iframe id='preview' src={`/documents/${doc.id}/original#page=${activePage}`}
                  className='mt-4 h-[720px] w-full rounded-xl border border-seam bg-white shadow-card' title='PDF preview' />
          {pinfo && (
            <div className='mt-3 flex flex-wrap items-center gap-2 text-[12px]'>
              {pinfo.page_class && pinfo.page_class !== 'TEXT_ONLY' && (
                <span className='rounded-full border border-seam bg-white px-3 py-1 font-mono text-[11px] text-stone-500'>
                  {pinfo.page_class.replaceAll('_', ' ').toLowerCase()}
                </span>
              )}
              {pinfo.ocr_used ? (
                <span className='rounded-full border border-coalline bg-coalsoft px-3 py-1 font-mono text-[11px] text-coal'>
                  page {activePage} is OCR{pinfo.avg_confidence ? ` · confidence ${Number(pinfo.avg_confidence).toFixed(1)}%` : ''}
                </span>
              ) : (
                <span className='rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-mono text-[11px] text-emerald-700'>page {activePage} has a digital text layer</span>
              )}
            </div>
          )}
        </Rise>
      )}

      {page && !sheet && (
        <Rise delay={0.1}>
          <div className='mt-6 rounded-xl border border-seam bg-white p-6 shadow-card'>
            <h2 className='text-[15px] font-semibold'>Extracted Content · Page {page}</h2>
            {pinfo?.summary && (
              <div className='mt-3 rounded-lg border border-coalline bg-coalsoft px-4 py-3'>
                <p className='font-mono text-[10px] uppercase tracking-wide text-coal font-semibold'>Page summary (LLM)</p>
                <p className='mt-1 text-[13.5px] leading-relaxed text-ink'>{pinfo.summary}</p>
              </div>
            )}
            <div className='mt-3 space-y-3'>
              {elements.length === 0 ? (
                <p className='text-[13.5px] text-muted1'>No elements extracted on this page.</p>
              ) : elements.map((el, i) => (
                <div key={i} className='border-l-2 border-coal/30 pl-3'>
                  <span className='font-mono text-[10px] uppercase tracking-wide text-muted1'>{el.element_type}</span>
                  {el.method && el.method !== 'native' && <span className='ml-2 rounded-full border border-coalline bg-coalsoft px-1.5 py-px font-mono text-[10px] text-coal'>{el.method}</span>}
                  {el.section_path && <span className='ml-2 font-mono text-[10px] text-muted1'>{el.section_path}</span>}
                  <p className='mt-0.5 text-[14px] leading-relaxed text-ink'>{(el.text || '').slice(0, 800)}</p>
                </div>
              ))}
            </div>
          </div>
        </Rise>
      )}

      {isSheet && sheets.length > 0 && (
        <Rise delay={0.14}>
          <div className='mt-6 flex flex-wrap items-center gap-1.5'>
            <span className='mr-1 font-mono text-[11px] uppercase tracking-wide text-muted1'>sheet</span>
            <AnimatedBackground defaultValue={sheet != null ? String(sheet) : undefined} className='flex flex-wrap items-center gap-1.5'
              transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}>
              {sheets.map((s) => (
                <button key={s.sheet_no} data-id={String(s.sheet_no)} onClick={() => setParams({ sheet: String(s.sheet_no) })}
                        className={`rounded-md border px-2.5 py-1 font-mono text-xs transition-colors ${sheet === s.sheet_no ? 'border-coal text-coal font-semibold shadow-xs' : 'border-seam bg-surface text-ink hover:border-coal hover:text-coal'}`}>{s.sheet_no}</button>
              ))}
            </AnimatedBackground>
          </div>
        </Rise>
      )}

      {sheet != null && (tables.length ? tables.map((t, i) => (
        <Rise key={t.id || i} delay={0.1 + i * 0.05}>
          <Card className='mt-6 overflow-hidden p-0'>
            <div className='flex items-center justify-between border-b border-seam bg-paper/60 px-5 py-3 text-xs font-semibold text-ink'>
              <div className='flex items-center gap-2'>
                <span>Table {t.table_idx + 1}</span>
                {t.section_path && <span className='font-normal font-mono text-[11px] text-muted1'>{t.section_path}</span>}
              </div>
              <span className='font-normal font-mono text-[11px] text-muted1'>{t.n_rows} rows × {t.n_cols} cols</span>
            </div>
            <div className='max-h-[560px] overflow-auto'>
              <table className='w-full text-left text-xs text-ink'>
                <thead className='sticky top-0 z-10 border-b border-seam bg-paper font-mono text-[11px] uppercase tracking-wider text-muted1'>
                  <tr>
                    {t.headers.map((h, hi) => <th key={hi} className='px-4 py-2.5 font-medium'>{h}</th>)}
                  </tr>
                </thead>
                <tbody className='divide-y divide-seam bg-surface'>
                  {Array.from({ length: maxRow + 1 }, (_, r) => (
                    <tr key={r} className='transition-colors hover:bg-paper/50 odd:bg-paper/20'>
                      {t.rows.filter((c) => c.row_idx === r).map((c, ci) => (
                        <td key={ci} className={`whitespace-nowrap px-4 py-2.5 ${c.value_norm != null ? 'font-mono tabular-nums text-coal font-medium' : ''}`}>{c.value_raw}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </Rise>
      )) : sheet != null && (
        <Card className='mt-6 p-8 text-center text-sm text-muted1'>
          No tables were detected on this sheet.
        </Card>
      ))}

      {((isPdf || isSheet) && !page && !sheet) && (
        <Rise delay={0.1}>
          <Card className='mt-6 p-10 text-center text-sm text-muted1'>
            {isSheet ? 'Pick a sheet above to see it as a spreadsheet.' : 'Select a page above to inspect its extraction with provenance.'}
          </Card>
        </Rise>
      )}

      {!isPdf && !isSheet && (
        <Rise delay={0.14}>
          <Card className='mt-6 p-6'>
            <h2 className='text-sm font-semibold uppercase tracking-wider text-muted1'>Document Reading View</h2>
            {doc.doc_type === 'image' && pages.length > 0 && pages[0].image_path && (
              <img src={`/page_image/${doc.id}/${pages[0].image_path.split('/').pop()}`}
                   className='mt-4 max-h-[560px] rounded-lg border border-seam' alt={title} />
            )}
            <div className='mt-4 space-y-4'>
              {reading.length === 0 ? (
                <p className='text-sm text-muted1'>No text content was extracted from this file.</p>
              ) : reading.map((el, i) => el.element_type === 'HEADING' ? (
                <h3 key={i} className='mt-6 text-lg font-semibold tracking-tight text-ink'>{el.text}</h3>
              ) : el.element_type === 'TABLE' ? (
                <p key={i} className='rounded-lg border border-coalline bg-coalsoft px-4 py-2.5 text-xs text-coal'>Table extracted on this document. Its cells are searchable and citable across the system.</p>
              ) : (
                <p key={i} className='max-w-[85ch] text-sm leading-relaxed text-ink'>{el.text}</p>
              ))}
            </div>
          </Card>
        </Rise>
      )}
    </div>
  );
}
