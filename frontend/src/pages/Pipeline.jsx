import { useRef, useState } from "react";
import { Upload, Workflow, Package, Info, File as FileIcon, TriangleAlert as Alert, LoaderCircle } from "lucide-react";
import { usePageData, usePolling } from "../hooks/useData.js";
import { uploadFiles } from "../api.js";
import { Rise, PageHeader, Loading, ErrorBox } from "../components/ui.jsx";

const STAGES = ["uploaded", "classifying", "extracting", "ocr", "normalizing",
  "chunking", "embedding", "indexing", "summarizing", "completed"];

function JobStrip() {
  const jobs = usePolling("/api/jobs", 2500);
  if (!jobs) return <div className="mt-4 space-y-3" aria-live="polite" />;
  return (
    <div className="mt-4 space-y-3" aria-live="polite">
      {jobs.map((j, i) => {
        const failed = j.status === "failed";
        const running = j.status === "running";
        const idx = STAGES.indexOf(j.stage);
        return (
          <div key={j.id || i}
               className={`rounded-xl border p-4 shadow-card ${failed ? "border-red-200 bg-red-50/60" : "border-seam bg-white"}`}>
            <div className="flex items-baseline justify-between gap-4 overflow-hidden">
              <span className="min-w-0 truncate text-sm font-semibold">{j.filename || "unknown file"}</span>
              <span className={`flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide ${failed ? "text-red-700" : j.status === "completed" ? "text-emerald-700" : "text-coal"}`}>
                {failed ? <Alert className="h-3.5 w-3.5" /> : running
                  ? <LoaderCircle2 /> : <CircleCheck />}
                {failed ? "failed" : j.stage}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-1 text-[10px] font-mono uppercase tracking-wide">
              {STAGES.map((s, si) => {
                const mine = STAGES.indexOf(s);
                const cls = failed && s === j.stage
                  ? "bg-red-600 text-white border-red-600"
                  : s === j.stage ? "bg-coal text-white border-coal"
                  : mine < idx ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-seam text-stone-400";
                return (
                  <span key={s} className="flex items-center gap-1">
                    {si > 0 && <span className="text-stone-300">›</span>}
                    <span className={`rounded border px-1.5 py-0.5 ${cls}`}>{s}</span>
                  </span>
                );
              })}
            </div>
            {j.error && <div className="mt-2 font-mono text-xs text-red-700">{j.error.split("\n")[0]}</div>}
          </div>
        );
      })}
    </div>
  );
}

function LoaderCircle2() {
  return <LoaderCircle className="h-3.5 w-3.5 animate-spin" />;
}
function CircleCheck() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
      <circle cx="12" cy="12" r="10" /><path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export default function Pipeline() {
  const { data, error, reload } = usePageData("/api/pages/pipeline");
  const [files, setFiles] = useState([]);
  const [hot, setHot] = useState(false);
  const [busy, setBusy] = useState(false);
  const [ingested, setIngested] = useState(null);
  const inputRef = useRef(null);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const { stats } = data;

  const submit = async (e) => {
    e.preventDefault();
    if (!inputRef.current?.files.length) return;
    setBusy(true);
    try {
      const res = await uploadFiles(inputRef.current.files);
      setIngested(res.results);
      reload();
    } catch (err) {
      setIngested([{ filename: "upload", error: err.message }]);
    }
    setBusy(false);
  };

  const loadDemo = async () => {
    setBusy(true);
    try {
      await fetch("/api/pipeline/demo", { method: "POST" });
      reload();
    } catch { /* ignore */ }
    setBusy(false);
  };

  const chips = ["PDF", "Scanned PDF", "DOCX", "XLSX", "CSV", "Images"];
  const statCards = [
    ["files", "Documents", stats.documents],
    ["braces", "Chunks Indexed", stats.chunks],
    ["hash", "Facts With Receipts", stats.facts],
    ["tags", "Extracted Tags", stats.tags],
  ];

  return (
    <div>
      <PageHeader
        title="Pipeline"
        subtitle="Drop in digital or scanned PDFs, DOCX, XLSX, CSV and images. Everything is parsed, chunked, embedded, summarized and indexed on this machine."
      />

      {ingested && (
        <Rise className="mt-6">
          <h2 className="text-lg font-semibold">Queued For Ingestion</h2>
          <div className="mt-3 space-y-3">
            {ingested.map((r, i) => (
              <div key={i} className="flex items-center justify-between rounded-xl border border-seam bg-white px-5 py-4 shadow-card">
                <span className="text-sm font-semibold">{r.filename}</span>
                {r.error
                  ? <span className="rounded-full border border-red-200 bg-red-50 px-3 py-1 font-mono text-[11px] text-red-700">rejected: {r.error}</span>
                  : r.duplicate
                    ? <span className="rounded-full border border-seam bg-paper px-3 py-1 font-mono text-[11px] text-stone-500">duplicate of existing document</span>
                    : <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-mono text-[11px] text-emerald-700">queued</span>}
              </div>
            ))}
          </div>
        </Rise>
      )}

      <Rise delay={0.05} className="mt-6">
        <form onSubmit={submit}>
          <div
            className={`dropzone relative rounded-2xl border-2 border-dashed border-seamdark bg-white px-6 py-14 text-center shadow-card hover:border-coal ${hot ? "dropzone-hot" : ""}`}
            onDragEnter={(e) => { e.preventDefault(); setHot(true); }}
            onDragOver={(e) => { e.preventDefault(); setHot(true); }}
            onDragLeave={(e) => { e.preventDefault(); setHot(false); }}
            onDrop={(e) => {
              e.preventDefault(); setHot(false);
              if (e.dataTransfer.files.length) {
                inputRef.current.files = e.dataTransfer.files;
                setFiles([...e.dataTransfer.files].map((f) => f.name));
              }
            }}
          >
            <input ref={inputRef} type="file" name="files" multiple
                   onChange={(e) => setFiles([...e.target.files].map((f) => f.name))}
                   className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                   accept=".pdf,.docx,.xlsx,.xls,.csv,.txt,.png,.jpg,.jpeg,.tif,.tiff" title="Choose files to ingest" />
            <div className="pointer-events-none">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-coalsoft text-coal transition-transform duration-300 hover:scale-105">
                <Upload className="h-8 w-8" />
              </div>
              <p className="mt-5 text-[16px] font-semibold">Drag &amp; drop files here</p>
              <p className="mt-1 text-[13.5px] text-stone-500">or click to browse your computer</p>
              <div className="mt-5 flex flex-wrap items-center justify-center gap-1.5">
                {chips.map((t) => (
                  <span key={t} className="rounded-full border border-seam bg-paper px-2.5 py-0.5 font-mono text-[10.5px] uppercase tracking-wide text-stone-400">{t}</span>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {files.map((n) => (
              <span key={n} className="inline-flex items-center gap-1.5 rounded-full border border-coalline bg-coalsoft px-3 py-1 text-[12px] text-coal">
                <FileIcon className="h-3 w-3" />{n}
              </span>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <button type="button" onClick={loadDemo} disabled={busy} title="Generate and ingest a curated demonstration corpus"
                    className="flex items-center gap-1.5 text-[12.5px] font-medium text-stone-500 transition-colors hover:text-coal disabled:opacity-50">
              <Package className="h-3.5 w-3.5 text-stone-400" /> No files handy? Load the demonstration dataset
            </button>
            <p className="flex items-center gap-1.5 text-[13px] text-stone-500">
              <Info className="h-4 w-4 shrink-0 text-stone-400" />
              Duplicates are rejected by SHA-256. Revised reports join version chains automatically.
            </p>
            <button type="submit" disabled={busy}
                    className="flex items-center gap-2 rounded-lg bg-coal px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:-translate-y-px hover:bg-amber-500 hover:shadow-lift active:translate-y-0 disabled:opacity-50">
              <Workflow className="h-4 w-4" /> Ingest Files
            </button>
          </div>
        </form>
      </Rise>

      <Rise delay={0.1}>
        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {statCards.map(([key, label, value]) => (
            <div key={label} className="flex items-center gap-3 rounded-xl border border-seam bg-white px-4 py-3.5 shadow-card">
              <div>
                <div className="font-mono text-[20px] font-semibold leading-none tracking-tight">{value}</div>
                <div className="mt-1 text-[12px] text-stone-500">{label}</div>
              </div>
            </div>
          ))}
        </div>
      </Rise>

      <Rise delay={0.15}>
        <div className="mt-8 flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight">Recent Jobs</h2>
          <span className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-stone-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600"></span> live
          </span>
        </div>
        <JobStrip />
      </Rise>
    </div>
  );
}
