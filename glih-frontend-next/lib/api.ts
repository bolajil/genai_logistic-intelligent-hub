const BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:9001";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status}: ${err}`);
  }
  return res.json();
}

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
  const res = await fetch(`${BASE}/query?${params}`);
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
