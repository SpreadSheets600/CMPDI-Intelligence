// Live pipeline polling, sidebar/theme state, drag-drop upload, and shared
// canvas colors. The jobs strip only re-renders when the payload actually
// changes so the page never flickers while polling.

function passed(job, stage, order) {
  return order.indexOf(stage) < order.indexOf(job.stage) ? 'done' : '';
}

const STAGES = ['uploaded', 'classifying', 'extracting', 'ocr', 'normalizing',
  'chunking', 'embedding', 'indexing', 'summarizing', 'completed'];

let _lastJobsPayload = null;

async function refreshJobs() {
  const el = document.getElementById('jobstrip');
  if (!el) return;
  try {
    const jobs = await (await fetch('/api/jobs')).json();
    const payload = JSON.stringify(jobs);
    if (payload === _lastJobsPayload) return;  // nothing changed: keep the DOM
    _lastJobsPayload = payload;
    const firstRender = el.dataset.rendered !== '1';
    el.innerHTML = jobs.map((j, i) => {
      const failed = j.status === 'failed';
      const running = j.status === 'running';
      const statusIcon = failed
        ? '<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4m0 4h.01"/></svg>'
        : running
          ? '<svg class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path d="M21 12a9 9 0 1 1-6.22-8.56"/></svg>'
          : '<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>';
      return `
      <div class="rounded-xl border ${failed ? 'border-red-200 bg-red-50/60' : 'border-seam bg-white'} p-4 shadow-card ${firstRender ? 'animate-rise' : ''}" style="animation-delay:${i * 50}ms">
        <div class="flex items-baseline justify-between gap-4">
          <span class="text-sm font-semibold">${j.filename || 'unknown file'}</span>
          <span class="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide ${failed ? 'text-red-700' : j.status === 'completed' ? 'text-emerald-700' : 'text-coal'}">${statusIcon}${failed ? 'failed' : j.stage}</span>
        </div>
        <div class="mt-2 flex flex-wrap items-center gap-1 text-[10px] font-mono uppercase tracking-wide">
          ${STAGES.map(s => {
            const idx = STAGES.indexOf(j.stage);
            const mine = STAGES.indexOf(s);
            const cls = failed && s === j.stage ? 'bg-red-600 text-white border-red-600'
              : s === j.stage ? 'bg-coal text-white border-coal'
              : mine < idx ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border-seam text-stone-400';
            return `<span class="stage ${cls}">${s}</span>`;
          }).join('<span class="text-stone-300">›</span>')}
        </div>
        ${j.error ? `<div class="mt-2 font-mono text-xs text-red-700">${j.error.split('\n')[0]}</div>` : ''}
      </div>`;
    }).join('');
    el.dataset.rendered = '1';
  } catch (e) { /* server briefly unavailable: keep last render */ }
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

const SB_W = { open: '240px', collapsed: '72px' };

function setSidebar(collapsed) {
  document.documentElement.style.setProperty('--sidebar-w', SB_W[collapsed ? 'collapsed' : 'open']);
  document.body.classList.toggle('sb-collapsed', collapsed);
  localStorage.setItem('cmpdi-sidebar', collapsed ? 'collapsed' : 'open');
  const btnIcon = document.querySelector('#sidebar-collapse .sb-icon svg');
  if (btnIcon) btnIcon.style.transform = collapsed ? 'rotate(180deg)' : '';
}

function setMobile(open) {
  document.getElementById('sidebar').classList.toggle('-translate-x-full', !open);
  document.getElementById('sidebar-backdrop').classList.toggle('hidden', !open);
}

// ---------------------------------------------------------------- theme

function setTheme(dark) {
  const root = document.documentElement;
  root.classList.add('theming');
  root.classList.toggle('dark', dark);
  localStorage.setItem('cmpdi-theme', dark ? 'dark' : 'light');
  window.dispatchEvent(new CustomEvent('themechange'));
  setTimeout(() => root.classList.remove('theming'), 400);
}

// ---------------------------------------------------------------- dropzone

function initDropzone() {
  const zone = document.getElementById('dropzone');
  const input = document.getElementById('file-input');
  const list = document.getElementById('file-list');
  if (!zone || !input) return;

  const showFiles = () => {
    if (!list) return;
    const names = [...input.files].map(f => f.name);
    if (!names.length) { list.innerHTML = ''; return; }
    list.innerHTML = names.map(n =>
      `<span class="inline-flex items-center gap-1.5 rounded-full border border-coalline bg-coalsoft px-3 py-1 text-[12px] text-coal">
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
        ${n}</span>`).join('');
  };
  input.addEventListener('change', showFiles);
  if (input.files.length) showFiles();

  ['dragenter', 'dragover'].forEach(ev =>
    zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add('dropzone-hot'); }));
  ['dragleave', 'drop'].forEach(ev =>
    zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.remove('dropzone-hot'); }));
  zone.addEventListener('drop', e => {
    if (e.dataTransfer && e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      showFiles();
    }
  });
}

// ---------------------------------------------------------------- boot

document.addEventListener('DOMContentLoaded', () => {
  const collapsed = localStorage.getItem('cmpdi-sidebar') === 'collapsed';
  setSidebar(collapsed);
  document.getElementById('sidebar-collapse')?.addEventListener('click', () =>
    setSidebar(localStorage.getItem('cmpdi-sidebar') !== 'collapsed'));
  document.getElementById('sidebar-mobile')?.addEventListener('click', () => setMobile(true));
  document.getElementById('sidebar-backdrop')?.addEventListener('click', () => setMobile(false));
  document.getElementById('theme-toggle')?.addEventListener('click', () =>
    setTheme(!document.documentElement.classList.contains('dark')));

  initDropzone();
  refreshJobs();
  setInterval(refreshJobs, 2500);
});

// ---------------------------------------------------------------- documents selection

document.addEventListener('change', (e) => {
  if (!e.target.classList?.contains('doc-select')) return;
  const bar = document.getElementById('selection-bar');
  if (!bar) return;
  const picked = [...document.querySelectorAll('.doc-select:checked')].map(x => x.value);
  bar.classList.toggle('hidden', !picked.length);
  bar.classList.toggle('flex', !!picked.length);
  document.getElementById('sel-count').textContent = picked.length;
  document.getElementById('ask-selection').href =
    picked.length ? '/ask?docs=' + picked.join(',') : '#';
});
