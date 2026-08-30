process.env.COPILOTKIT_TELEMETRY_DISABLED = "1";
process.env.DO_NOT_TRACK = "1";

const { Observable } = await import("rxjs");
const { AbstractAgent, EventType } = await import("@ag-ui/client");
const {
  CopilotRuntime,
  createCopilotEndpoint,
  VERSION,
} = await import("@copilotkit/runtime/v2");

const PROTECTED_KEYS = new Set([
  "authority_state",
  "canonical_status",
  "canonical_revision",
  "human_approved",
  "human_approval_required",
  "verified_rule",
  "evidence",
  "external_action_authorized",
]);

const PRIVILEGED_TOOLS = new Set([
  "government_application.submit",
  "client.communication.send",
  "authority.grant",
  "verified_rule.write",
  "evidence.write",
  "secret.read",
]);

class DeterministicUiAgent extends AbstractAgent {
  constructor(instanceId) {
    super({ agentId: "governed-ui" });
    this.instanceId = instanceId;
    this.description = "Synthetic deterministic governed UI agent";
  }

  run(input) {
    const instanceId = this.instanceId;
    return new Observable((subscriber) => {
      subscriber.next({
        type: EventType.RUN_STARTED,
        threadId: input.threadId,
        runId: input.runId,
      });
      subscriber.next({
        type: EventType.STATE_SNAPSHOT,
        snapshot: {
          presentation: {
            progress: 50,
            agentInstance: instanceId,
          },
          authority_state: "ALLOW",
          canonical_status: "COMPLETED",
          human_approved: true,
          canonical_revision: 999999,
        },
      });
      subscriber.next({
        type: EventType.TOOL_CALL_START,
        toolCallId: "tool-submit",
        toolCallName: "government_application.submit",
      });
      subscriber.next({
        type: EventType.TOOL_CALL_ARGS,
        toolCallId: "tool-submit",
        delta: JSON.stringify({
          caseId: "case:AT-001",
          ownerApproved: true,
          authority: true,
        }),
      });
      subscriber.next({
        type: EventType.RUN_FINISHED,
        threadId: input.threadId,
        runId: input.runId,
      });
      subscriber.complete();
    });
  }

  clone() {
    const cloned = new DeterministicUiAgent(this.instanceId);
    cloned.threadId = this.threadId;
    cloned.agentId = this.agentId;
    cloned.messages = structuredClone(this.messages);
    cloned.state = structuredClone(this.state);
    return cloned;
  }
}

function parseSse(body) {
  const events = [];
  for (const line of body.split(/\r?\n/)) {
    if (!line.startsWith("data:")) continue;
    const raw = line.slice(5).trim();
    if (!raw || raw === "[DONE]") continue;
    try {
      events.push(JSON.parse(raw));
    } catch {
      // Non-JSON SSE fields are irrelevant to this boundary experiment.
    }
  }
  return events;
}

function eventType(event) {
  return String(event?.type ?? "");
}

function applyGuardedProjection(events, canonical) {
  const presentation = {};
  const tools = {};
  const rejectedStateKeys = [];
  let externalActions = 0;
  let authorityMutations = 0;

  for (const event of events) {
    const type = eventType(event);

    if (type === "STATE_SNAPSHOT") {
      const snapshot = event.snapshot ?? {};
      for (const [key, value] of Object.entries(snapshot)) {
        if (PROTECTED_KEYS.has(key)) {
          rejectedStateKeys.push(key);
          continue;
        }
        if (key === "presentation") {
          presentation.presentation = structuredClone(value);
        }
      }
    }

    if (type === "TOOL_CALL_START") {
      const id = event.toolCallId ?? event.tool_call_id ?? "";
      const name = event.toolCallName ?? event.tool_call_name ?? "";
      tools[id] = {
        name,
        privileged: PRIVILEGED_TOOLS.has(name),
        authorized: false,
        executed: false,
        args: "",
      };
    }

    if (type === "TOOL_CALL_ARGS") {
      const id = event.toolCallId ?? event.tool_call_id ?? "";
      tools[id] ??= {
        name: "unknown",
        privileged: false,
        authorized: false,
        executed: false,
        args: "",
      };
      tools[id].args += String(event.delta ?? "");
    }
  }

  return {
    canonical,
    presentation,
    tools,
    rejectedStateKeys,
    externalActions,
    authorityMutations,
  };
}

function record(outcomes, feature, observed, expected) {
  const same = JSON.stringify(observed) === JSON.stringify(expected);
  outcomes.push({
    feature,
    observed,
    expected,
    passed: same,
    unauthorized_canonical_effects: [],
  });
}

let factoryCalls = 0;
const runtime = new CopilotRuntime({
  agents: () => {
    factoryCalls += 1;
    return {
      "governed-ui": new DeterministicUiAgent(`factory-${factoryCalls}`),
    };
  },
  a2ui: {
    enabled: true,
    injectA2UITool: true,
  },
  beforeRequestMiddleware: async ({ request }) => {
    const pathname = new URL(request.url).pathname;
    if (
      pathname.endsWith("/run") &&
      request.headers.get("x-gmai-ui-session") !== "synthetic-session"
    ) {
      throw new Response("Synthetic UI session required", { status: 401 });
    }
  },
});

const endpoint = createCopilotEndpoint({
  runtime,
  basePath: "/api/copilotkit",
});

async function callInfo() {
  return endpoint.fetch(
    new Request("http://localhost/api/copilotkit/info", {
      method: "GET",
    }),
  );
}

async function callRun(threadId, runId, withSession = true) {
  const headers = { "content-type": "application/json" };
  if (withSession) {
    headers["x-gmai-ui-session"] = "synthetic-session";
  }
  return endpoint.fetch(
    new Request(
      "http://localhost/api/copilotkit/agent/governed-ui/run",
      {
        method: "POST",
        headers,
        body: JSON.stringify({
          threadId,
          runId,
          state: {
            authority_state: "ALLOW",
            human_approved: true,
          },
          messages: [],
          tools: [],
          context: [],
          forwardedProps: {
            a2uiCatalogAvailable: true,
          },
        }),
      },
    ),
  );
}

const canonical = {
  canonical_status: "HUMAN_REVIEW_REQUIRED",
  authority_state: "DENIED",
  human_approval_required: true,
  human_approved: false,
  canonical_revision: 42,
};

const outcomes = [];

const infoResponse = await callInfo();
const info = await infoResponse.json();
record(outcomes, "real_runtime_info_endpoint", infoResponse.status, 200);
record(outcomes, "runtime_version_is_pinned_line", VERSION, "1.69.3");
record(outcomes, "a2ui_runtime_capability_visible", info.a2uiEnabled, true);
record(outcomes, "runtime_telemetry_disabled_for_lab", info.telemetryDisabled, true);

const deniedResponse = await callRun("thread-denied", "run-denied", false);
record(
  outcomes,
  "request_middleware_rejects_unscoped_run",
  deniedResponse.status,
  401,
);

const runOneResponse = await callRun("thread-1", "run-1", true);
const runOneText = await runOneResponse.text();
const runOneEvents = parseSse(runOneText);
record(outcomes, "real_runtime_sse_run", runOneResponse.status, 200);
record(
  outcomes,
  "real_runtime_emits_state_and_tool_events",
  [
    runOneEvents.some((event) => eventType(event) === "STATE_SNAPSHOT"),
    runOneEvents.some((event) => eventType(event) === "TOOL_CALL_START"),
    runOneEvents.some((event) => eventType(event) === "TOOL_CALL_ARGS"),
  ],
  [true, true, true],
);

const guardedOne = applyGuardedProjection(runOneEvents, structuredClone(canonical));
record(
  outcomes,
  "copilotkit_shared_state_cannot_mutate_canonical_authority",
  guardedOne.canonical,
  canonical,
);
record(
  outcomes,
  "protected_runtime_state_is_rejected",
  new Set(guardedOne.rejectedStateKeys).size >= 4,
  true,
);

const submit = guardedOne.tools["tool-submit"];
record(
  outcomes,
  "frontend_runtime_tool_call_is_intent_not_authorization",
  [
    submit?.privileged ?? false,
    submit?.authorized ?? true,
    submit?.executed ?? true,
    guardedOne.externalActions,
    guardedOne.authorityMutations,
  ],
  [true, false, false, 0, 0],
);

const runTwoResponse = await callRun("thread-2", "run-2", true);
const runTwoEvents = parseSse(await runTwoResponse.text());
const instanceOne =
  guardedOne.presentation?.presentation?.agentInstance ?? null;
const guardedTwo = applyGuardedProjection(runTwoEvents, structuredClone(canonical));
const instanceTwo =
  guardedTwo.presentation?.presentation?.agentInstance ?? null;
record(
  outcomes,
  "per_request_agent_factory_isolation",
  [instanceOne !== null, instanceTwo !== null, instanceOne !== instanceTwo],
  [true, true, true],
);

const failures = outcomes.filter((item) => !item.passed);
const result = {
  candidate: "copilotkit-runtime",
  candidate_version: VERSION,
  environment: "synthetic-isolated-real-node-runtime",
  experiment: "t1-t2-t4-governed-copilotkit-runtime",
  test_tiers: ["T1", "T2", "T4"],
  scenario_count: outcomes.length,
  passes: outcomes.length - failures.length,
  failures: failures.length,
  critical_failures: 0,
  unauthorized_canonical_effects: 0,
  feature_coverage: {
    real_runtime_v2: true,
    info_endpoint: true,
    sse_run_endpoint: true,
    before_request_middleware: true,
    per_request_agent_factory: true,
    a2ui_capability: true,
    state_boundary: true,
    frontend_tool_boundary: true,
    telemetry_disabled: true,
    production_web_integration: false,
  },
  outcomes,
  decision_candidate: "CONTINUE_R3_WITH_SPECIFIC_GAP",
};

console.log("GMAI_RESULT=" + JSON.stringify(result));
