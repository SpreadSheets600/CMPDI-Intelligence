import { useState } from "react";
import { usePageData } from "../hooks/useData.js";
import { postJSON } from "../api.js";
import { Rise, PageHeader, Loading, ErrorBox } from "../components/ui.jsx";

export default function Settings() {
  const { data, error, reload } = usePageData("/api/pages/settings");
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
      const res = await postJSON("/api/settings", Object.fromEntries(f));
      setNotice(res.error ? { bad: true, msg: res.error } : { bad: false, msg: res.message });
      reload();
    } catch (err) { setNotice({ bad: true, msg: err.message }); }
    setBusy(false);
  };

  const backfill = async () => {
    setBusy(true);
    try {
      const res = await postJSON("/api/settings/summaries");
      setNotice({ bad: false, msg: `Generated ${res.generated} document summary(ies).` });
      reload();
    } catch (err) { setNotice({ bad: true, msg: err.message }); }
    setBusy(false);
  };

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Only controls with a real effect live here. Changes apply immediately; environment variables remain the defaults underneath."
      />

      {notice && (
        <div className={`mt-4 rounded-xl border px-4 py-3 text-[13.5px] ${notice.bad ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"}`}>
          {notice.msg}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <form onSubmit={save} className="space-y-5 lg:col-span-2">
          <Rise delay={0.04}>
            <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
              <h2 className="text-[15px] font-semibold">Language Model</h2>
              <div className="mt-4 space-y-4">
                <label className="block">
                  <span className="text-[13px] font-medium text-stone-600">Backend</span>
                  <select name="llm_backend" defaultValue={settings.llm_backend}
                          className="mt-1 w-full rounded-lg border border-seamdark bg-paper px-3 py-2 text-sm focus:border-coal focus:outline-none">
                    <option value="auto">Auto: probe Ollama, then transformers, then evidence-only</option>
                    <option value="ollama">Ollama: local or cloud models served by Ollama</option>
                    <option value="transformers">Transformers: locally cached HuggingFace model</option>
                    <option value="none">None (evidence-only): no generation; verbatim cited evidence only</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-[13px] font-medium text-stone-600">Ollama model</span>
                  <input name="ollama_model" defaultValue={settings.ollama_model}
                         className="mt-1 w-full rounded-lg border border-seamdark bg-paper px-3 py-2 font-mono text-sm focus:border-coal focus:outline-none" />
                </label>
                <label className="block">
                  <span className="text-[13px] font-medium text-stone-600">Ollama URL</span>
                  <input name="ollama_url" defaultValue={settings.ollama_url}
                         className="mt-1 w-full rounded-lg border border-seamdark bg-paper px-3 py-2 font-mono text-sm focus:border-coal focus:outline-none" />
                </label>
              </div>
              <div className="mt-4 flex items-center gap-2 rounded-lg border border-seam bg-paper px-3 py-2.5 text-[13px]">
                <span className={`h-2 w-2 rounded-full ${llmStatus.available ? "bg-emerald-600" : "bg-coal"}`}></span>
                <span className="text-stone-600">
                  {llmStatus.backend || llmStatus.configured}
                  {llmStatus.model && <> · <span className="font-mono">{llmStatus.model}</span></>}: {llmStatus.detail}
                </span>
              </div>
            </div>
          </Rise>

          <Rise delay={0.08}>
            <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
              <h2 className="text-[15px] font-semibold">Retrieval</h2>
              <label className="mt-4 block">
                <span className="text-[13px] font-medium text-stone-600">Chunks retrieved per query (k)</span>
                <input name="retrieval_k" type="number" min="1" max="50" defaultValue={settings.retrieval_k}
                       className="mt-1 w-32 rounded-lg border border-seamdark bg-paper px-3 py-2 font-mono text-sm focus:border-coal focus:outline-none" />
                <span className="ml-2 text-[12.5px] text-stone-400">higher k widens evidence recall, lower k sharpens answers</span>
              </label>
            </div>
          </Rise>

          <button disabled={busy}
                  className="rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:bg-amber-500 active:translate-y-px disabled:opacity-50">
            Save Settings
          </button>
        </form>

        <Rise delay={0.12}>
          <div className="space-y-5">
            <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
              <h2 className="text-[15px] font-semibold">Embeddings</h2>
              <p className="mt-2 font-mono text-[13px]">{data.emb_name}</p>
              <p className="mt-1 text-[13px] text-stone-500">{data.emb_dim} dimensions · loaded once, kept resident</p>
            </div>
            <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
              <h2 className="text-[15px] font-semibold">Document Summaries</h2>
              <p className="mt-2 text-[13px] text-stone-500">{data.summaries_done} of {data.summaries_total} documents summarized. Summaries join the search index so descriptive queries find the right files.</p>
              <button onClick={backfill} disabled={busy || data.summaries_done >= data.summaries_total}
                      className={`mt-3 rounded-lg border border-seam px-3 py-1.5 text-[12.5px] font-medium ${data.summaries_done >= data.summaries_total ? "border-seam text-stone-300" : "text-stone-500 hover:border-coal hover:text-coal"}`}>
                Generate Missing Summaries
              </button>
            </div>
            <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
              <h2 className="text-[15px] font-semibold">Theme</h2>
              <p className="mt-2 text-[13px] text-stone-500">Switch with the <span className="font-medium text-ink">Theme</span> button in the sidebar. Your choice is remembered on this machine.</p>
            </div>
          </div>
        </Rise>
      </div>
    </div>
  );
}
