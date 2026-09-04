"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  type LivingOrganizationScene,
  getLatestAustriaLivingScene,
} from "../lib/live-organization";
import {
  type V2EmployeeInspectorModel,
  type V2MissionRoomModel,
  buildV2EmployeeInspectorModel,
  buildV2MissionRoomModel,
} from "../lib/v2/mission-room-inspector";

export function useV2MissionRoomInspector() {
  const [scene, setScene] = useState<LivingOrganizationScene | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const latest = await getLatestAustriaLivingScene();
      setScene(latest.established ? latest.scene : null);
    } catch (caught) {
      setScene(null);
      setError(caught instanceof Error ? caught.message : "Living Organization scene could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const employees = useMemo(() => scene?.deterministic.employees || [], [scene]);

  const selectors = useMemo(() => {
    return {
      missionRoomFor(missionKey: string | null): V2MissionRoomModel | null {
        if (!scene || !missionKey) return null;
        return buildV2MissionRoomModel(scene, missionKey);
      },
      employeeInspectorFor(positionKey: string | null): V2EmployeeInspectorModel | null {
        if (!scene || !positionKey) return null;
        return buildV2EmployeeInspectorModel(scene, positionKey);
      },
    };
  }, [scene]);

  return {
    sceneEstablished: scene !== null,
    employees,
    loading,
    error,
    refresh,
    missionRoomFor: selectors.missionRoomFor,
    employeeInspectorFor: selectors.employeeInspectorFor,
  };
}
