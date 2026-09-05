"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Appearance = "system" | "light" | "dark";
const Preferences = createContext<{ appearance: Appearance; theme: "light" | "dark"; setAppearance: (value: Appearance) => void }>({ appearance: "system", theme: "dark", setAppearance: () => {} });
export function V2Preferences({ children }: { children: ReactNode }) {
  const [appearance, update] = useState<Appearance>("system");
  const [systemDark, setSystemDark] = useState(true);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const changed = () => setSystemDark(media.matches);
    changed(); media.addEventListener("change", changed);
    try { const stored = localStorage.getItem("aios-v2-appearance"); if (stored === "light" || stored === "dark" || stored === "system") update(stored); } catch { /* Appearance works without browser storage. */ }
    return () => media.removeEventListener("change", changed);
  }, []);
  function setAppearance(value: Appearance) {
    update(value);
    try { localStorage.setItem("aios-v2-appearance", value); } catch { /* Optional preference only. */ }
  }
  return <Preferences.Provider value={{ appearance, theme: appearance === "system" ? systemDark ? "dark" : "light" : appearance, setAppearance }}>{children}</Preferences.Provider>;
}
export const useV2Preferences = () => useContext(Preferences);
