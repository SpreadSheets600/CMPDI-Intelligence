import { Link } from "react-router-dom";
import {
  MessageCircle, FileChartColumn, TriangleAlert, Files, FileCheck,
  Check, TriangleAlert as Alert, LoaderCircle,
} from "lucide-react";
import { usePageData } from "../hooks/useData.js";
import { Rise, PageHeader, Loading, ErrorBox } from "../components/ui.jsx";

const QUICK = [
  ["/ask", MessageCircle, "Ask a Question", "Cited answers, analysis and charts"],
  ["/reports", FileChartColumn, "Generate a Report", "Comprehensive DOCX with receipts"],
  ["/conflicts", TriangleAlert, "Investigate Conflicts", "Disagreeing values, explained"],
  ["/documents", Files, "Explore Documents", "Filter, preview, compare and ask"],
];

const pct = (v) => (v === null || v === undefined ? null : `${v}%`);

export default function Dashboard() {
  const { data, error } = usePageData("/api/pages/dashboard");
  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { stats, llm_status, kpi } = data;

  const headline = [
    ["/documents", stats.documents, "documents indexed", ""],
    ["/insights", stats.facts, "facts with receipts", ""],
    ["/conflicts", stats.processing !== undefined ? data.open_conflicts : data.open_conflicts, "conflicts to investigate", data.open_conflicts ? "text-red-700" : ""],
    ["/insights#quality", data.extraction_accuracy !== null && data.extraction_accuracy !== undefined ? `${data.extraction_accuracy}%` : "run eval", "extraction accuracy", data.extraction_accuracy >= 95 ? "text-emerald-700" : ""],
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="The state of your workspace at a glance: what the library holds, how reliable the extraction is, and what needs an officer's eye."
      />

      <Rise delay={0.05}>
        <div className="mt-6 grid grid-cols-2 divide-x divide-seam rounded-xl border border-seam bg-white shadow-card md:grid-cols-4">
          {headline.map(([href, value, label, extra]) => (
            <Link key={label} to={href} className="px-6 py-5 transition-colors hover:bg-paper">
              <div className={`font-mono text-[26px] font-semibold tracking-tight ${extra}`}>{value}</div>
              <div className="mt-0.5 text-[13px] text-stone-500">{label}</div>
            </Link>
          ))}
        </div>
      </Rise>

      <Rise delay={0.1}>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {QUICK.map(([href, Icon, title, desc]) => (
            <Link key={title} to={href}
                  className="group rounded-xl border border-seam bg-white p-4 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:border-coal hover:shadow-lift">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-coalsoft text-coal transition-colors group-hover:bg-coal group-hover:text-white">
                <Icon className="h-[18px] w-[18px]" />
              </span>
              <p className="mt-2.5 text-[14px] font-semibold group-hover:text-coal">{title}</p>
              <p className="mt-1 text-[12.5px] leading-snug text-stone-500">{desc}</p>
            </Link>
          ))}
        </div>
      </Rise>

      <Rise delay={0.15}>
        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
          <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
              <h2 className="text-[15px] font-semibold">Embeddings</h2>
            </div>
            <p className="mt-2 break-all font-mono text-[13px]">{data.emb_name}</p>
            <p className="mt-1 text-[13px] text-stone-500">{data.emb_dim}-dim · {data.vectors} vectors</p>
          </div>
          <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${llm_status.available ? "bg-emerald-600" : "bg-coal"}`}></span>
              <h2 className="text-[15px] font-semibold">Language Model</h2>
            </div>
            <p className="mt-2 break-all font-mono text-[13px]">{llm_status.model || "evidence-only mode"}</p>
            <p className="mt-1 text-[13px] text-stone-500">{llm_status.detail}</p>
          </div>
          <div className="rounded-xl border border-seam bg-white p-5 shadow-card">
            <div className="flex items-center justify-between">
              <h2 className="text-[15px] font-semibold">MVP Performance</h2>
              <span className="font-mono text-[10px] uppercase tracking-widest text-stone-400">measured</span>
            </div>
            <div className="mt-2.5 space-y-1.5 text-[13px]">
              <div className="flex justify-between"><span className="text-stone-500">Extraction accuracy</span><span className="font-mono font-semibold">{pct(kpi.extraction_accuracy) || "run eval"}</span></div>
              <div className="flex justify-between"><span className="text-stone-500">Report prep, AI-assisted</span><span className="font-mono font-semibold">{kpi.report?.ai_minutes ? `${kpi.report.ai_minutes} min` : "generate one"}</span></div>
              <div className="flex justify-between"><span className="text-stone-500">Time saved vs manual*</span><span className="font-mono font-semibold text-emerald-700">{kpi.report?.time_saved_pct ? `${kpi.report.time_saved_pct}%` : "-"}</span></div>
              <div className="flex justify-between"><span className="text-stone-500">Workflow automated</span><span className="font-mono font-semibold">{kpi.automation?.steps}/{kpi.automation?.of}</span></div>
            </div>
            <p className="mt-2 text-[10.5px] text-stone-400">*manual baseline is a stated planning figure (2h18m), the AI time is measured.</p>
          </div>
        </div>
      </Rise>

      <Rise delay={0.2}>
        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-5">
          <div className="rounded-xl border border-seam bg-white shadow-card lg:col-span-3">
            <div className="flex items-center justify-between border-b border-seam px-5 py-3.5">
              <h2 className="text-[15px] font-semibold">Recent Documents</h2>
              <Link to="/documents" className="text-[13px] font-medium text-coal hover:underline">View all</Link>
            </div>
            {data.recent_docs.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-stone-500">Nothing indexed yet — start by ingesting files.</p>
            ) : data.recent_docs.map((d) => (
              <Link key={d.id} to={`/doc/${d.id}`}
                    className="flex items-center gap-3 border-b border-seam px-5 py-3 transition-colors last:border-0 hover:bg-paper">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-coalsoft text-coal"><FileCheck className="h-4 w-4" /></span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[14px] font-medium">{d.display_name || d.filename}</p>
                  <p className="mt-0.5 font-mono text-[11px] uppercase tracking-wide text-stone-400">
                    {d.doc_type}{d.subsidiary ? ` · ${d.subsidiary}` : ""}{!d.has_summary ? " · summary pending" : ""}
                  </p>
                </div>
                {d.content_norm && <span className="hidden rounded-full border border-coalline bg-coalsoft px-2.5 py-0.5 font-mono text-[10.5px] text-coal sm:block">{d.content_norm}</span>}
              </Link>
            ))}
          </div>

          <div className="rounded-xl border border-seam bg-white shadow-card lg:col-span-2">
            <div className="flex items-center justify-between border-b border-seam px-5 py-3.5">
              <h2 className="text-[15px] font-semibold">Pipeline Activity</h2>
              <Link to="/pipeline" className="text-[13px] font-medium text-coal hover:underline">Pipeline</Link>
            </div>
            <div>
              {data.jobs.length === 0 ? (
                <p className="px-5 py-8 text-center text-sm text-stone-500">No jobs yet.</p>
              ) : data.jobs.map((j, i) => (
                <div key={i} className="flex items-center gap-3 border-b border-seam px-5 py-2.5 last:border-0">
                  <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${j.status === "completed" ? "bg-emerald-50 text-emerald-700" : j.status === "failed" ? "bg-red-50 text-red-700" : "bg-coalsoft text-coal"}`}>
                    {j.status === "failed" ? <Alert className="h-3.5 w-3.5" /> : j.status === "completed" ? <Check className="h-3.5 w-3.5" /> : <LoaderCircle className="h-3.5 w-3.5 animate-spin" />}
                  </span>
                  <p className="min-w-0 flex-1 truncate text-[13px]">{(j.filename || "unknown file").slice(0, 40)}</p>
                  <span className={`font-mono text-[11px] uppercase ${j.status === "completed" ? "text-emerald-700" : j.status === "failed" ? "text-red-700" : "text-coal"}`}>{j.stage}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between border-t border-seam px-5 py-2.5 text-[12.5px] text-stone-500">
              <span>library storage {data.storage_gb.toFixed(2)} GB</span>
              {stats.failed
                ? <Link to="/pipeline" className="text-red-700 hover:underline">{stats.failed} failed job(s)</Link>
                : <span className="text-emerald-700">no failures</span>}
            </div>
          </div>
        </div>
      </Rise>
    </div>
  );
}
