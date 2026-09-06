"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  getLatestAustriaLiveOrganization,
  LiveOrganizationRequestError,
  type AustriaLiveOrganizationLatest,
} from "../lib/live-organization";

type EvidenceRead = {
  latest: AustriaLiveOrganizationLatest | null;
  loading: boolean;
  error: string | null;
  loadedAt: string | null;
};

export function useV2EvidenceSnapshot() {
  const [read, setRead] = useState<EvidenceRead>({ latest: null, loading: true, error: null, loadedAt: null });
  const requestVersion = useRef(0);

  const refresh = useCallback(async () => {
    const version = ++requestVersion.current;
    setRead((current) => ({ ...current, loading: true, error: null }));
    try {
      const latest = await getLatestAustriaLiveOrganization();
      if (version === requestVersion.current) {
        setRead({ latest, loading: false, error: null, loadedAt: new Date().toISOString() });
      }
    } catch (caught) {
      if (version !== requestVersion.current) return;
      const denied = caught instanceof LiveOrganizationRequestError && [401, 403].includes(caught.status);
      setRead((current) => ({
        latest: denied ? null : current.latest,
        loading: false,
        error: denied ? "Access to Evidence records was denied." : caught instanceof Error ? caught.message : "Evidence source unavailable.",
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
