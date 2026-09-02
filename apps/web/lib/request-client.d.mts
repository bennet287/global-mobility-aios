export type ApiRequestConfiguration = {
  apiBase: string;
  authAllowHeaderRole?: string;
  role?: string;
  user?: string;
  nodeEnv?: string;
  clientConfigVersion?: string;
};

export function buildApiRequestInit(
  config: ApiRequestConfiguration,
  init?: RequestInit,
): RequestInit;

export function createApiFetch(
  config: ApiRequestConfiguration,
  fetchImplementation?: typeof fetch,
): (path: string, init?: RequestInit) => Promise<Response>;
