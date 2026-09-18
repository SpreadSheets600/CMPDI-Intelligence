import { NavLink, useLocation, Link } from 'react-router-dom';
import { useState } from 'react';
import {
  LayoutDashboard, Workflow, Files, Search, MessageCircle, Network,
  ChartColumn, History, TriangleAlert, GitCompareArrows, FileChartColumn,
  Pickaxe, Settings, Sun, Moon, Activity, PanelLeftClose, Menu,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { useTheme, useSidebar } from '../hooks/useTheme.jsx';
import { TextLoop } from '../components/motion/text-loop.jsx';

const GROUPS = [
  {
    name: 'Workspace',
    items: [
      ['/dashboard', 'Dashboard', LayoutDashboard],
      ['/pipeline', 'Pipeline', Workflow],
      ['/documents', 'Documents', Files],
    ],
  },
  {
    name: 'Intelligence',
    items: [
      ['/search', 'Search', Search],
      ['/ask', 'Ask', MessageCircle],
      ['/reports', 'Reports', FileChartColumn],
      ['/knowledge', 'Knowledge', Network],
    ],
  },
  {
    name: 'Discover',
    items: [
      ['/assets', 'Assets', Pickaxe],
      ['/insights', 'Insights', ChartColumn],
      ['/temporal', 'Temporal', History],
      ['/conflicts', 'Conflicts', TriangleAlert],
      ['/compare', 'Compare', GitCompareArrows],
    ],
  },
];

function SidebarNav({ collapsed, onNavigate }) {
  const location = useLocation();
  const raw = '/' + location.pathname.split('/')[1];
  // /doc/:id should highlight /documents
  const current = raw === '/doc' ? '/documents' : raw;

  return (
    <div className='space-y-4'>
      {GROUPS.map(({ name, items }, groupIdx) => (
        <div key={name}>
          {/* Section header or divider when collapsed */}
          {collapsed ? (
            groupIdx > 0 ? (
              <div className='my-2.5 mx-auto w-6 border-t border-sideline/70' />
            ) : null
          ) : (
            <p className='sb-label mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-sidemute/70'>
              {name}
            </p>
          )}

          <div className='space-y-1'>
            {items.map(([to, label, Icon]) => {
              const isActive = current === to;
              return (
                <NavLink
                  key={to}
                  to={to}
                  title={label}
                  onClick={onNavigate}
                  className={`group flex items-center transition-all duration-150 ${
                    collapsed
                      ? `h-10 w-10 mx-auto justify-center rounded-xl ${
                          isActive
                            ? 'bg-coal/20 text-coal ring-1 ring-coal/30'
                            : 'text-sidemute hover:bg-white/[0.06] hover:text-sidetext'
                        }`
                      : `gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] ${
                          isActive
                            ? 'bg-coal/15 text-coal font-semibold ring-1 ring-coal/20'
                            : 'text-sidemute hover:bg-white/[0.05] hover:text-sidetext font-medium'
                        }`
                  }`}
                >
                  <Icon
                    className={`shrink-0 transition-colors ${
                      collapsed ? 'h-[19px] w-[19px]' : 'h-[17px] w-[17px]'
                    } ${isActive ? 'text-coal' : 'text-sidemute group-hover:text-sidetext'}`}
                    strokeWidth={isActive ? 2 : 1.75}
                  />

                  {!collapsed && (
                    <span className='sb-label whitespace-nowrap'>{label}</span>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function Sidebar({ collapsed, toggleCollapse, mobileOpen, closeMobile }) {
  const { dark, toggle } = useTheme();
  const location = useLocation();
  const isSettingsActive = location.pathname === '/settings';

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex flex-col overflow-hidden border-r border-sideline bg-side text-sidetext shadow-[1px_0_0_rgb(0_0_0/0.15)] transition-[width,transform] duration-300 ease-out ${
        mobileOpen ? 'max-md:translate-x-0' : 'max-md:-translate-x-full'
      }`}
      style={{ width: 'var(--sidebar-w, 240px)' }}
    >
      {/* Wordmark Header */}
      <div className='flex h-[60px] shrink-0 items-center border-b border-sideline/50 px-3'>
        <Link
          to='/dashboard'
          onClick={closeMobile}
          className={`flex items-center transition-all ${
            collapsed ? 'mx-auto justify-center' : 'gap-3 px-1'
          }`}
          title='CMPDI Intelligence'
        >
          <span className='flex h-[32px] w-[32px] shrink-0 items-center justify-center rounded-lg bg-coal font-mono text-[13px] font-bold text-white shadow-[0_2px_8px_rgba(234,138,12,0.35)]'>
            C
          </span>
          {!collapsed && (
            <div className='sb-label min-w-0 flex-1 whitespace-nowrap'>
              <span className='text-[14px] font-bold tracking-tight text-sidetext'>
                CMPDI&nbsp;
                <span className='font-normal text-sidemute'>Intelligence</span>
              </span>
            </div>
          )}
        </Link>
      </div>

      {/* Nav */}
      <nav className={`flex-1 overflow-y-auto overflow-x-hidden py-4 ${collapsed ? 'px-2' : 'px-3'}`}>
        <SidebarNav collapsed={collapsed} onNavigate={closeMobile} />
      </nav>

      {/* Footer System / Utility actions */}
      <div className={`shrink-0 border-t border-sideline/50 ${collapsed ? 'p-2 space-y-1' : 'p-3 space-y-1'}`}>
        {/* Settings link */}
        <NavLink
          to='/settings'
          onClick={closeMobile}
          title='Settings'
          className={`group flex items-center transition-all duration-150 ${
            collapsed
              ? `h-10 w-10 mx-auto justify-center rounded-xl ${
                  isSettingsActive
                    ? 'bg-coal/20 text-coal ring-1 ring-coal/30'
                    : 'text-sidemute hover:bg-white/[0.06] hover:text-sidetext'
                }`
              : `gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] ${
                  isSettingsActive
                    ? 'bg-coal/15 text-coal font-semibold ring-1 ring-coal/20'
                    : 'text-sidemute hover:bg-white/[0.05] hover:text-sidetext font-medium'
                }`
          }`}
        >
          <Settings
            className={`shrink-0 transition-colors ${
              collapsed ? 'h-[19px] w-[19px]' : 'h-[17px] w-[17px]'
            } ${isSettingsActive ? 'text-coal' : 'text-sidemute group-hover:text-sidetext'}`}
            strokeWidth={isSettingsActive ? 2 : 1.75}
          />
          {!collapsed && <span className='sb-label whitespace-nowrap'>Settings</span>}
        </NavLink>

        {/* Offline status indicator */}
        <Link
          to='/settings'
          onClick={closeMobile}
          title='System: 100% Offline / Local models'
          className={`flex items-center rounded-lg text-sidemute transition-colors hover:bg-white/[0.04] hover:text-sidetext ${
            collapsed ? 'h-9 w-9 mx-auto justify-center' : 'gap-3 px-3 py-1.5 text-[12px]'
          }`}
        >
          <Activity className='h-[16px] w-[16px] shrink-0 text-sidemute' strokeWidth={1.75} />
          {!collapsed && (
            <span className='sb-label flex items-center gap-2 whitespace-nowrap font-mono text-[11px] text-sidemute'>
              <TextLoop interval={3.2}>
                <span>Offline</span>
                <span>Local models</span>
                <span>No cloud</span>
              </TextLoop>
              <span className='h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.8)]' />
            </span>
          )}
        </Link>

        {/* Theme & Collapse controls row */}
        <div className={`flex items-center ${collapsed ? 'flex-col gap-1' : 'justify-between pt-1'}`}>
          {/* Theme toggle */}
          <button
            onClick={toggle}
            type='button'
            title={dark ? 'Switch to light theme' : 'Switch to dark theme'}
            className={`flex items-center rounded-lg text-sidemute transition-colors hover:bg-white/[0.05] hover:text-sidetext ${
              collapsed
                ? 'h-9 w-9 justify-center'
                : 'gap-2 px-3 py-1.5 text-[12px] font-medium'
            }`}
          >
            {dark ? (
              <Sun className='h-[16px] w-[16px] shrink-0' strokeWidth={1.75} />
            ) : (
              <Moon className='h-[16px] w-[16px] shrink-0' strokeWidth={1.75} />
            )}
            {!collapsed && <span className='sb-label whitespace-nowrap'>Theme</span>}
          </button>

          {/* Collapse toggle (desktop only) */}
          <button
            onClick={toggleCollapse}
            type='button'
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={`hidden items-center rounded-lg text-sidemute transition-colors hover:bg-white/[0.05] hover:text-sidetext md:flex ${
              collapsed
                ? 'h-9 w-9 justify-center'
                : 'gap-2 px-3 py-1.5 text-[12px] font-medium'
            }`}
          >
            <PanelLeftClose
              className={`h-[16px] w-[16px] shrink-0 transition-transform duration-300 ${
                collapsed ? 'rotate-180 text-coal' : ''
              }`}
              strokeWidth={1.75}
            />
            {!collapsed && <span className='sb-label whitespace-nowrap'>Collapse</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}

export default function AppShell({ children }) {
  const [collapsed, toggleCollapse] = useSidebar();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <Sidebar
        collapsed={collapsed}
        toggleCollapse={toggleCollapse}
        mobileOpen={mobileOpen}
        closeMobile={() => setMobileOpen(false)}
      />

      {/* Mobile menu button */}
      <button
        onClick={() => setMobileOpen(true)}
        className='fixed left-3 top-3 z-40 rounded-lg bg-side p-2 text-sidetext shadow-lift md:hidden'
        title='Menu'
        aria-label='Open navigation menu'
      >
        <Menu className='h-5 w-5' strokeWidth={1.75} />
      </button>

      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className='fixed inset-0 z-30 bg-ink/40 backdrop-blur-sm md:hidden'
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Main content */}
      <div
        style={{ marginLeft: 'var(--sidebar-w, 240px)' }}
        className='flex min-h-dvh flex-col transition-[margin] duration-300 ease-out max-md:ml-0'
      >
        <main className='flex-1 overflow-x-clip px-5 pb-12 pt-8 md:px-8'>
          <div className='mx-auto max-w-6xl'>{children}</div>
        </main>

        <footer className='border-t border-seam'>
          <div className='mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-4 text-[11.5px] text-stone-500 md:px-8'>
            <div className='flex items-center gap-2'>
              <span className='flex h-5 w-5 items-center justify-center rounded bg-ink font-mono text-[9.5px] font-bold text-amber-400'>
                C
              </span>
              <span className='font-medium text-ink'>CMPDI Intelligence</span>
              <span className='hidden text-stone-400 sm:inline'>
                for coal, mining and geology reporting
              </span>
            </div>
            <nav className='flex flex-wrap items-center gap-x-4 gap-y-1'>
              {[
                ['/dashboard', 'Dashboard'],
                ['/documents', 'Documents'],
                ['/ask', 'Ask'],
                ['/reports', 'Reports'],
                ['/settings', 'Settings'],
              ].map(([to, label]) => (
                <a key={to} href={to} className='transition-colors hover:text-coal'>
                  {label}
                </a>
              ))}
            </nav>
            <span className='font-mono text-[9.5px] uppercase tracking-widest text-stone-400'>
              fully offline
            </span>
          </div>
        </footer>
      </div>
    </>
  );
}
