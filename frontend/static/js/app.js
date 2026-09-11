// Live pipeline polling and small viewer interactions.

function passed(job, stage, order) {
  return order.indexOf(stage) < order.indexOf(job.stage) ? 'done' : '';
}

const STAGES = ['uploaded', 'classifying', 'extracting', 'ocr', 'normalizing',
  'chunking', 'embedding', 'indexing', 'completed'];

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

document.addEventListener('DOMContentLoaded', () => {
  refreshJobs();
  setInterval(refreshJobs, 2500);
});
