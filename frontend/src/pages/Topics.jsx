import { useState } from "react";
import { RefreshCw, Shapes, Eye, Files } from "lucide-react";
import { usePageData } from "../hooks/useData.js";
import { postJSON } from "../api.js";
import { Rise, PageHeader, Loading, ErrorBox } from "../components/ui.jsx";

export default function Topics() {
  const scope = new URLSearchParams(window.location.search).get("scope") || "corpus";
  const { data, error, reload } = usePageData(`/api/pages/topics?scope=${encodeURIComponent(scope)}`);
  const [busy, setBusy] = useState(false);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;

  const analyze = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await postJSON("/api/topics/refresh", { scope: e.currentTarget.scope.value });
      reload();
    } catch { /* ignore */ }
    setBusy(false);
  };

  return (
    <div>
      <PageHeader
        title="Topics"
        subtitle="Recurring keywords, themes and document clusters across the library. Analysis runs locally on the embeddings.">
        <form onSubmit={analyze} className="flex flex-wrap items-center gap-2">
          <select name="scope" defaultValue={scope !== "corpus" ? scope : ""}
                  className="rounded-lg border border-seamdark bg-white px-3 py-2.5 text-sm shadow-card focus:border-coal focus:outline-none">
            <option value="">Corpus-wide</option>
            {data.subs.map((s) => <option key={s.subsidiary} value={`subsidiary:${s.subsidiary}`}>{s.subsidiary}</option>)}
          </select>
          <button type="submit" disabled={busy}
                  className="flex items-center gap-2 rounded-lg bg-coal px-4 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:-translate-y-px hover:bg-amber-500 hover:shadow-lift active:translate-y-0 disabled:opacity-50">
            <RefreshCw className="h-4 w-4" /> Analyze
          </button>
        </form>
      </PageHeader>

      <Rise delay={0.05}>
        <div className="mt-8 rounded-2xl border border-seam bg-white p-5 text-center shadow-card">
          <div className="mb-3 flex items-center justify-center gap-2 font-mono text-[10.5px] uppercase tracking-widest text-stone-400">
            <Eye className="h-3.5 w-3.5" /> word cloud · {scope}
          </div>
          <img src={`/api/topics/cloud?scope=${encodeURIComponent(scope)}`} alt={`Word cloud for ${scope}`}
               className="mx-auto max-w-full rounded-lg" />
        </div>
      </Rise>

      <h2 className="mt-10 flex items-center gap-2 text-lg font-semibold tracking-tight">
        <Shapes className="h-5 w-5 text-coal" /> Clusters
      </h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {data.clusters.length === 0 ? (
          <div className="flex flex-col items-center rounded-2xl border border-dashed border-seamdark bg-white px-6 py-14 text-center md:col-span-2">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-coalsoft text-coal"><Shapes className="h-6 w-6" /></span>
            <p className="mt-3 text-sm font-semibold">No cluster analysis yet</p>
            <p className="mt-1 text-[13px] text-stone-500">Pick a scope above and click Analyze; clustering runs on the local embeddings.</p>
          </div>
        ) : data.clusters.map((t) => (
          <section key={t.id} className="rounded-xl border border-seam bg-white p-5 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lift">
            <h3 className="text-[15px] font-semibold">{t.label}</h3>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {t.keywords.map((k) => (
                <span key={k} className="rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 text-[12px] text-coal">{k}</span>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between">
              <p className="flex items-center gap-1.5 text-[13px] text-stone-500">
                <Files className="h-3.5 w-3.5 text-stone-400" /> {t.doc_ids.length} document{t.doc_ids.length !== 1 ? "s" : ""}
              </p>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
