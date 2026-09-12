import { useState } from "react";
import { Link } from "react-router-dom";
import { Search as SearchIcon, Filter, X, Calendar, FileQuestion } from "lucide-react";
import { usePageData } from "../hooks/useData.js";
import { Rise, PageHeader, Loading, ErrorBox } from "../components/ui.jsx";

const SUGGESTIONS = ["lignite reserves", "coking coal washeries", "coal offtake 2022-23", "geological exploration"];

export default function Search() {
  const params = Object.fromEntries(new URLSearchParams(window.location.search));
  const [input, setInput] = useState(params.q || "");
  const query = new URLSearchParams(Object.entries({
    q: params.q || "", tag: params.tag || "", subsidiary: params.subsidiary || "",
    type: params.type || "", from: params.from || "", to: params.to || "",
  }).filter(([, v]) => v)).toString();
  const { data, error } = usePageData(`/api/pages/search${query ? `?${query}` : ""}`);
  const activeFilters = params.type || params.subsidiary || params.tag || params.from || params.to;
  const results = data?.results || [];
  const filters = data?.filters || params;

  const submit = (e) => {
    e.preventDefault();
    const next = new URLSearchParams(window.location.search);
    if (input) next.set("q", input); else next.delete("q");
    window.location.search = next.toString();
  };
  const select = (key) => (e) => {
    const next = new URLSearchParams(window.location.search);
    if (e.target.value) next.set(key, e.target.value); else next.delete(key);
    window.location.search = next.toString();
  };

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const selectCls = "rounded-lg border border-seam bg-paper px-2.5 py-2 text-[13px] focus:border-coal focus:outline-none";

  return (
    <div>
      <PageHeader
        title="Search"
        subtitle="Lexical BM25 and semantic vectors, fused. Narrow by type, subsidiary, tag or reporting period; every result links back to the exact page or cell it came from."
      />

      <Rise delay={0.05}>
        <form onSubmit={submit} className="mt-6">
          <div className="flex flex-wrap items-center gap-2">
            <label className="relative w-full min-w-0 flex-1 sm:max-w-md">
              <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
              <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Search mines, seams, reserves, numbers…"
                     className="w-full rounded-lg border border-seamdark bg-white py-2.5 pl-10 pr-4 text-sm shadow-card placeholder:text-stone-400 focus:border-coal focus:outline-none" />
            </label>
            <button type="submit"
                    className="flex items-center gap-2 rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:-translate-y-px hover:bg-amber-500 hover:shadow-lift active:translate-y-0">
              <SearchIcon className="h-4 w-4" /> Search
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-seam bg-white p-3 shadow-card">
            <span className="mr-1 flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-wide text-stone-400">
              <Filter className="h-3.5 w-3.5" /> filters
            </span>
            <select value={filters.type} onChange={select("type")} className={selectCls}>
              <option value="">Any type</option>
              {data.doc_types.map((t) => <option key={t.doc_type} value={t.doc_type}>{t.doc_type}</option>)}
            </select>
            <select value={filters.subsidiary} onChange={select("subsidiary")} className={selectCls}>
              <option value="">Any subsidiary</option>
              {data.subs.map((s) => <option key={s.subsidiary} value={s.subsidiary}>{s.subsidiary}</option>)}
            </select>
            <select value={filters.tag} onChange={select("tag")} className={`${selectCls} max-w-[180px]`}>
              <option value="">Any tag</option>
              {data.tags.map((t) => <option key={t.keyword} value={t.keyword}>{t.keyword} ({t.count})</option>)}
            </select>
            <span className="flex items-center gap-1.5 rounded-lg border border-seam bg-paper px-2.5 py-1.5 text-[13px]" title="Reporting period, e.g. 2022-23 or 2022">
              <Calendar className="h-3.5 w-3.5 text-stone-400" />
              <input defaultValue={filters.from} name="from" placeholder="from" size="7" onBlur={select("from")}
                     className="w-16 bg-transparent font-mono text-[12.5px] placeholder:text-stone-400 focus:outline-none" />
              <span className="text-stone-300">–</span>
              <input defaultValue={filters.to} name="to" placeholder="to" size="7" onBlur={select("to")}
                     className="w-16 bg-transparent font-mono text-[12.5px] placeholder:text-stone-400 focus:outline-none" />
            </span>
            {activeFilters && (
              <Link to="/search" className="ml-auto flex items-center gap-1 text-[12px] font-medium text-stone-500 transition-colors hover:text-red-700">
                <X className="h-3.5 w-3.5" /> clear
              </Link>
            )}
          </div>
        </form>
      </Rise>

      {!results.length && !params.q && (
        <Rise delay={0.08}>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="self-center font-mono text-[10px] uppercase tracking-wide text-stone-400">try</span>
            {SUGGESTIONS.map((s) => (
              <Link key={s} to={`/search?q=${encodeURIComponent(s)}`}
                    className="rounded-full border border-seam bg-white px-3.5 py-1.5 text-[13px] text-stone-600 transition-all hover:-translate-y-px hover:border-coal hover:text-coal">{s}</Link>
            ))}
          </div>
        </Rise>
      )}

      {params.q && (
        <p className="mt-5 font-mono text-[11.5px] uppercase tracking-wide text-stone-400">
          {results.length} result{results.length !== 1 ? "s" : ""} for "{params.q}"
        </p>
      )}

      <div className="mt-3 space-y-3">
        {results.map((ev, i) => (
          <article key={i}
                   className={`border-l-[3px] ${i === 0 ? "border-coal" : "border-coalline"} bg-white py-4 pl-5 pr-6 shadow-card transition-all duration-300 hover:-translate-y-px hover:shadow-lift`}>
            <div className="flex flex-wrap items-baseline justify-between gap-2 font-mono text-[12px]">
              <Link to={`/doc/${ev.doc_id}${ev.page_no ? `?page=${ev.page_no}` : ev.sheet_no != null ? `?sheet=${ev.sheet_no}` : ""}`}
                    className="font-semibold text-coal hover:underline">{ev.doc_title}</Link>
              <span className="flex items-center gap-2">
                {ev.score != null && (
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] uppercase ${ev.score >= 0.5 ? "border-coal bg-coal text-white" : "border-seam bg-paper text-stone-500"}`}>
                    {Math.round(ev.score * 100)}% match
                  </span>
                )}
                <span className="text-stone-400">
                  {ev.page_no ? `page ${ev.page_no}` : `sheet ${ev.sheet_no}`}
                  {" · "}{String(ev.content_type).toLowerCase()}
                  {ev.subsidiary ? ` · ${ev.subsidiary}` : ""}
                </span>
              </span>
            </div>
            <p className="mt-2 text-[14px] leading-relaxed text-stone-700">{(ev.text || "").slice(0, 600)}{(ev.text || "").length > 600 ? "…" : ""}</p>
            {ev.tags?.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {ev.tags.map((t) => (
                  <Link key={t} to={`/search?tag=${encodeURIComponent(t)}`}
                        className="rounded-full border border-coalline bg-coalsoft px-2 py-0.5 text-[11px] text-coal transition-colors hover:bg-amber-100">{t}</Link>
                ))}
              </div>
            )}
          </article>
        ))}
        {params.q && !results.length && (
          <div className="mt-4 flex flex-col items-center rounded-2xl border border-dashed border-seamdark bg-white px-6 py-14 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-coalsoft text-coal"><FileQuestion className="h-6 w-6" /></span>
            <p className="mt-3 text-sm font-semibold">Nothing in the library matches "{params.q}"</p>
            <p className="mt-1 text-[13px] text-stone-500">Try fewer words, or relax the filters above.</p>
          </div>
        )}
      </div>
    </div>
  );
}
