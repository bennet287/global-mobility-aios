import assert from "node:assert/strict";
import test from "node:test";

import { createApiFetch } from "./request-client.mjs";

function recordingFetch() {
  const calls = [];
  return {
    calls,
    fetch: async (input, init) => {
      calls.push({ input, init, headers: new Headers(init.headers) });
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  };
}

test("exported Eligibility GET and POST functions use the canonical final fetch", async () => {
  const originalFetch = globalThis.fetch;
  const originalEnvironment = {
    apiBase: process.env.NEXT_PUBLIC_API_BASE_URL,
    enabled: process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE,
    role: process.env.NEXT_PUBLIC_GMAI_ROLE,
    user: process.env.NEXT_PUBLIC_GMAI_USER,
    nodeEnv: process.env.NODE_ENV,
  };
  const recorder = recordingFetch();
  globalThis.fetch = recorder.fetch;
  process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8002";
  process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE = "true";
  process.env.NEXT_PUBLIC_GMAI_ROLE = "admin";
  process.env.NEXT_PUBLIC_GMAI_USER = "frontend-operator";
  process.env.NODE_ENV = "production";
  try {
    const api = await import(`./api.ts?eligibility-auth=${Date.now()}`);
    const clientConfig = await import(`./client-api-config.ts?eligibility-auth=${Date.now()}`);
    assert.deepEqual({
      apiBase: clientConfig.CLIENT_API_CONFIG.apiBase,
      authAllowHeaderRole: clientConfig.CLIENT_API_CONFIG.authAllowHeaderRole,
      role: clientConfig.CLIENT_API_CONFIG.role,
      user: clientConfig.CLIENT_API_CONFIG.user,
    }, {
      apiBase: "http://127.0.0.1:8002",
      authAllowHeaderRole: "true",
      role: "admin",
      user: "frontend-operator",
    });
    await api.getLatestEligibilityAssessment("lead-id");
    await api.evaluateEligibility("lead-id");
  } finally {
    globalThis.fetch = originalFetch;
    for (const [key, value] of Object.entries({
      NEXT_PUBLIC_API_BASE_URL: originalEnvironment.apiBase,
      NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE: originalEnvironment.enabled,
      NEXT_PUBLIC_GMAI_ROLE: originalEnvironment.role,
      NEXT_PUBLIC_GMAI_USER: originalEnvironment.user,
      NODE_ENV: originalEnvironment.nodeEnv,
    })) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }

  assert.deepEqual(recorder.calls.map((call) => call.input), [
    "http://127.0.0.1:8002/api/v1/eligibility/lead-id/latest",
    "http://127.0.0.1:8002/api/v1/eligibility/evaluate",
  ]);
  assert.equal(recorder.calls[0].init.method, undefined);
  assert.equal(recorder.calls[1].init.method, "POST");
  for (const call of recorder.calls) {
    assert.equal(call.headers.get("x-gmai-role"), "admin");
    assert.equal(call.headers.get("x-gmai-user"), "frontend-operator");
    assert.equal(call.init.credentials, "include");
  }
});

test("Eligibility GET and POST reach native fetch with configured local auth", async () => {
  const recorder = recordingFetch();
  const apiFetch = createApiFetch({
    apiBase: "http://127.0.0.1:8002",
    authAllowHeaderRole: "true",
    role: "admin",
    user: "frontend-operator",
    nodeEnv: "production",
  }, recorder.fetch);

  await apiFetch("/api/v1/eligibility/lead-id/latest");
  await apiFetch("/api/v1/eligibility/evaluate", {
    method: "POST",
    headers: { "X-Request-Scope": "eligibility-preview" },
    body: JSON.stringify({ lead_id: "lead-id" }),
  });

  assert.equal(recorder.calls.length, 2);
  for (const call of recorder.calls) {
    assert.equal(call.headers.get("x-gmai-role"), "admin");
    assert.equal(call.headers.get("x-gmai-user"), "frontend-operator");
    assert.equal(call.init.credentials, "include");
    assert.equal(call.init.cache, "no-store");
  }
  assert.equal(recorder.calls[1].headers.get("x-request-scope"), "eligibility-preview");
  assert.equal(recorder.calls[1].headers.get("content-type"), "application/json");
});

test("explicit false removes local header-role auth even on loopback", async () => {
  const recorder = recordingFetch();
  const apiFetch = createApiFetch({
    apiBase: "http://localhost:8002",
    authAllowHeaderRole: "false",
    role: "admin",
    user: "frontend-operator",
    nodeEnv: "development",
  }, recorder.fetch);

  await apiFetch("/api/v1/eligibility/lead-id/latest", {
    headers: { "x-gmai-role": "must-be-removed", "x-gmai-user": "must-be-removed" },
  });

  assert.equal(recorder.calls[0].headers.has("x-gmai-role"), false);
  assert.equal(recorder.calls[0].headers.has("x-gmai-user"), false);
});

test("non-loopback production is fail-closed even when public header auth is enabled", async () => {
  const recorder = recordingFetch();
  const apiFetch = createApiFetch({
    apiBase: "https://api.example.test",
    authAllowHeaderRole: "true",
    role: "admin",
    user: "frontend-operator",
    nodeEnv: "production",
  }, recorder.fetch);

  await apiFetch("/api/v1/eligibility/lead-id/latest");

  assert.equal(recorder.calls[0].headers.has("x-gmai-role"), false);
  assert.equal(recorder.calls[0].headers.has("x-gmai-user"), false);
});
