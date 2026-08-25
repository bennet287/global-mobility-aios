import { CLIENT_API_CONFIG } from "./client-api-config.ts";
import { createApiFetch } from "./request-client.mjs";

export type OrganizationPositionPresence = {
  contract_version: string;
  position_key: string;
  work_item_id: string;
  presence_state: "executing" | "not_executing" | "not_established" | string;
  presence_basis: string;
  observed_at: string | null;
  execution_attempt_id: string | null;
  execution_attempt_status: string | null;
  heartbeat_state: "not_established" | string;
  heartbeat_observed_at: string | null;
  heartbeat_fresh_until: string | null;
  authority_effect: boolean;
};

export type AustriaOrganizationPresenceSnapshot = {
  generated_at: string;
  root_work_item_id: string;
  positions: OrganizationPositionPresence[];
  heartbeat_capability_state: string;
};

export type AustriaOrganizationPresenceLatest = {
  established: boolean;
  snapshot: AustriaOrganizationPresenceSnapshot | null;
};

export class OrganizationPresenceRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "OrganizationPresenceRequestError";
    this.status = status;
  }
}

const apiFetch = createApiFetch(CLIENT_API_CONFIG);

export async function getLatestAustriaOrganizationPresence(): Promise<AustriaOrganizationPresenceLatest> {
  const response = await apiFetch(
    "/api/v1/organization/transparency/presence/austria/latest",
  );
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string" && body.detail.trim()) detail = body.detail;
    } catch {
      // Preserve the status fallback when a proxy returns non-JSON.
    }
    throw new OrganizationPresenceRequestError(response.status, detail);
  }
  return response.json() as Promise<AustriaOrganizationPresenceLatest>;
}
