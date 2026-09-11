"use client";

import { useEffect, useRef } from "react";

import {
  getLatestAustriaLivingScene,
  type LivingOrganizationSceneLatest,
} from "../lib/live-organization";

export const LIVING_HQ_SCENE_REFRESH_MS = 5000;

type LivingOrganizationSceneRefreshOptions = {
  enabled: boolean;
  rootWorkItemId: string | null;
  onScene: (latest: LivingOrganizationSceneLatest) => void;
  onError?: (error: unknown) => void;
};

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

  useEffect(() => {
    onSceneRef.current = onScene;
  }, [onScene]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    if (!enabled || !rootWorkItemId) return;

    disposed.current = false;

    const clearTimer = () => {
      if (timer.current) {
        clearTimeout(timer.current);
        timer.current = null;
      }
    };

    const schedule = () => {
      clearTimer();
      if (disposed.current || document.visibilityState !== "visible") return;
      timer.current = setTimeout(() => void refresh(), LIVING_HQ_SCENE_REFRESH_MS);
    };

    const refresh = async () => {
      if (disposed.current || inFlight.current || document.visibilityState !== "visible") return;
      inFlight.current = true;
      try {
        const latest = await getLatestAustriaLivingScene();
        if (disposed.current) return;
        if (latest.scene?.root_work_item_id !== rootWorkItemId) {
          schedule();
          return;
        }
        onSceneRef.current(latest);
      } catch (error) {
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
