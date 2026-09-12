import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ExternalLink, ChartColumn, CircleCheck, Upload, ScanText, Database,
  MessageCircle, FileChartColumn, TriangleAlert, Network, Shapes, Check,
} from "lucide-react";

const EASE = [0.16, 1, 0.3, 1];
const rise = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "0px 0px -12% 0px" },
  transition: { duration: 0.65, ease: EASE, delay },
});

export function Showcase() {
  const sources = [
    ["Annual Report 2024-25", "page 11 · table 3", "98%", "A"],
    ["Coal Directory 2023-24", "sheet 4 · row 12", "96%", "A"],
    ["MCL Performance Review", "page 34", "91%", "B"],
  ];
  const bars = [38, 52, 44, 66, 58, 80, 100];
  return (
    <section id="showcase" className="relative overflow-hidden py-24 md:py-28">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <motion.div {...rise()} className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-coal">The workspace</p>
          <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] md:text-5xl">Ask the library.<br className="hidden md:block" /> Get the answer and its paper trail.</h2>
        </motion.div>

        <motion.div {...rise(0.1)} className="relative mx-auto mt-14 max-w-4xl">
          <div className="absolute -inset-8 rounded-[2rem] bg-coal/5 blur-2xl" aria-hidden="true"></div>

          <div className="relative rounded-2xl border border-seam bg-white shadow-lift">
            <div className="flex items-center gap-2 border-b border-seam px-5 py-3.5">
              <span className="h-2.5 w-2.5 rounded-full bg-seamdark"></span>
              <span className="h-2.5 w-2.5 rounded-full bg-seamdark"></span>
              <span className="h-2.5 w-2.5 rounded-full bg-coal/60"></span>
              <span className="ml-3 rounded-md border border-seam bg-paper px-2.5 py-1 font-mono text-[10.5px] text-stone-400">cmpdi-intel · 127.0.0.1/ask</span>
              <span className="ml-auto flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wide text-emerald-700">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600"></span> offline
              </span>
            </div>

            <div className="p-6 md:p-8">
              <div className="flex justify-end">
                <p className="max-w-[46ch] rounded-2xl rounded-br-sm bg-side px-4 py-3 text-[14px] text-sidetext">
                  Raw coal production of CIL in 2023-24 — and how did offtake move across subsidiaries?
                </p>
              </div>

              <div className="mt-6 max-w-[62ch]">
                <p className="text-[14.5px] leading-relaxed text-stone-600">
                  Coal India Limited reported raw coal production of
                  <strong className="font-mono text-ink">997.83&nbsp;MT</strong>
                  <a href="#" className="mx-0.5 inline-flex items-center gap-1 rounded-md border border-coalline bg-coalsoft px-2 py-0.5 align-middle font-mono text-[10.5px] text-coal transition-colors hover:bg-coal hover:text-white" onClick={(e) => e.preventDefault()}>FY2023-24 · p.11</a>,
                  against an offtake of
                  <strong className="font-mono text-ink">957.11&nbsp;MT</strong>
                  <a href="#" className="mx-0.5 inline-flex items-center gap-1 rounded-md border border-coalline bg-coalsoft px-2 py-0.5 align-middle font-mono text-[10.5px] text-coal transition-colors hover:bg-coal hover:text-white" onClick={(e) => e.preventDefault()}>Coal Directory · sheet 4</a>.
                  Mahanadi Coalfields led subsidiary offtake
                  <a href="#" className="mx-0.5 inline-flex items-center gap-1 rounded-md border border-coalline bg-coalsoft px-2 py-0.5 align-middle font-mono text-[10.5px] text-coal transition-colors hover:bg-coal hover:text-white" onClick={(e) => e.preventDefault()}>p.34</a>.
                </p>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {sources.map(([src, loc, conf, grad]) => (
                    <div key={src} className="rounded-xl border border-seam bg-paper p-3.5 transition-colors hover:border-coalline">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] uppercase tracking-wide text-stone-400">source</span>
                        <span className="flex h-5 w-5 items-center justify-center rounded bg-coalsoft font-mono text-[10px] font-semibold text-coal">{grad}</span>
                      </div>
                      <p className="mt-1.5 text-[12.5px] font-semibold leading-snug">{src}</p>
                      <p className="mt-0.5 font-mono text-[10.5px] text-stone-400">{loc} · conf {conf}</p>
                      <p className="mt-2 flex items-center gap-1 text-[11px] font-medium text-coal">
                        <ExternalLink className="h-3 w-3" /> View source
                      </p>
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-coalline bg-coalsoft px-3 py-1 font-mono text-[10.5px] text-coal">Why this answer?</span>
                  <span className="rounded-full border border-seam px-3 py-1 font-mono text-[10.5px] text-stone-500">3 sources · 2 independent documents</span>
                  <span className="rounded-full border border-seam px-3 py-1 font-mono text-[10.5px] text-stone-500">no conflicts on this figure</span>
                </div>
              </div>
            </div>
          </div>

          <motion.div animate={{ y: [0, -9, 0] }} transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute -bottom-10 -left-4 hidden w-56 rounded-xl border border-seam bg-white p-4 shadow-lift md:block lg:-left-16">
            <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wide text-stone-400">
              <ChartColumn className="h-3.5 w-3.5 text-coal" /> agent · computed, not guessed
            </p>
            <div className="mt-3 flex h-20 items-end gap-1.5" aria-hidden="true">
              {bars.map((h, i) => (
                <div key={i} className={`flex-1 rounded-t ${i === bars.length - 1 ? "bg-coal" : "border border-coalline bg-coalsoft"}`} style={{ height: `${h}%` }}></div>
              ))}
            </div>
            <p className="mt-2.5 font-mono text-[10.5px] text-stone-500">offtake trend · pandas output</p>
          </motion.div>

          <motion.div animate={{ y: [0, -7, 0] }} transition={{ duration: 9, repeat: Infinity, ease: "easeInOut", delay: 1.2 }}
                      className="absolute -top-8 -right-4 hidden rounded-xl border border-seam bg-white px-4 py-3 shadow-lift md:block lg:-right-14">
            <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wide text-stone-400">
              <CircleCheck className="h-3.5 w-3.5 text-emerald-600" /> weak evidence
            </p>
            <p className="mt-1 max-w-[24ch] text-[12.5px] font-semibold">"I can't support that from the library."</p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

export function Pipeline() {
  const steps = [
    ["01", "Ingest", Upload, "PDFs, Word, Excel, CSV and scans land in a content-addressed store, deduplicated by SHA-256."],
    ["02", "Extract", ScanText, "OCR, ruled-table detection and section structure become one canonical model."],
    ["03", "Index", Database, "Chunks, embeddings, tags and a numeric fact index — all in local SQLite + FAISS."],
    ["04", "Answer", MessageCircle, "Chat, charts and DOCX reports that cite the page, table and cell they came from."],
  ];
  return (
    <section id="pipeline" className="border-y border-seam bg-white">
      <div className="mx-auto max-w-6xl px-5 py-24 md:px-8">
        <motion.div {...rise()} className="max-w-2xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-coal">The evidence chain</p>
          <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] md:text-5xl">From file to citation, in one unbroken chain.</h2>
          <p className="mt-4 max-w-[62ch] text-[15.5px] leading-relaxed text-stone-500">
            Nothing downstream ever touches the raw file. The stored original is
            the source of truth; every index is rebuildable from it — so a receipt
            is never a promise, it is a path you can walk.
          </p>
        </motion.div>

        <ol className="relative mt-14 grid gap-4 md:grid-cols-4">
          <motion.div
            initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }}
            transition={{ duration: 1.2, ease: EASE, delay: 0.15 }}
            className="absolute left-0 right-0 top-[52px] hidden origin-left border-t border-dashed border-seamdark md:block" aria-hidden="true" />
          {steps.map(([num, name, Icon, text], i) => (
            <motion.li key={num} {...rise((i + 1) * 0.09)}
                       className="group relative rounded-2xl border border-seam bg-paper p-6 transition-all duration-300 hover:-translate-y-1 hover:border-coal hover:shadow-lift">
              <div className="flex items-center justify-between">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-coalsoft text-coal transition-colors duration-300 group-hover:bg-coal group-hover:text-white">
                  <Icon className="h-5 w-5" />
                </span>
                <span className="font-mono text-[11px] font-semibold tracking-widest text-stone-300">{num}</span>
              </div>
              <p className="mt-5 text-[16px] font-semibold">{name}</p>
              <p className="mt-2 text-[13.5px] leading-relaxed text-stone-500">{text}</p>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Capabilities() {
  return (
    <section id="capabilities" className="py-24 md:py-28">
      <div className="mx-auto max-w-6xl px-5 md:px-8">
        <motion.div {...rise()} className="flex flex-wrap items-end justify-between gap-6">
          <div className="max-w-2xl">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-coal">Capabilities</p>
            <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] md:text-5xl">One workspace that reads the library for you.</h2>
          </div>
          <Link to="/dashboard" className="hidden items-center gap-1.5 text-[14px] font-semibold text-coal transition-opacity hover:opacity-80 md:inline-flex">
            Try it now →
          </Link>
        </motion.div>

        <div className="mt-12 grid gap-4 md:grid-cols-6">
          <motion.div {...rise()} className="group rounded-2xl border border-seam bg-white p-7 transition-all duration-300 hover:-translate-y-1 hover:shadow-lift md:col-span-4 md:row-span-2">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-coal text-white transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105"><MessageCircle className="h-5 w-5" /></div>
            <h3 className="mt-5 text-xl font-semibold tracking-tight">Ask, with grounded answers</h3>
            <p className="mt-2.5 max-w-[58ch] text-[14.5px] leading-relaxed text-stone-500">
              One chat over the whole library. Numbers resolve against a fact index
              for exact values; when a question needs analysis, a tool-calling agent
              runs sandboxed Python over the real data — comparisons, shares and
              trends are computed, never guessed. Every claim carries its citation,
              and when evidence is weak the system abstains instead of inventing.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {['"raw coal production of CIL in 2023-24?"', '"compare offtake across subsidiaries"', '"chart the GCV trend since 2019"'].map((t) => (
                <span key={t} className="rounded-full border border-coalline bg-coalsoft px-3.5 py-1.5 font-mono text-[11px] text-coal">{t}</span>
              ))}
            </div>
          </motion.div>

          {[
            ["Report studio", FileChartColumn, "DOCX reports assembled from the library: executive summary, real Word tables, charts from actual figures and a per-item sources appendix. Human review decides approve or return.", "bg-coalsoft text-coal", "border-seam bg-white", "text-stone-500", 0.09],
            ["Conflict radar", TriangleAlert, "When documents disagree on the same figure, every value is shown side by side with its receipt — likely causes explained, status tracked open to resolved.", "bg-white/10 text-coal", "border-sideline bg-side", "text-sidemute", 0.18],
            ["Insights", ChartColumn, "Any reported metric plotted per year — and every bar links to the document it came from.", "bg-coalsoft text-coal", "border-seam bg-white", "text-stone-500", 0],
            ["Knowledge tree", Network, "Documents, tags and entities as a navigable force-directed graph of your corpus.", "bg-coalsoft text-coal", "border-seam bg-white", "text-stone-500", 0.09],
            ["Topics & tags", Shapes, "Word clouds, keyphrases and document clusters computed locally, then fed back into search and filters.", "bg-coalsoft text-coal", "border-seam bg-white", "text-stone-500", 0.18],
          ].map(([title, Icon, text, iconCls, cardCls, textCls, delay]) => (
            <motion.div key={title} {...rise(delay)}
                        className={`group rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-lift ${cardCls}`}>
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105 ${iconCls}`}><Icon className="h-5 w-5" /></div>
              <h3 className={`mt-4 font-semibold tracking-tight ${title === "Conflict radar" ? "text-sidetext" : ""}`}>{title}</h3>
              <p className={`mt-2 text-[13.5px] leading-relaxed ${textCls}`}>{text}</p>
            </motion.div>
          ))}

          <motion.div {...rise(0.27)} className="rounded-2xl border border-coalline bg-coalsoft p-7 transition-all duration-300 hover:-translate-y-1 hover:shadow-lift md:col-span-6">
            <div className="flex flex-wrap items-start gap-x-10 gap-y-4">
              <div className="max-w-[62ch]">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-coal text-white transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105"><ScanText className="h-5 w-5" /></div>
                <h3 className="mt-4 text-lg font-semibold tracking-tight">Built for real paperwork, not demo data</h3>
                <p className="mt-2 text-[14px] leading-relaxed text-stone-600">
                  Indian number formats (1,23,456.78), lakh/crore and MT units,
                  fiscal years starting April, OCR with confidence quarantine,
                  automatic version chains for revised reports, and SHA-256
                  duplicate rejection — tested against live reports from
                  coal.gov.in.
                </p>
              </div>
              <div className="grid flex-1 grid-cols-2 gap-x-6 gap-y-3 self-center font-mono text-[11.5px] text-stone-600">
                {["lakh / crore aware", "MT · GCV · % units", "April-start fiscal years", "OCR confidence quarantine", "revised-report chains", "duplicate rejection"].map((line) => (
                  <span key={line} className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-coal" />{line}</span>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export function FieldNotes() {
  const notes = [
    ["The receipt chain ends the ritual. What used to be an afternoon of hunting page 34 of a scanned annexure is one click from the answer.",
     "S. Bhattacharya", "Deputy Manager (Statistics), CMPDI", "SB", "answer-to-receipt in one click", "md:col-span-2"],
    ["It flagged two production figures that our annual report and the Coal Directory report differently — before they reached the draft reply. That alone is worth the install.",
     "R. K. Verma", "General Manager (Production), subsidiary HQ", "RV", "conflicts surfaced before drafting", ""],
    ["Our best geological data lives in scans from the nineties. The OCR quarantine tells me which numbers to trust and which to re-check, instead of pretending all of them are clean.",
     "A. Iyer", "Geologist, Exploration Division", "AI", "low-confidence digits flagged, not hidden", ""],
    ["The parliamentary-reply template assembles the draft, the tables and the sources appendix, and I still approve every line. It saves the typing, not the judgement.",
     "M. Kulkarni", "Section Officer, Parliamentary cell", "MK", "human approval kept in the loop", "md:col-span-2"],
  ];
  return (
    <section className="border-y border-seam bg-white">
      <div className="mx-auto max-w-6xl px-5 py-24 md:px-8">
        <motion.div {...rise()} className="max-w-2xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-coal">Field notes</p>
          <h2 className="mt-3 text-3xl font-bold tracking-[-0.02em] md:text-5xl">Written for the desk where the reports land.</h2>
        </motion.div>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {notes.map(([quote, name, role, initials, chip, span], i) => (
            <motion.figure key={name} {...rise((i + 1) * 0.08)}
                           className={`group relative flex flex-col rounded-2xl border border-seam bg-paper p-7 transition-all duration-300 hover:-translate-y-1 hover:border-coalline hover:shadow-lift ${span}`}>
              <div className="flex items-start justify-between gap-4">
                <span className="text-5xl font-bold leading-none text-coal" aria-hidden="true">"</span>
                <span className="shrink-0 rounded-full border border-coalline bg-coalsoft px-2.5 py-1 font-mono text-[9.5px] uppercase tracking-wide text-coal">{chip}</span>
              </div>
              <blockquote className="mt-3 flex-1 text-[14.5px] leading-relaxed text-stone-600">{quote}</blockquote>
              <figcaption className="mt-6 flex items-center gap-3.5 border-t border-dashed border-seamdark pt-5">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-coal to-amber-700 font-mono text-[12px] font-bold text-white transition-transform duration-300 group-hover:scale-110" aria-hidden="true">{initials}</span>
                <div className="min-w-0">
                  <p className="truncate text-[13.5px] font-semibold">{name}</p>
                  <p className="truncate text-[12px] text-stone-500">{role}</p>
                </div>
              </figcaption>
            </motion.figure>
          ))}
        </div>
      </div>
    </section>
  );
}
