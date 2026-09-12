import { NavLink } from "react-router-dom";
import { useState } from "react";
import {
  LayoutDashboard, Workflow, Files, Search, MessageCircle, Network,
  ChartColumn, TriangleAlert, GitCompareArrows, Shapes, FileChartColumn,
  Settings, Sun, Moon, Activity, PanelLeftClose, Menu,
} from "lucide-react";
import { useTheme, useSidebar } from "../hooks/useTheme.jsx";

const GROUPS = [
  ["Workspace", [
    ["/dashboard", "Dashboard", LayoutDashboard],
    ["/pipeline", "Pipeline", Workflow],
    ["/documents", "Documents", Files],
  ]],
  ["Intelligence", [
    ["/search", "Search", Search],
    ["/ask", "Ask", MessageCircle],
    ["/knowledge", "Knowledge", Network],
  ]],
  ["Discover", [
    ["/insights", "Insights", ChartColumn],
    ["/conflicts", "Conflicts", TriangleAlert],
    ["/compare", "Compare", GitCompareArrows],
    ["/topics", "Topics", Shapes],
    ["/reports", "Reports", FileChartColumn],
  ]],
  ["System", [
    ["/settings", "Settings", Settings],
  ]],
];

function Sidebar({ collapsed, toggleCollapse, mobileOpen, closeMobile }) {
  const { dark, toggle } = useTheme();
  const linkCls = ({ isActive }) =>
    `group relative flex items-center gap-3 rounded-lg px-2.5 py-2 text-[13.5px] font-medium transition-colors duration-150 ${
      isActive ? "bg-coal/15 text-coal" : "text-sidemute hover:bg-sidecard hover:text-sidetext"
    }`;
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex flex-col overflow-hidden border-r border-black/40 bg-side text-sidetext shadow-[1px_0_0_rgb(0_0_0/0.2)] transition-all duration-300 ease-out ${
        mobileOpen ? "max-md:translate-x-0" : "max-md:-translate-x-full"
      }`}
      style={{ width: "var(--sidebar-w, 240px)" }}
    >
      <div className="flex h-16 shrink-0 items-center gap-3 px-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-coal font-mono text-[15px] font-bold text-white shadow-[0_2px_10px_rgb(217_119_6/0.4)]">C</span>
        <span className="sb-label whitespace-nowrap text-[15px] font-semibold tracking-tight">CMPDI&nbsp;Intelligence</span>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto overflow-x-hidden px-3 py-3">
        {GROUPS.map(([group, items]) => (
          <div key={group}>
            <p className="sb-label sb-hide mb-1 px-2.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-sidemute">{group}</p>
            <div className="space-y-0.5">
              {items.map(([to, label, Icon]) => (
                <NavLink key={to} to={to} title={label} className={linkCls} onClick={closeMobile}>
                  {({ isActive }) => (
                    <>
                      <span className={`absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-r bg-coal transition-opacity duration-200 ${isActive ? "opacity-100" : "opacity-0 group-hover:opacity-40"}`} />
                      <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={2} />
                      <span className="sb-label whitespace-nowrap">{label}</span>
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="shrink-0 space-y-0.5 border-t border-sideline p-3">
        <button onClick={toggle} title="Toggle theme"
                className="flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-[13px] font-medium text-sidemute transition-colors hover:bg-sidecard hover:text-sidetext">
          {dark ? <Sun className="h-[18px] w-[18px] shrink-0" /> : <Moon className="h-[18px] w-[18px] shrink-0" />}
          <span className="sb-label whitespace-nowrap">Theme</span>
        </button>
        <a href="/settings" title="Model status"
           className="flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-[13px] font-medium text-sidemute transition-colors hover:bg-sidecard hover:text-sidetext">
          <Activity className="h-[18px] w-[18px] shrink-0" />
          <span className="sb-label flex items-center gap-2 whitespace-nowrap">Offline
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 shadow-[0_0_6px_rgb(16_185_129/0.8)]"></span>
          </span>
        </a>
        <button onClick={toggleCollapse} title="Collapse sidebar"
                className="hidden w-full items-center gap-3 rounded-lg px-2.5 py-2 text-[13px] font-medium text-sidemute transition-colors hover:bg-sidecard hover:text-sidetext md:flex">
          <span className="flex h-[18px] w-[18px] shrink-0 items-center justify-center">
            <PanelLeftClose className="h-[18px] w-[18px] transition-transform duration-300" style={{ transform: collapsed ? "rotate(180deg)" : "" }} />
          </span>
          <span className="sb-label whitespace-nowrap">Collapse</span>
        </button>
      </div>
    </aside>
  );
}

export default function AppShell({ children }) {
  const [collapsed, toggleCollapse] = useSidebar();
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <>
      <Sidebar collapsed={collapsed} toggleCollapse={toggleCollapse}
               mobileOpen={mobileOpen} closeMobile={() => setMobileOpen(false)} />
      <button onClick={() => setMobileOpen(true)}
              className="fixed left-3 top-3 z-40 rounded-lg bg-side p-2 text-sidetext shadow-lift md:hidden" title="Menu">
        <Menu className="h-5 w-5" />
      </button>
      <div
        className={`fixed inset-0 z-30 bg-ink/50 md:hidden ${mobileOpen ? "" : "hidden"}`}
        onClick={() => setMobileOpen(false)}
      />
      <div style={{ marginLeft: "var(--sidebar-w, 240px)" }}
           className="flex min-h-dvh flex-col transition-[margin] duration-300 ease-out max-md:ml-0">
        <main className="flex-1 overflow-x-clip px-5 pb-10 pt-8 md:px-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
        <footer className="border-t border-seam">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-5 text-[12.5px] text-stone-500 md:px-8">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded bg-ink font-mono text-[10px] font-bold text-amber-400">C</span>
              <span className="font-medium text-ink">CMPDI Intelligence</span>
              <span className="hidden text-stone-400 sm:inline">for coal, mining and geology reporting</span>
            </div>
            <nav className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <a href="/dashboard" className="transition-colors hover:text-coal">Dashboard</a>
              <a href="/documents" className="transition-colors hover:text-coal">Documents</a>
              <a href="/ask" className="transition-colors hover:text-coal">Ask</a>
              <a href="/reports" className="transition-colors hover:text-coal">Reports</a>
              <a href="/settings" className="transition-colors hover:text-coal">Settings</a>
            </nav>
            <span className="flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-widest text-stone-400">
              fully offline
            </span>
          </div>
        </footer>
      </div>
    </>
  );
}
