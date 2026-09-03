"use client";

import { useCallback, useEffect, useState } from "react";

import {
  type V2OwnerOrganizationData,
  loadV2OwnerOrganization,
} from "../lib/v2/owner-organization";

export function useV2OwnerOrganization() {
  const [data, setData] = useState<V2OwnerOrganizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await loadV2OwnerOrganization());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "AIOS V2 organization data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    data,
    loading,
    error,
    refresh,
  };
}
