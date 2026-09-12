// Count-up for the social-proof band. The real value is rendered
// server-side; the animation only replaces the text while it counts, so
// no-JS visitors (and reduced-motion users) still see the true figures.

const DURATION = 1400;

export function initCountUp() {
  const nodes = document.querySelectorAll("[data-count]");
  if (!nodes.length) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced || !("IntersectionObserver" in window)) return;

  const format = (n) => Math.round(n).toLocaleString("en-IN");

  const animate = (el) => {
    const target = Number(el.dataset.count);
    if (!Number.isFinite(target) || target === 0) return;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min((now - start) / DURATION, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = format(target * eased);
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          animate(entry.target);
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.6 }
  );
  nodes.forEach((el) => observer.observe(el));
}
