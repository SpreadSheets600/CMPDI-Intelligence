// Theme toggle: same storage key as the workspace (app.js) so the landing
// page and the workspace always agree on the mode.

const KEY = "cmpdi-theme";

export function initTheme() {
  const btn = document.getElementById("landing-theme");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const root = document.documentElement;
    const dark = !root.classList.contains("dark");
    root.classList.add("theming");
    root.classList.toggle("dark", dark);
    localStorage.setItem(KEY, dark ? "dark" : "light");
    setTimeout(() => root.classList.remove("theming"), 400);
  });
}
