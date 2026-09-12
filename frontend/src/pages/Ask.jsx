import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { RefreshCw, X, FileText, MessageCircle, Send } from "lucide-react";
import { usePageData } from "../hooks/useData.js";
import { getJSON, postJSON } from "../api.js";
import { Rise, Loading, ErrorBox } from "../components/ui.jsx";

const TOOL_LABEL = {
  search_documents: "Searched Documents",
  get_facts: "Queried Fact Index",
  run_python: "Ran Python Analysis",
};

// tiny markdown renderer: headings, lists, bold, code, [E1] citation marks
function mdLite(text) {
  const lines = String(text ?? "").split("\n");
  const inline = (s) =>
    s
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, '<code class="rounded bg-paper px-1 font-mono text-[12.5px]">$1</code>')
      .replace(/\[E(\d+)\]/g, '<sup class="mx-0.5 rounded border border-coalline bg-coalsoft px-1 font-mono text-[10px] font-semibold text-coal">E$1</sup>');
  let html = "", inList = false, buf = [];
  const flush = () => { if (buf.length) { html += `<p class="mt-2">${buf.map(inline).join("<br>")}</p>`; buf = []; } };
  const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };
  for (const line of lines) {
    const t = line.trim();
    if (/^#{1,6}\s/.test(t)) { flush(); closeList(); html += `<h3 class="mt-4 text-[15px] font-semibold">${inline(t.replace(/^#+\s/, ""))}</h3>`; }
    else if (/^[-*]\s/.test(t)) { buf.length && flush(); if (!inList) { html += '<ul class="mt-2 list-disc space-y-1 pl-5">'; inList = true; } html += `<li>${inline(t.replace(/^[-*]\s/, ""))}</li>`; }
    else if (t === "") { closeList(); flush(); }
    else { closeList(); buf.push(t); }
  }
  closeList(); flush();
  return { __html: html };
}

function EvidenceCard({ c, i }) {
  const loc = c.page_no ? `page ${c.page_no}` : c.sheet_no ? `sheet ${c.sheet_no}` : "document";
  const isFact = c.content_type && c.content_type !== "EVIDENCE";
  return (
    <div className={`rounded-lg border ${isFact ? "border-emerald-200" : "border-seam"} bg-paper p-3 text-[12.5px]`}>
      <div className="flex items-center justify-between gap-2">
        <span className={`flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest ${isFact ? "text-emerald-700" : "text-stone-400"}`}>
          {isFact ? "✓ verified evidence" : "supporting evidence"}
          <sup className="rounded border border-coalline bg-coalsoft px-1 font-semibold text-coal">E{i + 1}</sup>
        </span>
        <Link className="flex items-center gap-1 rounded-md border border-coal px-2 py-0.5 text-[11px] font-semibold text-coal transition-colors hover:bg-coal hover:text-white"
              to={`/doc/${c.doc_id}${c.page_no ? `/?page=${c.page_no}` : c.sheet_no ? `?sheet=${c.sheet_no}` : ""}`}>
          View Source →
        </Link>
      </div>
      <div className="mt-2 grid grid-cols-[64px_1fr] gap-x-2 gap-y-0.5">
        <span className="text-stone-400">Source</span><span className="truncate font-medium text-ink" title={c.doc_title}>{c.doc_title}</span>
        <span className="text-stone-400">Location</span><span className="font-mono">{loc}{c.content_type && c.content_type !== "EVIDENCE" ? ` · ${String(c.content_type).toLowerCase()}` : ""}</span>
        {c.doc_type && <><span className="text-stone-400">Type</span><span className="font-mono uppercase">{c.doc_type}</span></>}
        {c.conf && <><span className="text-stone-400">Confidence</span><span className="font-mono">{c.conf}%</span></>}
      </div>
      {c.text && !isFact && <p className="mt-2 line-clamp-2 text-stone-500">{String(c.text).slice(0, 200)}</p>}
    </div>
  );
}

function QualityBadge({ q }) {
  if (!q) return null;
  const color = q.level === "HIGH" ? "border-emerald-200 bg-emerald-50 text-emerald-700"
    : q.level === "LOW" ? "border-red-200 bg-red-50 text-red-700"
    : "border-coalline bg-coalsoft text-coal";
  const mark = (s) => (s === "ok" ? <span className="text-emerald-600">✓</span> : s === "warn" ? <span className="text-coal">⚠</span> : <span className="text-red-600">✗</span>);
  return (
    <div className={`mb-3 flex flex-wrap items-center gap-2 rounded-lg border ${color} px-3 py-2`}>
      <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest">Evidence Quality: {q.level}</span>
      {q.conflicts > 0 && (
        <Link to="/conflicts" className={`rounded-full border ${color} px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide`} title="Investigate on the Conflict Radar">
          {q.conflicts} conflict{q.conflicts !== 1 ? "s" : ""} →
        </Link>
      )}
      <details className="min-w-0 flex-1">
        <summary className="cursor-pointer select-none list-none text-right font-mono text-[10.5px] uppercase tracking-wide opacity-70">details</summary>
        <div className="mt-2 space-y-1 text-left text-[12px] normal-case">
          {(q.checks || []).map((c, i) => <div key={i} className="flex items-center gap-1.5">{mark(c[0])}<span>{c[1]}</span></div>)}
        </div>
      </details>
    </div>
  );
}

function WhyPanel({ w }) {
  if (!w) return null;
  const row = (k, v) => <div className="flex justify-between gap-3"><dt className="text-stone-400">{k}</dt><dd className="font-mono text-[11.5px] text-stone-600">{String(v)}</dd></div>;
  return (
    <details className="mt-3 rounded-lg border border-seam bg-paper px-3 py-2">
      <summary className="cursor-pointer select-none list-none font-mono text-[10.5px] uppercase tracking-widest text-stone-400">Why this answer?</summary>
      <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-[12px]">
        {row("Query type", w.route)}
        {row("Chunks retrieved", w.chunks_retrieved)}
        {row("Documents represented", w.documents_represented)}
        {w.facts_matched !== undefined && row("Facts matched", w.facts_matched)}
        {w.computations !== undefined && row("Computations run", w.computations)}
        {row("Sources cited", w.sources_cited)}
        {row("Conflicts", w.conflicts)}
        {row("LLM", w.llm)}
        {row("Generation", w.generation)}
      </dl>
    </details>
  );
}

function TracePanel({ trace }) {
  if (!trace?.length) return null;
  const n = trace.filter((s) => s.type === "tool").length;
  return (
    <details className="mb-3 rounded-lg border border-seam bg-paper px-3 py-2">
      <summary className="cursor-pointer select-none list-none font-mono text-[10.5px] uppercase tracking-wide text-stone-400">
        How this was answered · {n} step{n === 1 ? "" : "s"}
      </summary>
      <div className="mt-2 space-y-1.5 border-l-2 border-coalline pl-3">
        {trace.map((s, i) => s.type === "thought" ? (
          <p key={i} className="text-[12.5px] leading-relaxed text-stone-500">{s.text}</p>
        ) : s.type === "tool" ? (
          <p key={i} className="font-mono text-[11px] uppercase tracking-wide text-stone-400">{TOOL_LABEL[s.tool] || s.tool}</p>
        ) : null)}
      </div>
    </details>
  );
}

const PHASES = ["Looking through the library…", "Resolving numbers from the fact index…", "Computing and drawing charts…", "Composing the answer…"];

export default function Ask() {
  const [params] = useSearchParams();
  const qs = new URLSearchParams();
  for (const k of ["doc", "docs", "q"]) if (params.get(k)) qs.set(k, params.get(k));
  const { data, error } = usePageData(`/api/pages/ask${qs.toString() ? `?${qs}` : ""}`);

  const [messages, setMessages] = useState([]); // {role, payload?, error?}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const historyRef = useRef([]);
  const logRef = useRef(null);
  const inputRef = useRef(null);
  const scopedDocIds = (data?.scoped_docs || []).map((d) => d.id);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages, busy]);

  const send = async (textArg) => {
    const text = (textArg ?? input).trim();
    if (!text || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    historyRef.current.push({ role: "user", content: text });
    setBusy(true);
    try {
      const payload = await postJSON("/api/chat", {
        messages: historyRef.current,
        doc_ids: scopedDocIds,
      });
      setMessages((m) => [...m, { role: "assistant", payload }]);
      historyRef.current.push({ role: "assistant", content: payload.answer || "" });
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", error: e.message }]);
    }
    setBusy(false);
    inputRef.current?.focus();
  };

  const downloadReport = async (runRowId, btn) => {
    btn.disabled = true;
    try {
      const { download } = await postJSON("/api/agent/report", { run_id: runRowId });
      window.location.href = download;
    } catch (e) {
      window.alert(e.message);
    }
    btn.disabled = false;
  };

  // deep links carrying ?q= kick off the first question automatically
  const seeded = useRef(false);
  useEffect(() => {
    if (!seeded.current && data?.seed_q) {
      seeded.current = true;
      send(data.seed_q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const scoped = data.scoped_docs;
  const pills = scoped.length
    ? ["What was the production reported here?", "What mines are mentioned?", "Summarize the key findings.", "What reserves are reported?", "What changed from the previous report?"]
    : ["raw coal production of CIL in 2023-24", "compare production across subsidiaries", "generate a few charts for this data", "what does the library say about washeries?"];

  const typing = busy && (
    <div className="flex">
      <div className="w-full rounded-2xl rounded-tl-md border border-seam bg-white p-5 shadow-card">
        <div className="flex items-center gap-3 text-[13.5px] text-stone-500">
          <span className="flex gap-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-coal"></span>
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-coal [animation-delay:150ms]"></span>
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-coal [animation-delay:300ms]"></span>
          </span>
          <span>Looking through the library…</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-[calc(100dvh-11rem)] flex-col">
      <Rise className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Ask</h1>
          <p className="mt-1 max-w-[70ch] text-[15px] text-stone-500">One interface over the whole library. It answers with citations, resolves numbers from the fact index, and when a question needs analysis or charts it runs the tools itself: just ask.</p>
        </div>
        <button title="New conversation" onClick={() => { historyRef.current = []; setMessages([]); window.location.href = "/ask"; }}
                className="flex shrink-0 items-center gap-2 rounded-lg border border-seam px-3 py-2 text-[12.5px] font-medium text-stone-500 transition-colors hover:border-coal hover:text-coal">
          <RefreshCw className="h-3.5 w-3.5" /> New chat
        </button>
      </Rise>

      {scoped.length > 0 && (
        <Rise delay={0.04}>
          <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-coalline bg-coalsoft px-4 py-2.5 text-[13px]">
            <span className="font-mono text-[10.5px] uppercase tracking-widest text-coal">scoped to</span>
            {scoped.map((d) => (
              <span key={d.id} className="inline-flex items-center gap-1.5 rounded-full border border-coalline bg-white px-2.5 py-0.5 text-[12px] text-stone-600">
                <FileText className="h-3 w-3 text-coal" /> {d.display_name || d.filename}
              </span>
            ))}
            <Link to="/ask" className="ml-auto flex items-center gap-1 text-[12px] font-medium text-coal hover:underline">
              <X className="h-3.5 w-3.5" /> clear scope
            </Link>
          </div>
        </Rise>
      )}

      <div ref={logRef} className="mt-5 flex-1 space-y-5 overflow-y-auto pr-1" aria-live="polite">
        {messages.length === 0 && !busy && (
          <div className="mx-auto max-w-xl pt-6 text-center">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-coalsoft text-coal"><MessageCircle className="h-7 w-7" /></span>
            <p className="mt-4 font-semibold">Ask anything about your documents</p>
            <p className="mt-1 text-[13.5px] text-stone-500">Factual questions get cited answers; analytical questions get computed results and charts.</p>
            <div className="mt-6 flex flex-wrap justify-center gap-1.5">
              {pills.map((p) => (
                <button key={p} onClick={() => send(p)}
                        className="rounded-full border border-coalline bg-coalsoft px-3 py-1.5 text-[12.5px] text-coal transition-all hover:-translate-y-px hover:bg-amber-100">{p}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => m.role === "user" ? (
          <div key={i} className="flex justify-end">
            <div className="max-w-[80%] rounded-2xl rounded-br-md bg-coal px-4 py-2.5 text-[14.5px] leading-relaxed text-white shadow-card">{m.text}</div>
          </div>
        ) : m.error ? (
          <div key={i} className="flex">
            <div className="w-full rounded-2xl rounded-tl-md border border-seam bg-white p-5 shadow-card">
              <p className="text-[14px] text-red-700">{m.error}</p>
            </div>
          </div>
        ) : (
          <div key={i} className="flex">
            <div className="w-full rounded-2xl rounded-tl-md border border-seam bg-white p-5 shadow-card">
              <TracePanel trace={m.payload.trace} />
              <QualityBadge q={m.payload.quality} />
              <div className="text-[14.5px] leading-relaxed text-stone-700" dangerouslySetInnerHTML={mdLite(m.payload.abstained ? m.payload.answer || "Insufficient evidence." : m.payload.answer || "")} />
              {(m.payload.charts || []).map((src) => (
                <div key={src} className="mt-4">
                  <img src={src} className="max-h-[420px] w-auto rounded-lg border border-seam bg-white shadow-card" alt="Chart generated from library data" />
                </div>
              ))}
              {(m.payload.citations || []).length > 0 && (
                <div className="mt-4 border-t border-seam pt-3">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-stone-400">source coverage</p>
                  <div className="mt-1.5 grid gap-2 sm:grid-cols-2">
                    {m.payload.citations.map((c, ci) => <EvidenceCard key={ci} c={c} i={ci} />)}
                  </div>
                </div>
              )}
              <WhyPanel w={m.payload.why} />
              {m.payload.mode === "agent" && m.payload.run_row_id && (
                <button onClick={(e) => downloadReport(m.payload.run_row_id, e.currentTarget)}
                        className="mt-3 flex items-center gap-2 rounded-lg border border-coal px-3 py-1.5 text-[12.5px] font-semibold text-coal transition-colors hover:bg-coal hover:text-white">
                  Generate DOCX Report
                </button>
              )}
              {(m.payload.alternatives || []).length > 0 && (
                <div className="mt-3 rounded-lg border border-coalline bg-coalsoft px-3 py-2.5 text-[12.5px] text-stone-600">
                  <strong className="text-coal">Also reported elsewhere:</strong>{" "}
                  {m.payload.alternatives.map((a) => (
                    <span key={a.filename}>
                      <span className="font-mono">{String(a.fact_values?.[0]?.value_raw ?? "")}</span> ({a.filename})
                    </span>
                  )).reduce((acc, x) => [acc, ", "], [])}
                </div>
              )}
            </div>
          </div>
        ))}
        {typing}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(); }} className="mt-4 flex items-end gap-2">
        <div className="relative flex-1">
          <textarea ref={inputRef} rows="1" value={input}
                    onChange={(e) => {
                      setInput(e.target.value);
                      e.target.style.height = "auto";
                      e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
                    }}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                    placeholder="Ask about production, reserves, offtake... or request charts and analysis"
                    className="w-full resize-none rounded-xl border border-seamdark bg-white py-3 pl-4 pr-12 text-[14.5px] leading-relaxed shadow-card placeholder:text-stone-400 focus:border-coal focus:outline-none" />
          <button type="submit" title="Send" disabled={busy || !input.trim()}
                  className="absolute bottom-2.5 right-2.5 flex h-8 w-8 items-center justify-center rounded-lg bg-coal text-white transition-all hover:bg-amber-500 active:scale-95 disabled:opacity-40">
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
      <p className="mt-2 text-center text-[11.5px] text-stone-400">Answers cite their sources; figures resolve from the fact index where possible.</p>
    </div>
  );
}
