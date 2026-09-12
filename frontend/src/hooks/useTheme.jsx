import { createContext, useContext, useEffect, useState } from "react";

const ThemeCtx = createContext({ dark: true, toggle: () => {} });

export function ThemeProvider({ children }) {
  const [dark, setDark] = useState(
    () => (localStorage.getItem("cmpdi-theme") || "dark") === "dark"
  );
  const toggle = () => {
    const root = document.documentElement;
    const next = !root.classList.contains("dark");
    root.classList.add("theming");
    root.classList.toggle("dark", next);
    localStorage.setItem("cmpdi-theme", next ? "dark" : "light");
    setDark(next);
    window.dispatchEvent(new CustomEvent("themechange"));
    setTimeout(() => root.classList.remove("theming"), 400);
  };
  return <ThemeCtx.Provider value={{ dark, toggle }}>{children}</ThemeCtx.Provider>;
}

export const useTheme = () => useContext(ThemeCtx);

// Collapsed sidebar state, persisted per machine (matches workspace key).
export function useSidebar() {
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("cmpdi-sidebar") === "collapsed"
  );
  useEffect(() => {
    document.documentElement.style.setProperty(
      "--sidebar-w",
      collapsed ? "72px" : "240px"
    );
    document.body.classList.toggle("sb-collapsed", collapsed);
    localStorage.setItem("cmpdi-sidebar", collapsed ? "collapsed" : "open");
  }, [collapsed]);
  return [collapsed, () => setCollapsed((c) => !c)];
}
