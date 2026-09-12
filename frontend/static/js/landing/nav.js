// Sticky header: transparent over the hero, frosted paper once scrolled.

export function initNav() {
  const nav = document.getElementById("landing-nav");
  if (!nav) return;
  const update = () => nav.classList.toggle("is-scrolled", window.scrollY > 12);
  update();
  window.addEventListener("scroll", update, { passive: true });
}
