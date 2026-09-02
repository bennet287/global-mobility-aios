"use client";

import { useEffect, useState } from "react";
import { getHealthStatus, HealthStatus } from "../lib/api";

export function useBackendStatus() {
  const [health, setHealth] = useState<{ data: HealthStatus | null; error: string | null }>({ data: null, error: null });

  const check = async () => {
    const result = await getHealthStatus();
    setHealth(result);
  };

  useEffect(() => {
    void check();
    const interval = setInterval(() => void check(), 15000);
    return () => clearInterval(interval);
  }, []);

  return {
    health: health.data,
    error: health.error,
  };
}
