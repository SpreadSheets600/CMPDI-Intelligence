import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Package, ShieldCheck, HardDrive, CircleCheck, Plus } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1];
const rise = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "0px 0px -12% 0px" },
  transition: { duration: 0.65, ease: EASE, delay },
});

const FAQS = [
  ["Does any data leave my machine?",
   "No. Parsing, OCR, embeddings and language models all run locally. After the one-time model download the network cable can stay unplugged — the app never calls an external service, and there is no telemetry."],
  ["What kinds of files does it take?",
   "Digital and scanned PDFs, Word documents, Excel workbooks, CSVs and images. Scanned pages go through OCR; ruled tables are detected as table regions; multi-sheet workbooks are read sheet by sheet."],
  ["What exactly is a \u201Creceipt\u201D?",
   "The path from an answer back to its source: document, page, table and cell or row. Every fact, chat citation, chart bar and report table links through the index to the stored original — you read the figure where it was printed, not where the system remembered it."],
  ["What happens when two documents disagree?",
   "Nothing is silently picked. Values that disagree on the same entity, metric and period are shown side by side in chat, reports and the Conflict Radar, with likely causes (partial periods, OCR uncertainty, revised figures) and a status the officer sets: open, acknowledged or resolved."],
  ["Does it need an LLM to be useful?",
   "No. Without a model it runs in extractive mode — verbatim evidence snippets with citations, no generation. With Ollama or local Transformers available, answers, summaries and the analytical agent come online. The fact index and search never depend on a generative model."],
  ["How do I start without my own files?",
   "One click generates a curated demonstration corpus — a digital annual report, a scanned geological report, a mixed PDF, a multi-sheet workbook and a parliamentary DOCX — ingests it, and immediately shows conflicts, receipts and reports working end to end."],
];

function FaqItem({ q, a, open, onToggle }) {
  return (
    <div className={`overflow-hidden rounded-2xl border bg-white transition-colors duration-300 ${open ? "border-coalline" : "border-seam hover:border-coalline"}`}>
      <button type="button" onClick={onToggle}
              className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left"
              aria-expanded={open}>
        <span className="text-[15px] font-semibold tracking-tight">{q}</span>
        <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-seam text-stone-400 transition-all duration-300 ${open ? "rotate-45 border-coal text-coal" : ""}`} aria-hidden="true">
          <Plus className="h-3.5 w-3.5" />
        </span>
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ type: "spring", stiffness: 260, damping: 30 }}
        className="overflow-hidden">
        <p className="px-6 pb-6 text-[14px] leading-relaxed text-stone-500">{a}</p>
      </motion.div>
    </div>
  );
}

export function Faq() {
  const [open, setOpen] = useState(0);
  return (
    <section id="faq" className="py-24 md:py-28">
      <div className="mx-auto grid max-w-6xl gap-12 px-5 md:grid-cols-12 md:px-8">
        <motion.div {...rise()} className="md:col-span-4">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-coal">Questions</p>
          <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] md:text-4xl">Before you open the workspace.</h2>
          <p className="mt-4 max-w-[44ch] text-[14.5px] leading-relaxed text-stone-500">
            Everything else is in the architecture notes — or just load the
            demonstration corpus and poke at it.
          </p>
        </motion.div>

        <motion.div {...rise(0.1)} className="md:col-span-8">
          <div className="space-y-3">
            {FAQS.map(([q, a], i) => (
              <FaqItem key={q} q={q} a={a} open={open === i} onToggle={() => setOpen(open === i ? -1 : i)} />
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export function FinalCta() {
  const loadDemo = async (e) => {
    e.preventDefault();
    await fetch("/api/pipeline/demo", { method: "POST" });
    window.location.href = "/pipeline";
  };
  return (
    <section className="relative">
      <div className="h-3.5 bg-[radial-gradient(circle_at_8px_-4px,transparent_8px,rgb(var(--s-bg))_8.5px)] bg-[length:16px_14px] bg-repeat-x" aria-hidden="true"></div>
      <div className="relative overflow-hidden bg-side text-sidetext">
        <div className="pointer-events-none absolute -top-40 left-1/2 h-96 w-[60rem] -translate-x-1/2 rounded-full bg-coal/15 blur-3xl" aria-hidden="true"></div>

        <div className="relative mx-auto max-w-6xl px-5 py-24 text-center md:px-8 md:py-28">
          <motion.p {...rise()} className="font-mono text-[11px] uppercase tracking-[0.18em] text-coal">Ready when you are</motion.p>
          <motion.h2 {...rise(0.08)} className="mx-auto mt-4 max-w-[20ch] text-4xl font-bold leading-[1.05] tracking-[-0.03em] md:text-6xl">
            Stop hunting through PDFs.<br />
            <span className="text-coal">Start reading the library.</span>
          </motion.h2>
          <motion.p {...rise(0.16)} className="mx-auto mt-6 max-w-[58ch] text-[15.5px] leading-relaxed text-sidemute">
            Set up takes minutes and everything stays on this machine. Drop in
            your own reports — or generate the demonstration corpus first and see
            receipts, conflicts and reports working end to end.
          </motion.p>

          <motion.div {...rise(0.24)} className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <a href="/dashboard"
               className="group relative inline-flex items-center gap-2.5 overflow-hidden rounded-full bg-coal px-11 py-[1.15rem] text-[1.05rem] font-semibold text-white shadow-[0_4px_18px_rgb(var(--c-coal)/0.35)] transition-transform duration-300 hover:-translate-y-0.5 active:translate-y-0 animate-[cta-breathe_3.4s_ease-in-out_1.8s_infinite]">
              Open the Workspace
              <span className="pointer-events-none absolute inset-y-[-25%] left-0 w-[45%] -translate-x-[180%] skew-x-[-18deg] bg-gradient-to-r from-transparent via-white/40 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-[340%]" aria-hidden="true"></span>
              <ArrowRight className="h-[18px] w-[18px] transition-transform duration-300 group-hover:translate-x-1" />
            </a>
            <form onSubmit={loadDemo}>
              <button type="submit"
                      className="flex items-center gap-2 rounded-full border border-sideline px-7 py-[1.13rem] text-[1.05rem] font-semibold text-sidetext transition-all duration-300 hover:border-coal hover:bg-coal/10 hover:text-coal">
                <Package className="h-[18px] w-[18px]" /> Load the demo corpus first
              </button>
            </form>
          </motion.div>

          <motion.p {...rise(0.32)} className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 font-mono text-[10.5px] uppercase tracking-widest text-sidemute">
            <span className="flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-coal" /> no cloud, no API calls</span>
            <span className="flex items-center gap-1.5"><HardDrive className="h-3.5 w-3.5 text-coal" /> one machine, one database</span>
            <span className="flex items-center gap-1.5"><CircleCheck className="h-3.5 w-3.5 text-coal" /> every answer you can audit</span>
          </motion.p>
        </div>
      </div>
    </section>
  );
}

const FOOTER_COLS = [
  ["Product", [["/dashboard", "Dashboard"], ["/pipeline", "Ingest"], ["/ask", "Ask"], ["/reports", "Reports"], ["/settings", "Settings"]]],
  ["Library tools", [["/documents", "Documents"], ["/search", "Search"], ["/insights", "Insights"], ["/conflicts", "Conflict Radar"], ["/knowledge", "Knowledge Tree"]]],
];

export function Footer() {
  return (
    <footer className="border-t border-sideline bg-side text-sidetext">
      <div className="mx-auto max-w-6xl px-5 pb-10 pt-16 md:px-8">
        <div className="grid gap-12 md:grid-cols-12">
          <div className="md:col-span-5">
            <a href="/" className="flex items-center gap-2.5" aria-label="CMPDI Intelligence home">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-coal font-mono text-[14px] font-bold text-white">C</span>
              <span className="text-[16px] font-semibold tracking-tight">CMPDI&nbsp;Intelligence</span>
            </a>
            <p className="mt-4 max-w-[46ch] text-[13.5px] leading-relaxed text-sidemute">
              An offline document-intelligence workspace for coal, mining and
              geology reporting. Every number, answer and report carries a receipt
              back to its exact source.
            </p>
            <p className="mt-6 inline-flex items-center gap-2 rounded-full border border-sideline px-3.5 py-1.5 font-mono text-[10.5px] uppercase tracking-widest text-sidemute">
              <ShieldCheck className="h-3.5 w-3.5 text-coal" /> fully offline · no telemetry
            </p>
          </div>

          {FOOTER_COLS.map(([title, links]) => (
            <nav key={title} className="md:col-span-2" aria-label={title}>
              <p className="font-mono text-[10.5px] uppercase tracking-widest text-sidemute">{title}</p>
              <ul className="mt-4 space-y-2.5 text-[13.5px]">
                {links.map(([to, label]) => (
                  <li key={to}><a href={to} className="text-sidetext/85 transition-colors hover:text-coal">{label}</a></li>
                ))}
              </ul>
            </nav>
          ))}

          <nav className="md:col-span-3" aria-label="Trust">
            <p className="font-mono text-[10.5px] uppercase tracking-widest text-sidemute">Trust</p>
            <ul className="mt-4 space-y-2.5 text-[13.5px]">
              <li><a href="#faq" className="text-sidetext/85 transition-colors hover:text-coal">Questions &amp; answers</a></li>
              <li><a href="#pipeline" className="text-sidetext/85 transition-colors hover:text-coal">How evidence works</a></li>
              <li><a href="/compare" className="text-sidetext/85 transition-colors hover:text-coal">Compare documents</a></li>
              <li><a href="/ask" className="text-sidetext/85 transition-colors hover:text-coal">Analytical agent</a></li>
            </ul>
          </nav>
        </div>

        <div className="mt-14 flex flex-wrap items-center justify-between gap-3 border-t border-sideline pt-6 font-mono text-[10.5px] uppercase tracking-widest text-sidemute">
          <span>© 2026 CMPDI Intelligence · SIH26023</span>
          <span className="flex items-center gap-4">
            <a href="/" className="normal-case tracking-normal text-sidetext/85 transition-colors hover:text-coal">Home</a>
            <span aria-hidden="true" className="text-coal">·</span>
            <span>built for the desk where the reports land</span>
          </span>
        </div>
      </div>
    </footer>
  );
}
