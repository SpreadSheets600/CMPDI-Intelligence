import { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'motion/react';
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
import Topics from './pages/Topics.jsx';
import Conflicts from './pages/Conflicts.jsx';
import Compare from './pages/Compare.jsx';
import Topics from './pages/Topics.jsx';

import Reports from './pages/Reports.jsx';
import Review from './pages/Review.jsx';
import Settings from './pages/Settings.jsx';
import NotFound from './pages/NotFound.jsx';

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
  { match: (p) => p === '/topics', render: () => <Topics /> },
  { match: (p) => p === '/reports', render: () => <Reports /> },
  { match: (p) => p.startsWith('/reports/'), render: () => <Review /> },
  { match: (p) => p === '/settings', render: () => <Settings /> },
];

// One mounted page at a time, keyed by pathname so the enter/exit
// transition replays on navigation but query-only changes (page, sheet,
// filters) update in place. This also provides real route params, which
// useParams() readers (Viewer, Review) depend on.
function AnimatedOutlet() {
  const location = useLocation();
  return (
    <AnimatePresence mode='popLayout' initial={false}>
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
      >
        <Routes location={location}>
          <Route path='/dashboard' element={<Dashboard />} />
          <Route path='/pipeline' element={<Pipeline />} />
          <Route path='/ingested' element={<Navigate to='/pipeline' replace />} />
          <Route path='/documents' element={<Documents />} />
          <Route path='/doc/:docId' element={<Viewer />} />
          <Route path='/search' element={<Search />} />
          <Route path='/ask' element={<Ask />} />
          <Route path='/knowledge' element={<Graph />} />
          <Route path='/assets' element={<Assets />} />
          <Route path='/insights' element={<Insights />} />
          <Route path='/temporal' element={<Temporal />} />
          <Route path='/topics' element={<Topics />} />
          <Route path='/conflicts' element={<Conflicts />} />
          <Route path='/compare' element={<Compare />} />
          <Route path='/reports' element={<Reports />} />
          <Route path='/reports/:rid' element={<Review />} />
          <Route path='/settings' element={<Settings />} />
          <Route path='*' element={<NotFound />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  const location = useLocation();
  // the landing page has its own chrome (fixed nav, no sidebar)
  if (location.pathname === '/') return <Landing />;

  return (
    <AppShell>
      <ScrollToTop />
      <AnimatedOutlet />
    </AppShell>
  );
}
