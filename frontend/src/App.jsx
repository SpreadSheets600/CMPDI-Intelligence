import { useState, useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import AppShell from "./layout/AppShell.jsx";
import Landing from "./pages/Landing.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Pipeline from "./pages/Pipeline.jsx";
import Documents from "./pages/Documents.jsx";
import Viewer from "./pages/Viewer.jsx";
import Search from "./pages/Search.jsx";
import Ask from "./pages/Ask.jsx";
import Graph from "./pages/Graph.jsx";
import Insights from "./pages/Insights.jsx";
import Conflicts from "./pages/Conflicts.jsx";
import Compare from "./pages/Compare.jsx";
import Topics from "./pages/Topics.jsx";
import Reports from "./pages/Reports.jsx";
import Review from "./pages/Review.jsx";
import Settings from "./pages/Settings.jsx";

export default function App() {
  const location = useLocation();
  // the landing page has its own chrome (fixed nav, no sidebar)
  const bare = location.pathname === "/";
  return bare ? (
    <Routes>
      <Route path="/" element={<Landing />} />
    </Routes>
  ) : (
    <AppShell>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/ingested" element={<Pipeline />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/doc/:docId" element={<Viewer />} />
          <Route path="/search" element={<Search />} />
          <Route path="/ask" element={<Ask />} />
          <Route path="/knowledge" element={<Graph />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/conflicts" element={<Conflicts />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/topics" element={<Topics />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/reports/:rid/review" element={<Review />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </AnimatePresence>
    </AppShell>
  );
}
