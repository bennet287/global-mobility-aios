"use client";
import { createContext, useCallback, useContext, useEffect, useId, useMemo, useState, type ReactNode } from "react";
export type V2SearchItem = { label: string; href: string; description: string; icon: "organization" | "missions" | "evidence" | "decisions" | "history"; kind: "Employee" | "Mission" | "Evidence" | "Decision" | "Event" };
const SearchContext = createContext<{ items: V2SearchItem[]; register: (key: string, items: V2SearchItem[] | null) => void }>({ items: [], register: () => {} });
export function V2NavigationContext({ children }: { children: ReactNode }) {
  const [registrations, setRegistrations] = useState<Record<string, V2SearchItem[]>>({});
  const register = useCallback((key: string, items: V2SearchItem[] | null) => setRegistrations((old) => { const next = { ...old }; if (items) next[key] = items; else delete next[key]; return next; }), []);
  const items = useMemo(() => [...new Map(Object.values(registrations).flat().map((item) => [item.href, item])).values()], [registrations]);
  return <SearchContext.Provider value={{ items, register }}>{children}</SearchContext.Provider>;
}
/** Register only already-loaded records; never fetch or persist entity search contents. */
export function useV2SearchItems(items: V2SearchItem[]) {
  const { register } = useContext(SearchContext);
  const key = useId();
  const serialized = JSON.stringify(items);
  useEffect(() => { register(key, JSON.parse(serialized) as V2SearchItem[]); return () => register(key, null); }, [key, register, serialized]);
}
export const useV2Search = () => useContext(SearchContext);
