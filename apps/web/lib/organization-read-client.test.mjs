import assert from "node:assert/strict";
import test from "node:test";

import { createApiFetch } from "./request-client.mjs";

function recordingFetch() {
  const calls = [];
  return {
    calls,
    fetch: async (input, init) => {
      calls.push({ input, init, headers: new Headers(init.headers) });
      return new Response(JSON.stringify({ ok: true, data: [], page: 1, page_size: 50, total: 0, total_pages: 1 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  };
}

function setupEnvironment() {
  return {
    apiBase: "http://127.0.0.1:8003",
    authAllowHeaderRole: "true",
    role: "admin",
    user: "frontend-operator",
    nodeEnv: "production",
  };
}

test("Organization read list functions reach the expected endpoints and params", async () => {
  const originalFetch = globalThis.fetch;
  const recorder = recordingFetch();
  globalThis.fetch = recorder.fetch;

  const env = setupEnvironment();
  process.env.NEXT_PUBLIC_API_BASE_URL = env.apiBase;
  process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE = env.authAllowHeaderRole;
  process.env.NEXT_PUBLIC_GMAI_ROLE = env.role;
  process.env.NEXT_PUBLIC_GMAI_USER = env.user;
  process.env.NODE_ENV = env.nodeEnv;

  try {
    const api = await import(`./api.ts?organization-read=${Date.now()}`);
    await api.listOrganizationBlockers({ status: "open", page_size: 50 });
    await api.listOrganizationWorkItemDependencies({ status: "active", page_size: 50 });
    await api.listOrganizationWorkItems({ status_filter: "running", page_size: 100 });
  } finally {
    globalThis.fetch = originalFetch;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE;
    delete process.env.NEXT_PUBLIC_GMAI_ROLE;
    delete process.env.NEXT_PUBLIC_GMAI_USER;
    delete process.env.NODE_ENV;
  }

  const inputs = recorder.calls.map((call) => call.input);
  assert.deepEqual(inputs, [
    "http://127.0.0.1:8003/api/v1/organization/blockers?page=1&page_size=50&status=open",
    "http://127.0.0.1:8003/api/v1/organization/work-item-dependencies?page=1&page_size=50&status=active",
    "http://127.0.0.1:8003/api/v1/organization/work-items/records?page=1&page_size=100&status=running",
  ]);

  for (const call of recorder.calls) {
    assert.equal(call.init.method, undefined);
    assert.equal(call.headers.get("x-gmai-role"), "admin");
    assert.equal(call.headers.get("x-gmai-user"), "frontend-operator");
    assert.equal(call.init.credentials, "include");
  }
});

test("Organization contribution list reaches the expected endpoint with department filter", async () => {
  const originalFetch = globalThis.fetch;
  const recorder = recordingFetch();
  globalThis.fetch = recorder.fetch;

  process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8003";
  process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE = "true";
  process.env.NEXT_PUBLIC_GMAI_ROLE = "admin";
  process.env.NEXT_PUBLIC_GMAI_USER = "frontend-operator";
  process.env.NODE_ENV = "production";

  try {
    const api = await import(`./api.ts?organization-contribution=${Date.now()}`);
    await api.listOrganizationContributions({ department: "Global Mobility Operations", page_size: 50 });
  } finally {
    globalThis.fetch = originalFetch;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE;
    delete process.env.NEXT_PUBLIC_GMAI_ROLE;
    delete process.env.NEXT_PUBLIC_GMAI_USER;
    delete process.env.NODE_ENV;
  }

  assert.deepEqual(recorder.calls.map((call) => call.input), [
    "http://127.0.0.1:8003/api/v1/organization/contributions?page=1&page_size=50&department=Global+Mobility+Operations",
  ]);

  for (const call of recorder.calls) {
    assert.equal(call.init.method, undefined);
    assert.equal(call.headers.get("x-gmai-role"), "admin");
    assert.equal(call.headers.get("x-gmai-user"), "frontend-operator");
    assert.equal(call.init.credentials, "include");
  }
});
