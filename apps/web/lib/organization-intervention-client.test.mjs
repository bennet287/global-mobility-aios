import assert from "node:assert/strict";
import test from "node:test";

function recordingFetch() {
  const calls = [];
  return {
    calls,
    fetch: async (input, init) => {
      calls.push({ input, init, headers: new Headers(init.headers) });
      return new Response(JSON.stringify({
        id: "request-1",
        request_key: "cockpit-intervention:organization_blocker:blocker-1:v1",
        request_type: "review",
        title: "Owner follow-up: Evidence blocker",
        instructions: "Review the evidence gap and report the next governed action.",
        status: "required",
        priority: "high",
        required_role: "reviewer",
        assigned_human_id: null,
        requested_by_type: "human",
        requested_by_id: "frontend-operator",
        work_item_id: "work-1",
        decision_id: null,
        blocker_id: "blocker-1",
        contribution_id: null,
        due_at: null,
        outcome: null,
        completed_at: null,
        completed_by_human_id: null,
        created_at: "2026-08-16T20:00:00Z",
        updated_at: "2026-08-16T20:00:00Z",
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  };
}

test("Cockpit governed intervention uses the existing human-action request command with auth headers", async () => {
  const originalFetch = globalThis.fetch;
  const recorder = recordingFetch();
  globalThis.fetch = recorder.fetch;

  process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8003";
  process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE = "true";
  process.env.NEXT_PUBLIC_GMAI_ROLE = "admin";
  process.env.NEXT_PUBLIC_GMAI_USER = "frontend-operator";
  process.env.NODE_ENV = "production";

  const payload = {
    request_key: "cockpit-intervention:organization_blocker:blocker-1:v1",
    request_type: "review",
    title: "Owner follow-up: Evidence blocker",
    instructions: "Review the evidence gap and report the next governed action.",
    required_role: "reviewer",
    priority: "high",
    work_item_id: "work-1",
    blocker_id: "blocker-1",
    source_object_type: "organization_blocker",
    source_object_id: "blocker-1",
    source_object_version: "v1",
  };

  try {
    const api = await import(`./api.ts?organization-intervention=${Date.now()}`);
    const created = await api.createOrganizationHumanActionRequest(payload);
    assert.equal(created.status, "required");
  } finally {
    globalThis.fetch = originalFetch;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE;
    delete process.env.NEXT_PUBLIC_GMAI_ROLE;
    delete process.env.NEXT_PUBLIC_GMAI_USER;
    delete process.env.NODE_ENV;
  }

  assert.equal(recorder.calls.length, 1);
  const [call] = recorder.calls;
  assert.equal(call.input, "http://127.0.0.1:8003/api/v1/organization/human-action-requests");
  assert.equal(call.init.method, "POST");
  assert.deepEqual(JSON.parse(call.init.body), payload);
  assert.equal(call.headers.get("x-gmai-role"), "admin");
  assert.equal(call.headers.get("x-gmai-user"), "frontend-operator");
  assert.equal(call.init.credentials, "include");
});
