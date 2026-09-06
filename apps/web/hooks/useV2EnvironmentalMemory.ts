"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  getLatestAustriaOrganizationEnvironmentalMemory,
  LiveOrganizationRequestError,
  type OrganizationEnvironmentalMemoryLatest,
} from "../lib/live-organization";

type MemoryRead = {
  latest: OrganizationEnvironmentalMemoryLatest | null;
  loading: boolean;
  error: string | null;
  loadedAt: string | null;
};

export function useV2EnvironmentalMemory() {
  const [read, setRead] = useState<MemoryRead>({ latest: null, loading: true, error: null, loadedAt: null });
  const requestVersion = useRef(0);

  const refresh = useCallback(async () => {
    const version = ++requestVersion.current;
    setRead((current) => ({ ...current, loading: true, error: null }));
    try {
      const latest = await getLatestAustriaOrganizationEnvironmentalMemory();
      if (version === requestVersion.current) {
        setRead({ latest, loading: false, error: null, loadedAt: new Date().toISOString() });
      }
    } catch (caught) {
      if (version !== requestVersion.current) return;
      const denied = caught instanceof LiveOrganizationRequestError && [401, 403].includes(caught.status);
      setRead((current) => ({
        latest: denied ? null : current.latest,
        loading: false,
        error: denied ? "Access to aggregate organization memory was denied." : caught instanceof Error ? caught.message : "Aggregate organization memory unavailable.",
        loadedAt: denied ? null : current.loadedAt,
      }));
    }
  }, []);

  useEffect(() => {
    void refresh();
    return () => { requestVersion.current += 1; };
  }, [refresh]);

  return { ...read, refresh };
}
