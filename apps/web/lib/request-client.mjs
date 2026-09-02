function isLoopbackApiBase(apiBase) {
  try {
    const hostname = new URL(apiBase).hostname.toLowerCase();
    return hostname === "127.0.0.1" || hostname === "localhost" || hostname === "::1";
  } catch {
    return false;
  }
}

function localHeaderAuthEnabled(config) {
  const configured = String(config.authAllowHeaderRole ?? "").trim().toLowerCase();
  if (config.nodeEnv === "production" && !isLoopbackApiBase(config.apiBase)) return false;
  if (configured === "false") return false;
  if (configured === "true") return true;
  return config.nodeEnv === "development" || isLoopbackApiBase(config.apiBase);
}

export function buildApiRequestInit(config, init = {}) {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (localHeaderAuthEnabled(config)) {
    headers.set("x-gmai-role", String(config.role || "admin").trim());
    headers.set("x-gmai-user", String(config.user || "frontend-operator").trim());
  } else {
    headers.delete("x-gmai-role");
    headers.delete("x-gmai-user");
  }
  return {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  };
}

export function createApiFetch(config, fetchImplementation) {
  const apiBase = config.apiBase.replace(/\/$/, "");
  return (path, init) => {
    const finalFetch = fetchImplementation || globalThis.fetch;
    if (typeof finalFetch !== "function") {
      throw new TypeError("A fetch implementation is required.");
    }
    return finalFetch(`${apiBase}${path}`, buildApiRequestInit(config, init));
  };
}
