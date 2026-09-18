import { useLocation } from 'react-router-dom';
import AppShell from './layout/AppShell.jsx';
import Landing from './pages/landing/index.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Pipeline from './pages/Pipeline.jsx';
import Documents from './pages/Documents.jsx';
import Viewer from './pages/Viewer.jsx';
import Search from './pages/Search.jsx';
import Ask from './pages/Ask.jsx';
import Graph from './pages/Graph.jsx';
import Assets from './pages/Assets.jsx';
import Insights from './pages/Insights.jsx';
import Temporal from './pages/Temporal.jsx';
import Conflicts from './pages/Conflicts.jsx';
import Compare from './pages/Compare.jsx';

import Reports from './pages/Reports.jsx';
import Review from './pages/Review.jsx';
import Settings from './pages/Settings.jsx';
import { TransitionPanel } from './components/motion/transition-panel.jsx';

const PANELS = [
  { match: (p) => p === '/dashboard', render: () => <Dashboard /> },
  { match: (p) => p === '/pipeline' || p === '/ingested', render: () => <Pipeline /> },
  { match: (p) => p === '/documents', render: () => <Documents /> },
  { match: (p) => p.startsWith('/doc/'), render: () => <Viewer /> },
  { match: (p) => p === '/search', render: () => <Search /> },
  { match: (p) => p === '/ask', render: () => <Ask /> },
  { match: (p) => p === '/knowledge', render: () => <Graph /> },
  { match: (p) => p === '/assets' || p.startsWith('/assets/'), render: () => <Assets /> },
  { match: (p) => p === '/insights', render: () => <Insights /> },
  { match: (p) => p === '/temporal', render: () => <Temporal /> },
  { match: (p) => p === '/conflicts', render: () => <Conflicts /> },
  { match: (p) => p === '/compare', render: () => <Compare /> },
  { match: (p) => p === '/reports', render: () => <Reports /> },
  { match: (p) => p.startsWith('/reports/'), render: () => <Review /> },
  { match: (p) => p === '/settings', render: () => <Settings /> },
];

function matchIndex(pathname) {
  const i = PANELS.findIndex((r) => r.match(pathname));
  return i === -1 ? 0 : i;
}

export default function App() {
  const location = useLocation();
  const pathname = location.pathname;
  // the landing page has its own chrome (fixed nav, no sidebar)
  if (pathname === '/') return <Landing />;

  const activeIndex = matchIndex(pathname);
  // key on pathname so param routes (/doc/:id) re-run data hooks on change
  const panels = PANELS.map((r, i) => (
    <div key={`${i}-${i === activeIndex ? pathname : 'idle'}`}>{r.render()}</div>
  ));

  return (
    <AppShell>
      <TransitionPanel
        activeIndex={activeIndex}
        transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
        variants={{
          enter: { opacity: 0, y: 12 },
          center: { opacity: 1, y: 0 },
          exit: { opacity: 0, y: -8 },
        }}
      >
        {panels}
      </TransitionPanel>
    </AppShell>
  );
}
