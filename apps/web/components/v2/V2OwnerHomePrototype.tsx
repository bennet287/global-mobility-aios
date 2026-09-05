"use client";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import { V2OwnerSituationRoom } from "./V2OwnerSituationRoom";
import { V2Shell } from "./V2Shell";

export function V2OwnerHomePrototype() {
  const { health } = useBackendStatus();
  const { data, loading, error, refresh } = useV2OwnerOrganization();
  const backendOnline = health?.status === "ok";

  return (
    <V2Shell activeItem="Home" backendOnline={backendOnline}>
      <V2OwnerSituationRoom
        data={data}
        error={error}
        loading={loading}
        onRetry={() => void refresh()}
      />
    </V2Shell>
  );
}
