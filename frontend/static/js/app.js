// Live pipeline polling, sidebar/theme state, and shared canvas colors.

function passed(job, stage, order) {
  return order.indexOf(stage) < order.indexOf(job.stage) ? 'done' : '';
}

const STAGES = ['uploaded', 'classifying', 'extracting', 'ocr', 'normalizing',
  'chunking', 'embedding', 'indexing', 'summarizing', 'completed'];

const STAGE_CHIP = (s, cls) =>
  `<span class="stage ${cls}">${s}</span>`;

async function refreshJobs() {
  const el = document.getElementById('jobstrip');
  if (!el) return;
  const jobs = await (await fetch('/api/jobs')).json();
  el.innerHTML = jobs.map((j, i) => {
    const failed = j.status === 'failed';
    return `
    <div class="rounded-xl border ${failed ? 'border-red-200 bg-red-50/60' : 'border-seam bg-white'} p-4 shadow-card animate-rise" style="animation-delay:${i * 50}ms">
      <div class="flex items-baseline justify-between gap-4">
        <span class="text-sm font-semibold">${j.filename || 'unknown file'}</span>
        <span class="font-mono text-[11px] uppercase tracking-wide ${failed ? 'text-red-700' : j.status === 'completed' ? 'text-emerald-700' : 'text-coal'}">${failed ? 'failed' : j.stage}</span>
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-1 text-[10px] font-mono uppercase tracking-wide">
        ${STAGES.map(s => {
          const idx = STAGES.indexOf(j.stage);
          const mine = STAGES.indexOf(s);
          const cls = failed && s === j.stage ? 'bg-red-600 text-white border-red-600'
            : s === j.stage ? 'bg-coal text-white border-coal'
            : mine < idx ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
            : 'border-seam text-stone-400';
          return STAGE_CHIP(s, cls);
        }).join('<span class="text-stone-300">›</span>')}
      </div>
      ${j.error ? `<div class="mt-2 font-mono text-xs text-red-700">${j.error.split('\n')[0]}</div>` : ''}
    </div>`;
  }).join('');
}

// Canvas visuals (knowledge graph, insights chart) read theme colors from CSS
// variables so they restyle instantly when the theme flips.
function cmpdiColors() {
  const css = getComputedStyle(document.documentElement);
  const v = (name, fallback) => {
    const raw = css.getPropertyValue(name).trim();
    if (!raw) return fallback;
    const [r, g, b] = raw.split(/\s+/).map(Number);
    return `rgb(${r}, ${g}, ${b})`;
  };
  return {
    coal: v('--c-coal', '#d97706'),
    ink: v('--c-ink', '#1c1917'),
    paper: v('--c-paper', '#fafaf9'),
    surface: v('--c-surface', '#ffffff'),
    seam: v('--c-seam', '#e7e5e4'),
    muted2: v('--c-muted2', '#78716c'),
    muted3: v('--c-muted3', '#57534e'),
    dark: document.documentElement.classList.contains('dark'),
  };
}
window.cmpdiColors = cmpdiColors;

// ---------------------------------------------------------------- sidebar

function setSidebar(collapsed) {
  document.documentElement.style.setProperty('--sidebar-w', collapsed ? '68px' : '240px');
  document.getElementById('sidebar').classList.toggle('md:w-16', collapsed);
  document.getElementById('sidebar').classList.toggle('md:w-[240px]', !collapsed);
  localStorage.setItem('cmpdi-sidebar', collapsed ? 'collapsed' : 'open');
}

function setMobile(open) {
  document.getElementById('sidebar').classList.toggle('-translate-x-full', !open);
  document.getElementById('sidebar-backdrop').classList.toggle('hidden', !open);
}

document.addEventListener('DOMContentLoaded', () => {
  const collapsed = localStorage.getItem('cmpdi-sidebar') === 'collapsed';
  setSidebar(collapsed);
  const arrow = document.querySelector('#sidebar-collapse svg');
  if (arrow) arrow.style.transform = collapsed ? 'rotate(180deg)' : '';
  document.getElementById('sidebar-collapse')?.addEventListener('click', () => {
    const next = localStorage.getItem('cmpdi-sidebar') !== 'collapsed';
    setSidebar(next);
    if (arrow) arrow.style.transform = next ? 'rotate(180deg)' : '';
  });
  document.getElementById('sidebar-mobile')?.addEventListener('click', () => setMobile(true));
  document.getElementById('sidebar-backdrop')?.addEventListener('click', () => setMobile(false));

  const themeBtn = document.getElementById('theme-toggle');
  themeBtn?.addEventListener('click', () => {
    const dark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('cmpdi-theme', dark ? 'dark' : 'light');
    window.dispatchEvent(new CustomEvent('themechange'));
  });

  refreshJobs();
  setInterval(refreshJobs, 2500);
});
