import type { ApiRequestConfiguration } from "./request-client.mjs";

// Next.js only exposes NEXT_PUBLIC_* values to client bundles when referenced
// statically. Keep every public environment read in this compiled TypeScript module;
// the generic request builder receives resolved values and never discovers env vars.
export const CLIENT_API_CONFIG: ApiRequestConfiguration = Object.freeze({
  apiBase: process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000",
  authAllowHeaderRole: process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE,
  role: process.env.NEXT_PUBLIC_GMAI_ROLE,
  user: process.env.NEXT_PUBLIC_GMAI_USER,
  nodeEnv: process.env.NODE_ENV,
  clientConfigVersion: "v13_10_2_15_f01_browser_runtime",
});
