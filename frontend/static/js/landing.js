// Landing page interactions, driven by Motion (vendored UMD build of
// Framer Motion's vanilla engine — motion.dev — so everything runs offline).
//
// Sections: theme, header, hero entrance, scroll reveals, count-up,
// FAQ accordion, parallax, receipt tilt. Elements declare intent with
// data-attributes; no page-specific CSS lives outside Tailwind utilities.
(() => {
  "use strict";

  const M = window.Motion || {};
  const { animate, inView, scroll, stagger } = M;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const EASE_OUT = [0.16, 1, 0.3, 1];

  /* ---------- theme toggle (same key as the workspace) ---------- */

  function initTheme() {
    const btn = document.getElementById("landing-theme");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const root = document.documentElement;
      const dark = !root.classList.contains("dark");
      root.classList.add("theming");
      root.classList.toggle("dark", dark);
      localStorage.setItem("cmpdi-theme", dark ? "dark" : "light");
      setTimeout(() => root.classList.remove("theming"), 400);
    });
  }

  /* ---------- header: frosted on scroll + reading progress ---------- */

  const NAV_SCROLLED = ["is-scrolled"];
  const NAV_SCROLLED_CLASSES = [
    "bg-paper/85", "backdrop-blur-md", "border-seam", "shadow-card",
  ];

  function initHeader() {
    const nav = document.getElementById("landing-nav");
    if (!nav) return;
    const progress = document.getElementById("scroll-progress");
    const update = () => {
      const scrolled = window.scrollY > 12;
      NAV_SCROLLED_CLASSES.forEach((c) => nav.classList.toggle(c, scrolled));
      nav.classList.toggle("border-transparent", !scrolled);
      if (progress) {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.transform = `scaleX(${max > 0 ? window.scrollY / max : 0})`;
      }
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
  }

  /* ---------- hero entrance: staggered headline + printed receipt ---------- */

  function initHero() {
    const words = document.querySelectorAll("[data-hero-word]");
    if (!words.length) return;

    if (reduced || !animate) return; // no-JS and reduced-motion stay visible

    words.forEach((w) => (w.style.opacity = "0"));
    animate(
      words,
      { opacity: [0, 1], y: [28, 0] },
      { delay: stagger(0.09, { startDelay: 0.15 }), duration: 0.7, ease: EASE_OUT }
    );

    document.querySelectorAll("[data-hero-fade]").forEach((el) => {
      const delay = parseFloat(el.dataset.heroFade || 0);
      el.style.opacity = "0";
      animate(el, { opacity: [0, 1], y: [16, 0] }, { delay, duration: 0.6, ease: EASE_OUT });
    });

    const receipt = document.querySelector("[data-receipt-print]");
    if (receipt) {
      receipt.style.opacity = "0";
      animate(
        receipt,
        { opacity: [0, 1], y: [-42, 0], rotate: [-2.5, 0] },
        { type: "spring", stiffness: 110, damping: 15, delay: 0.55 }
      );
    }
  }

  /* ---------- scroll reveals (data-reveal, optional data-reveal-delay) ---------- */

  function initReveals() {
    if (!inView || !animate || reduced) return;
    document.querySelectorAll("[data-reveal]").forEach((el) => {
      el.style.opacity = "0";
    });
    inView(
      "[data-reveal]",
      ({ target }) => {
        animate(
          target,
          { opacity: [0, 1], y: [18, 0] },
          { duration: 0.65, ease: EASE_OUT, delay: parseFloat(target.dataset.revealDelay || 0) }
        );
      },
      { margin: "0px 0px -12% 0px" }
    );

    // the evidence-chain connector draws itself left to right
    const line = document.querySelector("[data-draw-line]");
    if (line) {
      line.style.transform = "scaleX(0)";
      line.style.transformOrigin = "left";
      inView(
        line,
        () => animate(line, { scaleX: [0, 1] }, { duration: 1.2, ease: EASE_OUT, delay: 0.15 }),
        { margin: "0px 0px -20% 0px" } // zero-height element: any intersection fires
      );
    }
  }

  /* ---------- count-up on the live stat band ---------- */

  function initCountUp() {
    const nodes = document.querySelectorAll("[data-count]");
    if (!nodes.length || reduced || !inView) return;

    const format = (n) => Math.round(n).toLocaleString("en-IN");
    inView(
      "[data-count]",
      ({ target }) => {
        const end = Number(target.dataset.count);
        if (!Number.isFinite(end) || end === 0) return;
        const start = performance.now();
        const tick = (now) => {
          const t = Math.min((now - start) / 1400, 1);
          target.textContent = format(end * (1 - Math.pow(1 - t, 3)));
          if (t < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      },
      { amount: 0.6 }
    );
  }

  /* ---------- FAQ accordion: Motion height springs ---------- */

  function initFaq() {
    const items = document.querySelectorAll("[data-faq-item]");
    if (!items.length) return;

    const setOpen = (item, open) => {
      const body = item.querySelector("[data-faq-body]");
      const icon = item.querySelector("[data-faq-icon]");
      const trigger = item.querySelector("[data-faq-trigger]");
      if (!body) return;
      item.dataset.open = open ? "true" : "false";
      trigger?.setAttribute("aria-expanded", String(open));
      if (icon) {
        ["rotate-45", "border-coal", "text-coal"].forEach((c) => icon.classList.toggle(c, open));
      }
      if (reduced || !animate) {
        body.style.height = open ? "auto" : "0px";
        return;
      }
      body.style.overflow = "hidden";
      if (open) {
        animate(body, { height: [body.scrollHeight + "px", "auto"] }, { type: "spring", stiffness: 260, damping: 30 });
      } else {
        animate(body, { height: [body.scrollHeight + "px", "0px"] }, { type: "spring", stiffness: 260, damping: 30 });
      }
    };

    items.forEach((item) => {
      const body = item.querySelector("[data-faq-body]");
      const open = item.dataset.open === "true";
      if (body && !open) body.style.height = "0px";
      item.querySelector("[data-faq-trigger]")?.addEventListener("click", () => {
        const wasOpen = item.dataset.open === "true";
        items.forEach((other) => {
          if (other !== item && other.dataset.open === "true") setOpen(other, false);
        });
        setOpen(item, !wasOpen);
      });
    });
  }

  /* ---------- parallax: hero glow drifts up as you scroll away ---------- */

  function initParallax() {
    if (reduced || !scroll || !animate) return;
    const glow = document.querySelector("[data-parallax]");
    const hero = document.getElementById("hero");
    if (!glow || !hero) return;
    try {
      scroll(
        animate(glow, { y: [0, 160], opacity: [1, 0.35] }, { ease: "linear" }),
        { target: hero, offset: ["start start", "end start"] }
      );
    } catch {
      /* scroll-linked animation unsupported: leave the glow static */
    }
  }

  /* ---------- receipt tilt: spring-smoothed 3D pointer tracking ---------- */

  function initTilt() {
    if (reduced || !animate) return;
    const card = document.querySelector("[data-tilt]");
    if (!card || !window.matchMedia("(hover: hover)").matches) return;
    card.style.transformStyle = "preserve-3d";
    let controls = null;
    const to = (rx, ry) => {
      const next = { rotateX: rx, rotateY: ry };
      if (controls) controls.stop();
      controls = animate(card, next, { type: "spring", stiffness: 180, damping: 18 });
    };
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      to(-py * 8, px * 10);
    });
    card.addEventListener("pointerleave", () => to(0, 0));
  }

  initTheme();
  initHeader();
  initHero();
  initReveals();
  initCountUp();
  initFaq();
  initParallax();
  initTilt();
})();
