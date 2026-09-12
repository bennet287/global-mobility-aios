"use client";

import { useEffect, useRef } from "react";

import {
  getLatestAustriaLivingScene,
  type LivingOrganizationSceneLatest,
} from "../lib/live-organization";

export const LIVING_HQ_SCENE_REFRESH_MS = 5000;
export const LIVING_HQ_INITIAL_SCENE_REFRESH_MS = 8000;

type LivingOrganizationSceneRefreshOptions = {
  enabled: boolean;
  rootWorkItemId: string | null;
  onScene: (latest: LivingOrganizationSceneLatest) => void;
  onError?: (error: unknown) => void;
};

function canonicalSceneFingerprint(latest: LivingOrganizationSceneLatest): string {
  const scene = latest.scene;
  if (!scene) return "scene:unavailable";
  return JSON.stringify({
    contract_version: scene.contract_version,
    root_work_item_id: scene.root_work_item_id,
    objective_key: scene.objective_key,
    coverage: scene.coverage,
    deterministic: scene.deterministic,
    predictive: scene.predictive,
    environmental: scene.environmental,
    truth: scene.truth,
  });
}

export function useLivingOrganizationSceneRefresh({
  enabled,
  rootWorkItemId,
  onScene,
  onError,
}: LivingOrganizationSceneRefreshOptions) {
  const inFlight = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const disposed = useRef(false);
  const onSceneRef = useRef(onScene);
  const onErrorRef = useRef(onError);
  const lastCanonicalFingerprint = useRef<string | null>(null);
  const hasCompletedAutomaticRead = useRef(false);

  useEffect(() => {
    onSceneRef.current = onScene;
  }, [onScene]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    if (!enabled || !rootWorkItemId) return;

    disposed.current = false;
    lastCanonicalFingerprint.current = null;
    hasCompletedAutomaticRead.current = false;

    const clearTimer = () => {
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
      }
    };

    const schedule = () => {
      clearTimer();
      if (disposed.current || document.visibilityState !== "visible") return;
      const delay = hasCompletedAutomaticRead.current
        ? LIVING_HQ_SCENE_REFRESH_MS
        : LIVING_HQ_INITIAL_SCENE_REFRESH_MS;
      timer.current = setTimeout(() => void refresh(), delay);
    };

    const refresh = async () => {
      if (disposed.current || inFlight.current || document.visibilityState !== "visible") return;
      inFlight.current = true;
      try {
        const latest = await getLatestAustriaLivingScene();
        if (disposed.current) return;
        if (latest.scene?.root_work_item_id !== rootWorkItemId) {
          hasCompletedAutomaticRead.current = true;
          schedule();
          return;
        }

        const fingerprint = canonicalSceneFingerprint(latest);
        const unchanged = lastCanonicalFingerprint.current === fingerprint;
        lastCanonicalFingerprint.current = fingerprint;
        hasCompletedAutomaticRead.current = true;
        if (!unchanged) onSceneRef.current(latest);
      } catch (error) {
        hasCompletedAutomaticRead.current = true;
        if (!disposed.current) onErrorRef.current?.(error);
      } finally {
        inFlight.current = false;
        if (!disposed.current) schedule();
      }
    };

    const handleVisibility = () => {
      clearTimer();
      if (document.visibilityState === "visible") void refresh();
    };

    document.addEventListener("visibilitychange", handleVisibility);
    schedule();

    return () => {
      disposed.current = true;
      clearTimer();
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [enabled, rootWorkItemId]);
}
