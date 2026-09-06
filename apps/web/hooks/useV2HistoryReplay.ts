"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  getLatestAustriaOrganizationReplay,
  getLatestAustriaOrganizationReplayState,
  getLatestAustriaOrganizationReplayStateDiff,
  LiveOrganizationRequestError,
  type OrganizationReplayLatest,
  type OrganizationReplayState,
  type OrganizationReplayStateDiff,
} from "../lib/live-organization";

type HistoryReplayRead = {
  latest: OrganizationReplayLatest | null;
  loading: boolean;
  error: string | null;
  loadedAt: string | null;
};

export function useV2HistoryReplay() {
  const [read, setRead] = useState<HistoryReplayRead>({ latest: null, loading: true, error: null, loadedAt: null });
  const requestVersion = useRef(0);

  const refresh = useCallback(async () => {
    const version = ++requestVersion.current;
    setRead((current) => ({ ...current, loading: true, error: null }));
    try {
      const latest = await getLatestAustriaOrganizationReplay();
      if (version === requestVersion.current) setRead({ latest, loading: false, error: null, loadedAt: new Date().toISOString() });
    } catch (caught) {
      if (version !== requestVersion.current) return;
      const denied = caught instanceof LiveOrganizationRequestError && [401, 403].includes(caught.status);
      setRead((current) => ({
        latest: denied ? null : current.latest,
        loading: false,
        error: denied ? "Access to canonical replay was denied." : caught instanceof Error ? caught.message : "Canonical replay unavailable.",
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

type CursorRead = {
  state: OrganizationReplayState | null;
  diff: OrganizationReplayStateDiff | null;
  stateLoading: boolean;
  diffLoading: boolean;
  stateError: string | null;
  diffError: string | null;
};

export function useV2ReplayCursor(cursorActivityId: string | null, fromActivityId: string | null) {
  const [read, setRead] = useState<CursorRead>({
    state: null,
    diff: null,
    stateLoading: false,
    diffLoading: false,
    stateError: null,
    diffError: null,
  });
  const requestVersion = useRef(0);

  useEffect(() => {
    const version = ++requestVersion.current;
    if (!cursorActivityId) {
      setRead({ state: null, diff: null, stateLoading: false, diffLoading: false, stateError: null, diffError: null });
      return () => { requestVersion.current += 1; };
    }

    setRead((current) => ({
      ...current,
      state: null,
      diff: null,
      stateLoading: true,
      diffLoading: Boolean(fromActivityId && fromActivityId !== cursorActivityId),
      stateError: null,
      diffError: null,
    }));

    void getLatestAustriaOrganizationReplayState(cursorActivityId)
      .then((state) => {
        if (version === requestVersion.current) setRead((current) => ({ ...current, state, stateLoading: false }));
      })
      .catch((caught) => {
        if (version !== requestVersion.current) return;
        setRead((current) => ({ ...current, stateLoading: false, stateError: caught instanceof Error ? caught.message : "As-of replay state unavailable." }));
      });

    if (fromActivityId && fromActivityId !== cursorActivityId) {
      void getLatestAustriaOrganizationReplayStateDiff(fromActivityId, cursorActivityId)
        .then((diff) => {
          if (version === requestVersion.current) setRead((current) => ({ ...current, diff, diffLoading: false }));
        })
        .catch((caught) => {
          if (version !== requestVersion.current) return;
          setRead((current) => ({ ...current, diffLoading: false, diffError: caught instanceof Error ? caught.message : "Replay cursor comparison unavailable." }));
        });
    }

    return () => { requestVersion.current += 1; };
  }, [cursorActivityId, fromActivityId]);

  return read;
}
