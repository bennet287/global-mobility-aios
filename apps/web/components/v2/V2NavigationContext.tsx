"use client";

// AIOS V2 Q2 — scoped loaded-record registry for command-palette selection.
//
// Pages register records they have ALREADY loaded from canonical sources so the
// command palette can offer entity selection without issuing new requests.
//
// Invariants:
// - register only records the page already holds; never fetch for search;
// - never persist registry contents (no localStorage/sessionStorage/cookies);
// - the registry is navigation metadata, not organization truth or authority;
// - registrations are removed when the registering component unmounts.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { V2NavigationIcon } from "../../lib/v2/navigation";

export type V2SearchItemKind = "Employee" | "Mission" | "Evidence" | "Decision" | "Event";

export type V2SearchItem = {
  readonly id: string;
  readonly label: string;
  readonly description: string;
  readonly href: string;
  readonly icon: V2NavigationIcon;
  readonly kind: V2SearchItemKind;
};

type V2SearchRegistry = {
  readonly items: readonly V2SearchItem[];
  readonly register: (key: string, items: readonly V2SearchItem[] | null) => void;
};

const SearchContext = createContext<V2SearchRegistry>({ items: [], register: () => {} });

export function V2NavigationContext({ children }: { children: ReactNode }) {
  const [registrations, setRegistrations] = useState<Record<string, readonly V2SearchItem[]>>({});

  const register = useCallback((key: string, items: readonly V2SearchItem[] | null) => {
    setRegistrations((current) => {
      const next = { ...current };
      if (items && items.length) next[key] = items;
      else delete next[key];
      return next;
    });
  }, []);

  const items = useMemo(() => {
    const byIdentity = new Map<string, V2SearchItem>();
    for (const group of Object.values(registrations)) {
      for (const item of group) {
        const identity = `${item.kind}:${item.id}`;
        if (!byIdentity.has(identity)) byIdentity.set(identity, item);
      }
    }
    return [...byIdentity.values()];
  }, [registrations]);

  return <SearchContext.Provider value={{ items, register }}>{children}</SearchContext.Provider>;
}

export function useV2SearchItems(items: readonly V2SearchItem[]) {
  const { register } = useContext(SearchContext);
  const key = useId();
  const serialized = JSON.stringify(items);
  useEffect(() => {
    register(key, JSON.parse(serialized) as V2SearchItem[]);
    return () => register(key, null);
  }, [key, register, serialized]);
}

export function useV2Search() {
  return useContext(SearchContext);
}
