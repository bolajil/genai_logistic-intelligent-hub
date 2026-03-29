const BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9001";

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("glih_access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function refreshTokens(): Promise<boolean> {
  const refresh = typeof window !== "undefined" ? localStorage.getItem("glih_refresh_token") : null;
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem("glih_access_token", data.access_token);
    localStorage.setItem("glih_refresh_token", data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

function clearSessionAndRedirect() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("glih_access_token");
    localStorage.removeItem("glih_refresh_token");
    window.location.href = "/login";
  }
}

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options?.headers as Record<string, string> ?? {}) },
  });
  if (res.status === 401) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      const retry = await fetch(`${BASE}${path}`, {
        ...options,
        headers: { ...authHeaders(), ...(options?.headers as Record<string, string> ?? {}) },
      });
      if (!retry.ok) {
        const err = await retry.text();
        throw new Error(`${retry.status}: ${err}`);
      }
      return retry.json();
    }
    clearSessionAndRedirect();
    throw new Error("Session expired — please log in again");
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status}: ${err}`);
  }
  return res.json();
}

/** Raw fetch wrapper with the same 401→refresh→retry logic. Use in pages that need the Response object. */
export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const makeHeaders = () => ({ ...authHeaders(), ...(options?.headers as Record<string, string> ?? {}) });
  const res = await fetch(`${BASE}${path}`, { ...options, headers: makeHeaders() });
  if (res.status === 401) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      return fetch(`${BASE}${path}`, { ...options, headers: makeHeaders() });
    }
    clearSessionAndRedirect();
  }
  return res;
}

export { BASE, authHeaders };

// Health
export const getHealth = () => req<{ status: string }>("/health");
export const getHealthDetailed = () => req<any>("/health/detailed");

// RAG query
export interface QueryResult {
  results: Array<{
    text: string;
    metadata: Record<string, any>;
    score: number;
    collection: string;
  }>;
  query: string;
  collection: string;
  total: number;
}

export const ragQuery = async (query: string, collection = "lineage-sops", topK = 5): Promise<any> => {
  const params = new URLSearchParams({ q: query, collection, k: String(topK), style: "bulleted" });
  const res = await fetch(`${BASE}/query?${params}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
};

// Agent endpoints (wired to real LLM)
export interface AgentRunResponse {
  run_id: string;
  agent_name: string;
  status: string;
  result: any;
  duration_ms: number;
}

export const runAnomalyAgent = (payload: any) =>
  req<AgentRunResponse>("/agents/anomaly", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const runRouteAgent = (payload: any) =>
  req<AgentRunResponse>("/agents/route", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const runNotifyAgent = (payload: any) =>
  req<AgentRunResponse>("/agents/notify", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const runOpsSummaryAgent = (payload: any) =>
  req<AgentRunResponse>("/agents/ops-summary", {
    method: "POST",
    body: JSON.stringify(payload),
  });

// Ingest document
export const ingestTexts = (texts: string[], collection?: string, metadatas?: any[]) =>
  req<any>("/ingest", {
    method: "POST",
    body: JSON.stringify({ texts, collection, metadatas }),
  });

// Config / LLM
export const getLLMCurrent = () => req<any>("/llm/current");
export const getBackendConfig = () => req<any>("/config");
