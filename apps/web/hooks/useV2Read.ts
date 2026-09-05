"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** A stale response can never replace the result of a newer selection or refresh. */
export function useV2Read<T>(load: () => Promise<T>) {
  const generation = useRef(0);
  const [state, setState] = useState<{ owner: typeof load; data: T | null; loading: boolean; error: string | null; updatedAt: string | null }>({ owner: load, data: null, loading: true, error: null, updatedAt: null });
  const refresh = useCallback(async () => {
    const request = ++generation.current;
    setState((old) => ({ owner: load, data: old.owner === load ? old.data : null, loading: true, error: null, updatedAt: old.owner === load ? old.updatedAt : null }));
    try {
      const data = await load();
      if (request === generation.current) setState({ owner: load, data, loading: false, error: null, updatedAt: new Date().toISOString() });
    } catch (error) {
      if (request === generation.current) setState((old) => ({ ...old, loading: false, error: error instanceof Error ? error.message : "The source could not be reached." }));
    }
  }, [load]);
  useEffect(() => { void refresh(); return () => { generation.current++; }; }, [refresh]);
  return { data: state.owner === load ? state.data : null, loading: state.owner !== load || state.loading, error: state.owner === load ? state.error : null, updatedAt: state.owner === load ? state.updatedAt : null, refresh };
}
