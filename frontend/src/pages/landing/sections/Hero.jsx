import { useEffect, useState } from "react";
import { useScroll, useTransform, motion } from "framer-motion";
import { ArrowRight, ScanText, ShieldCheck, TriangleAlert, CircleCheck } from "lucide-react";
import { getJSON } from "../../../api.js";

const EASE = [0.16, 1, 0.3, 1];
const rise = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "0px 0px -12% 0px" },
  transition: { duration: 0.65, ease: EASE, delay },
});

const NAV_LINKS = [
  ["#showcase", "Product"],
  ["#pipeline", "Evidence"],
  ["#capabilities", "Capabilities"],
  ["#faq", "FAQ"],
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    const dark = !root.classList.contains("dark");
    root.classList.add("theming");
    root.classList.toggle("dark", dark);
    localStorage.setItem("cmpdi-theme", dark ? "dark" : "light");
    setTimeout(() => root.classList.remove("theming"), 400);
  };

  return (
    <header className={`fixed inset-x-0 top-0 z-40 border-b transition-all duration-300 ${scrolled ? "border-seam bg-paper/85 backdrop-blur-md" : "border-transparent"}`}>
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-8 px-5 md:px-8">
        <a href="/" className="group flex items-center gap-2.5" aria-label="CMPDI Intelligence home">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-coal font-mono text-[14px] font-bold text-white shadow-[0_2px_10px_rgb(217_119_6/0.35)] transition-transform duration-300 group-hover:rotate-[-6deg]">C</span>
          <span className="text-[16px] font-semibold tracking-tight">CMPDI&nbsp;Intelligence</span>
        </a>
        <nav className="ml-auto hidden items-center gap-6 text-[13.5px] font-medium text-stone-500 md:flex" aria-label="Page sections">
          {NAV_LINKS.map(([to, label]) => (
            <a key={to} href={to}
               className="relative transition-colors after:absolute after:-bottom-1 after:left-0 after:h-[1.5px] after:w-full after:origin-left after:scale-x-0 after:bg-coal after:transition-transform after:duration-300 hover:text-coal hover:after:scale-x-100">
              {label}
            </a>
          ))}
        </nav>
        <button onClick={toggleTheme} type="button"
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-seam text-stone-500 transition-colors hover:border-coal hover:text-coal"
                aria-label="Toggle dark and light theme">
          <span className="hidden dark:inline">☀</span>
          <span className="inline dark:hidden">☾</span>
        </button>
        <a href="/dashboard"
           className="flex items-center gap-2 rounded-lg bg-coal px-4 py-2 text-[13.5px] font-semibold text-white shadow-[0_2px_10px_rgb(217_119_6/0.35)] transition-all hover:-translate-y-px hover:shadow-lift active:translate-y-0">
          Open Workspace <ArrowRight className="h-4 w-4" />
        </a>
      </div>
    </header>
  );
}

export function Hero({ stats }) {
  const { scrollY } = useScroll();
  const glowY = useTransform(scrollY, [0, 800], [0, 160]);
  const glowOpacity = useTransform(scrollY, [0, 800], [1, 0.35]);
  const words = ["Every", "number,"];

  return (
    <section id="hero" className="relative overflow-hidden bg-[linear-gradient(rgba(var(--c-seam)/0.4)_1px,transparent_1px),linear-gradient(90deg,rgba(var(--c-seam)/0.4)_1px,transparent_1px))] bg-[length:44px_44px]">
      <motion.div style={{ y: glowY, opacity: glowOpacity }}
                  className="pointer-events-none absolute -top-72 left-1/2 h-[46rem] w-[72rem] -translate-x-[58%] bg-[radial-gradient(closest-side,rgba(var(--c-coal)/0.14),transparent_70%)]" aria-hidden="true" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_75%_at_50%_30%,transparent_30%,rgb(var(--c-paper))_100%)]" aria-hidden="true" />

      <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 pb-24 pt-32 md:grid-cols-12 md:px-8 md:pb-28 md:pt-40">
        <div className="md:col-span-7">
          <motion.p {...rise(0.1)} className="flex items-center gap-2.5 font-mono text-[11px] uppercase tracking-[0.18em] text-coal">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-coal"></span>
            For CMPDI, CIL and subsidiary teams
          </motion.p>
          <motion.h1
            initial="hidden"
            animate="show"
            variants={{ show: { transition: { staggerChildren: 0.09, delayChildren: 0.15 } } }}
            className="mt-5 max-w-[13ch] text-5xl font-bold leading-[1.02] tracking-[-0.03em] md:text-7xl">
            {["Every", "number,"].map((w) => (
              <span key={w}>
                <motion.span className="inline-block"
                  variants={{ hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: EASE } } }}>
                  {w}
                </motion.span>{" "}
              </span>
            ))}
            <br />
            {["with", "its", "receipt."].map((w) => (
              <motion.span key={w} className="inline-block text-coal"
                variants={{ hidden: { opacity: 0, y: 28 }, show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: EASE } } }}>
                {w}&nbsp;
              </motion.span>
            ))}
          </motion.h1>
          <motion.p {...rise(0.55)} className="mt-6 max-w-[54ch] text-[17px] leading-relaxed text-stone-500">
            An offline document-intelligence workspace for coal, mining and geology
            reporting. Upload reports, scans and spreadsheets; ask questions,
            generate DOCX reports — and open the exact page, table row or
            spreadsheet cell behind any figure.
          </motion.p>
          <motion.div {...rise(0.75)} className="mt-9 flex flex-wrap items-center gap-3">
            <a href="/dashboard"
               className="group relative inline-flex items-center gap-2.5 overflow-hidden rounded-full bg-coal px-8 py-4 text-[0.9rem] font-semibold text-white shadow-[0_4px_18px_rgb(var(--c-coal)/0.35)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_10px_28px_rgb(var(--c-coal)/0.45)] active:translate-y-0">
              Open the Workspace
              <span className="pointer-events-none absolute inset-y-[-25%] left-0 w-[45%] -translate-x-[180%] skew-x-[-18deg] bg-gradient-to-r from-transparent via-white/40 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-[340%]" aria-hidden="true"></span>
              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </a>
            <a href="#pipeline"
               className="flex items-center gap-2 rounded-full border border-seamdark px-6 py-3.5 text-sm font-semibold text-ink transition-colors hover:border-coal hover:bg-coal/5 hover:text-coal">
              <ScanText className="h-4 w-4" /> How evidence works
            </a>
          </motion.div>
          <motion.p {...rise(0.95)} className="mt-6 flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-stone-400">
            <ShieldCheck className="h-3.5 w-3.5 text-coal" />
            Runs entirely on one machine · no cloud, no API calls
          </motion.p>
        </div>

        <div className="md:col-span-5">
          <motion.div
            initial={{ opacity: 0, y: -42, rotate: -2.5 }}
            animate={{ opacity: 1, y: 0, rotate: 0 }}
            transition={{ type: "spring", stiffness: 110, damping: 15, delay: 0.55 }}
            className="relative">
            <div className="absolute -inset-4 -rotate-2 rounded-3xl border border-coalline bg-coalsoft/40" aria-hidden="true"></div>
            <div className="relative rounded-2xl border border-seam bg-white p-7 shadow-lift">
              <div className="absolute inset-x-0 -top-px h-[7px] bg-[radial-gradient(circle_at_5.5px_-2px,transparent_5px,rgb(var(--c-surface))_5.5px)] bg-[length:11px_7px] bg-repeat-x" aria-hidden="true"></div>
              <div className="flex items-center justify-between">
                <span className="rounded-full border border-coalline bg-coalsoft px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide text-coal">fact</span>
                <span className="font-mono text-[10.5px] text-stone-400">FY2023-24</span>
              </div>
              <p className="mt-5 font-mono text-[42px] font-semibold leading-none tracking-tight tabular-nums">997.83 <span className="text-[16px] font-medium text-stone-500">MT</span></p>
              <p className="mt-2.5 text-[14px] text-stone-600">Raw coal production, Coal India Limited</p>
              <div className="mt-6 border-t border-dashed border-seamdark pt-5">
                <p className="font-mono text-[10px] uppercase tracking-widest text-stone-400">receipt</p>
                <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-[11.5px]">
                  {["Annual Report 2024-25", "page 11", "table 3"].map((s) => (
                    <span key={s} className="flex items-center gap-1.5">
                      <span className="rounded-md border border-seam bg-paper px-2 py-1 font-mono">{s}</span>
                      <span className="text-stone-300">›</span>
                    </span>
                  ))}
                  <span className="rounded-md border border-coal bg-coal px-2 py-1 font-mono text-white">cell</span>
                </div>
              </div>
              <div className="mt-5 flex items-center justify-between border-t border-dashed border-seamdark pt-4">
                <span className="flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-wide text-emerald-700">
                  <CircleCheck className="h-3.5 w-3.5" /> evidence grade A
                </span>
                <span className="font-mono text-[10.5px] text-stone-400">2 independent sources</span>
              </div>
            </div>
            <motion.div animate={{ y: [0, -9, 0] }} transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
                        className="absolute -bottom-6 -left-6 hidden rounded-xl border border-seam bg-white px-4 py-3 shadow-lift md:block">
              <p className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wide text-stone-400">
                <TriangleAlert className="h-3.5 w-3.5 text-coal" /> conflict radar
              </p>
              <p className="mt-1 text-[12.5px] font-semibold">2 values disagree · both cited</p>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export function SocialProof({ stats }) {
  const items = [
    ["Documents indexed", stats?.documents ?? "—"],
    ["Facts with receipts", stats?.facts ?? "—"],
    ["Searchable chunks", stats?.chunks ?? "—"],
    ["Bytes sent to the cloud", 0],
  ];
  const formats = ["Digital PDF", "Scanned PDF + OCR", "Word documents", "Excel workbooks",
    "Multi-sheet CSV", "Parliamentary replies", "Image-only pages", "SHA-256 dedupe",
    "Version chains", "Indian number formats"];
  return (
    <section className="border-y border-seam bg-white">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-y-8 px-5 py-10 md:grid-cols-4 md:px-8 md:py-12">
        {items.map(([label, value]) => (
          <div key={label} className="px-2 text-center md:px-6">
            <div className="font-mono text-3xl font-semibold tracking-tight md:text-4xl">
              {value === 0 ? <span className="text-coal">0</span> : <CountUp to={value} />}
            </div>
            <div className="mt-1.5 text-[12.5px] text-stone-500">{label}</div>
          </div>
        ))}
      </div>
      <div className="overflow-hidden border-t border-seam py-3.5" aria-hidden="true">
        <div className="flex w-max animate-[marquee_36s_linear_infinite] items-center gap-10 font-mono text-[11px] uppercase tracking-[0.2em] text-stone-400 hover:[animation-play-state:paused]">
          {[...formats, ...formats].map((f, i) => (
            <span key={i} className="flex items-center gap-10">
              <span className="whitespace-nowrap">{f}</span>
              <span className="text-coal">·</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

function CountUp({ to }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!Number.isFinite(to) || to === 0) return;
    const start = performance.now();
    let raf;
    const tick = (now) => {
      const t = Math.min((now - start) / 1400, 1);
      setN(Math.round(to * (1 - Math.pow(1 - t, 3))));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to]);
  const shown = Number.isFinite(to) && to !== 0 ? n.toLocaleString("en-IN") : "—";
  return <span>{shown}</span>;
}
