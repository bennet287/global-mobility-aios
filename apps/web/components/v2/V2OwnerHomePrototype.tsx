"use client";

import { useMemo } from "react";

import { useBackendStatus } from "../../hooks/useBackendStatus";
import { useV2OwnerOrganization } from "../../hooks/useV2OwnerOrganization";
import type { V2AttentionItem } from "../../lib/v2/owner-organization";
import {
  useV2SearchItems,
  type V2SearchItem,
} from "./V2NavigationContext";
import { V2OwnerSituationRoom } from "./V2OwnerSituationRoom";
import { V2Shell } from "./V2Shell";

// Q2 continuity: attention items the Owner Home already loaded remain selectable
// records in the command palette. Q3 changes presentation only and adds no
// search-specific request path.
function attentionSearchItem(item: V2AttentionItem): V2SearchItem {
  return {
    id: item.id,
    label: item.title,
    description: item.detail,
    href: item.href,
    icon:
      item.kind === "decision"
        ? "decisions"
        : item.kind === "human_action"
          ? "organization"
          : item.kind === "blocker"
            ? "missions"
            : "intelligence",
    kind: item.kind === "decision" ? "Decision" : "Event",
  };
}

export function V2OwnerHomePrototype() {
  const { health } = useBackendStatus();
  const { data, loading, error, refresh } = useV2OwnerOrganization();
  const backendOnline = health?.status === "ok";

  const attentionSearchItems = useMemo(
    () => (data?.attention || []).map(attentionSearchItem),
    [data?.attention],
  );
  useV2SearchItems(attentionSearchItems);

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
