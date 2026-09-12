// Sticky header: transparent over the hero, frosted paper once scrolled.
// The hairline progress bar tracks reading depth through the page.

export function initNav() {
  const nav = document.getElementById("landing-nav");
  if (!nav) return;
  const progress = document.getElementById("scroll-progress");
  const update = () => {
    nav.classList.toggle("is-scrolled", window.scrollY > 12);
    if (progress) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const t = max > 0 ? window.scrollY / max : 0;
      progress.style.transform = `scaleX(${t})`;
    }
  };
  update();
  window.addEventListener("scroll", update, { passive: true });
}
