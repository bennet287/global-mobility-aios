"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function getStoredTheme(): Theme | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("gmai-theme");
  if (raw === "light" || raw === "dark") return raw;
  return null;
}

function applyTheme(theme: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    const stored = getStoredTheme();
    const initial = stored || getSystemTheme();
    setThemeState(initial);
    applyTheme(initial);

    const listener = (e: MediaQueryListEvent) => {
      if (!getStoredTheme()) {
        const next = e.matches ? "dark" : "light";
        setThemeState(next);
        applyTheme(next);
      }
    };

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, []);

  const setTheme = (next: Theme) => {
    setThemeState(next);
    applyTheme(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("gmai-theme", next);
    }
  };

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  return { theme, setTheme, toggleTheme };
}
