"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { getLatestAustriaLivingScene, LiveOrganizationRequestError, type LivingOrganizationScene } from "../lib/live-organization";
import { validateMissionScene } from "../lib/v2/missions-workspace";

type MissionRead = { scene: LivingOrganizationScene | null; received: boolean; loading: boolean; error: string | null; loadedAt: string | null };
export function useV2MissionsWorkspace() {
  const [read, setRead] = useState<MissionRead>({ scene: null, received: false, loading: true, error: null, loadedAt: null });
  const requestVersion = useRef(0);
  const refresh = useCallback(async () => {
    const version = ++requestVersion.current;
    setRead((previous) => ({ ...previous, loading: true, error: null }));
    try {
      const latest = await getLatestAustriaLivingScene();
      const scene = validateMissionScene(latest);
      if (version === requestVersion.current) setRead({ scene, received: true, loading: false, error: null, loadedAt: new Date().toISOString() });
    } catch (error) {
      if (version !== requestVersion.current) return;
      const denied = error instanceof LiveOrganizationRequestError && [401, 403].includes(error.status);
      setRead((previous) => ({ ...previous, ...(denied ? { scene: null, received: false, loadedAt: null } : {}), loading: false, error: denied ? "Access to Mission records was denied." : error instanceof Error ? error.message : "The Mission source could not be reached." }));
    }
  }, []);
  useEffect(() => { void refresh(); return () => { requestVersion.current += 1; }; }, [refresh]);
  return { ...read, refresh };
}
