import { useState } from 'react';
import { usePageData } from '../hooks/useData.js';
import { postJSON } from '../api.js';
import { Rise, Reveal, PageHeader, Loading, ErrorBox, Card, Button } from '../components/ui.jsx';
import { Disclosure, DisclosureTrigger, DisclosureContent } from '../components/motion/disclosure.jsx';
import { ChevronDown } from 'lucide-react';

function InnerSection({ title, children }) {
  const [open, setOpen] = useState(true);
  return (
    <Card className='overflow-hidden p-0'>
      <Disclosure open={open} onOpenChange={setOpen}>
        <DisclosureTrigger className='flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-surface/50'>
          <span className='text-sm font-semibold text-ink'>{title}</span>
          <ChevronDown className={`h-4 w-4 text-muted1 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
        </DisclosureTrigger>
        <DisclosureContent className='border-t border-seam px-5 pb-5 pt-4'>{children}</DisclosureContent>
      </Disclosure>
    </Card>
  );
}

export default function Settings() {
  const { data, error, reload } = usePageData('/api/pages/settings');
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { settings, llm_status: llmStatus } = data;

  const save = async (e) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    try {
      const res = await postJSON('/api/settings', Object.fromEntries(f));
      setNotice(res.error ? { bad: true, msg: res.error } : { bad: false, msg: res.message });
      reload();
    } catch (err) { setNotice({ bad: true, msg: err.message }); }
    setBusy(false);
  };

  const backfill = async () => {
    setBusy(true);
    try {
      const res = await postJSON('/api/settings/summaries');
      setNotice({ bad: false, msg: `Generated ${res.generated} document summary(ies).` });
      reload();
    } catch (err) { setNotice({ bad: true, msg: err.message }); }
    setBusy(false);
  };

  return (
    <div>
      <PageHeader
        title='Settings'
        subtitle='Only controls with a real effect live here. Changes apply immediately; environment variables remain the defaults underneath.'
      />

      {notice && (
        <div className={`mt-4 rounded-xl border px-4 py-3 text-xs font-medium ${notice.bad ? 'border-rose-500/20 bg-rose-500/10 text-rose-600 dark:text-rose-400' : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'}`}>
          {notice.msg}
        </div>
      )}

      <div className='mt-6 grid grid-cols-1 gap-5 lg:grid-cols-3'>
        <form onSubmit={save} className='space-y-5 lg:col-span-2'>
          <Rise delay={0.04}>
            <InnerSection title='Language Model'>
              <div className='space-y-4'>
                <label className='block'>
                  <span className='text-xs font-medium text-muted0'>Provider</span>
                  <select
                    name='llm_provider'
                    defaultValue={settings.llm_provider || settings.llm_backend}
                    className='mt-1.5 w-full rounded-lg border border-seam bg-surface px-3 py-2 text-xs text-ink shadow-card focus:border-coal focus:outline-none transition-colors'
                  >
                    <option value='auto'>Auto: Ollama, then OpenAI-compatible, then local Hugging Face, then evidence-only</option>
                    <option value='ollama'>Ollama: local server + configurable model</option>
                    <option value='huggingface'>Hugging Face: locally downloaded model, CPU or GPU</option>
                    <option value='openai_compatible'>OpenAI-compatible API: endpoint + model + env key</option>
                    <option value='none'>None (evidence-only): no generation; verbatim cited evidence only</option>
                  </select>
                </label>
                <label className='block'>
                  <span className='text-xs font-medium text-muted0'>Ollama model</span>
                  <input
                    name='ollama_model'
                    defaultValue={settings.ollama_model}
                    className='mt-1.5 w-full rounded-lg border border-seam bg-surface px-3 py-2 font-mono text-xs text-ink placeholder:text-muted2 shadow-card focus:border-coal focus:outline-none transition-colors'
                  />
                </label>
                <label className='block'>
                  <span className='text-xs font-medium text-muted0'>Ollama URL</span>
                  <input
                    name='ollama_url'
                    defaultValue={settings.ollama_url}
                    className='mt-1.5 w-full rounded-lg border border-seam bg-surface px-3 py-2 font-mono text-xs text-ink placeholder:text-muted2 shadow-card focus:border-coal focus:outline-none transition-colors'
                  />
                </label>
                <label className='block'>
                  <span className='text-xs font-medium text-muted0'>Hugging Face model (id or local path)</span>
                  <input
                    name='hf_model'
                    defaultValue={settings.hf_model}
                    placeholder='e.g. Qwen/Qwen2.5-1.5B-Instruct or /models/mistral'
                    className='mt-1.5 w-full rounded-lg border border-seam bg-surface px-3 py-2 font-mono text-xs text-ink placeholder:text-muted2 shadow-card focus:border-coal focus:outline-none transition-colors'
                  />
                </label>
                <label className='block'>
                  <span className='text-xs font-medium text-muted0'>OpenAI-compatible base URL</span>
                  <input
                    name='openai_base_url'
                    defaultValue={settings.openai_base_url}
                    placeholder='e.g. https://inference.example.gov/v1'
                    className='mt-1.5 w-full rounded-lg border border-seam bg-surface px-3 py-2 font-mono text-xs text-ink placeholder:text-muted2 shadow-card focus:border-coal focus:outline-none transition-colors'
                  />
                </label>
                <label className='block'>
                  <span className='text-xs font-medium text-muted0'>OpenAI-compatible model</span>
                  <input
                    name='openai_model'
                    defaultValue={settings.openai_model}
                    className='mt-1.5 w-full rounded-lg border border-seam bg-surface px-3 py-2 font-mono text-xs text-ink placeholder:text-muted2 shadow-card focus:border-coal focus:outline-none transition-colors'
                  />
                </label>
                <p className='text-[11.5px] text-muted1'>The API key is never stored here — set <span className='font-mono text-ink'>CMPDI_OPENAI_API_KEY</span> in the environment{llmStatus.auth_configured === true ? ' (currently set)' : llmStatus.auth_configured === false ? ' (currently missing)' : ''}.</p>
              </div>
              <div className='mt-4 flex items-center gap-2.5 rounded-lg border border-seam bg-paper px-3.5 py-2.5 text-xs text-muted0'>
                <span className={`h-2 w-2 rounded-full ${llmStatus.available ? 'bg-emerald-500 ring-2 ring-emerald-500/20' : 'bg-coal'}`} />
                <span>
                  <strong className='font-medium text-ink'>{llmStatus.backend || llmStatus.configured}</strong>
                  {llmStatus.model && <> · <span className='font-mono text-ink'>{llmStatus.model}</span></>}: {llmStatus.detail}
                </span>
              </div>
            </InnerSection>
          </Rise>

          <Rise delay={0.08}>
            <InnerSection title='Retrieval'>
              <label className='block'>
                <span className='text-xs font-medium text-muted0'>Chunks retrieved per query (k)</span>
                <div className='mt-1.5 flex items-center gap-3'>
                  <input
                    name='retrieval_k'
                    type='number'
                    min='1'
                    max='50'
                    defaultValue={settings.retrieval_k}
                    className='w-24 rounded-lg border border-seam bg-surface px-3 py-2 font-mono tabular-nums text-xs text-ink shadow-card focus:border-coal focus:outline-none transition-colors'
                  />
                  <span className='text-xs text-muted1'>Higher k widens evidence recall, lower k sharpens answers</span>
                </div>
              </label>
            </InnerSection>
          </Rise>

          <div>
            <Button
              type='submit'
              disabled={busy}
              loading={busy}
              variant='primary'
              size='md'
            >
              Save Settings
            </Button>
          </div>
        </form>

        <Reveal>
          <div className='space-y-5'>
            <Card className='p-5'>
              <h2 className='text-sm font-semibold text-ink'>Embeddings</h2>
              <p className='mt-2 font-mono text-xs text-ink'>{data.emb_name}</p>
              <p className='mt-1 text-xs text-muted1'>{data.emb_dim} dimensions · loaded once, kept resident</p>
            </Card>
            <Card className='p-5'>
              <h2 className='text-sm font-semibold text-ink'>Document Summaries</h2>
              <p className='mt-2 text-xs leading-relaxed text-muted0'>
                <span className='font-mono tabular-nums font-medium text-ink'>{data.summaries_done}</span> of <span className='font-mono tabular-nums font-medium text-ink'>{data.summaries_total}</span> documents summarized. Summaries join the search index so descriptive queries find the right files.
              </p>
              <Button
                onClick={backfill}
                disabled={busy || data.summaries_done >= data.summaries_total}
                loading={busy}
                variant='secondary'
                size='sm'
                className='mt-4'
              >
                Generate Missing Summaries
              </Button>
            </Card>
            <Card className='p-5'>
              <h2 className='text-sm font-semibold text-ink'>Theme</h2>
              <p className='mt-2 text-xs leading-relaxed text-muted0'>
                Switch with the <span className='font-medium text-ink'>Theme</span> button in the sidebar. Your choice is remembered on this machine.
              </p>
            </Card>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
