import type {
  Execution,
  ExecutionLog,
  HealthIntegrations,
  OutreachDraft,
  Prospect,
  ProspectCreateInput,
  ResearchSource,
  Signal,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore - use statusText
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string; database: boolean }>("/health"),
  healthIntegrations: () => request<HealthIntegrations>("/health/integrations"),

  listProspects: (limit = 100) => request<Prospect[]>(`/api/v1/prospects?limit=${limit}`),
  getProspect: (id: string) => request<Prospect>(`/api/v1/prospects/${id}`),
  createProspect: (payload: ProspectCreateInput) =>
    request<Prospect>("/api/v1/prospects", { method: "POST", body: JSON.stringify(payload) }),

  runResearch: (prospectId: string, idempotencyKey?: string) =>
    request<{ execution_id: string; status: string; message: string }>("/api/v1/research/run", {
      method: "POST",
      body: JSON.stringify({ prospect_id: prospectId, idempotency_key: idempotencyKey }),
    }),
  getExecution: (executionId: string) => request<Execution>(`/api/v1/research/${executionId}`),
  getSources: (executionId: string) => request<ResearchSource[]>(`/api/v1/research/${executionId}/sources`),
  getSignals: (executionId: string) => request<Signal[]>(`/api/v1/research/${executionId}/signals`),

  listExecutions: (limit = 100) => request<Execution[]>(`/api/v1/executions?limit=${limit}`),
  getExecutionLogs: (executionId: string) =>
    request<ExecutionLog[]>(`/api/v1/executions/${executionId}/logs`),

  listAllDrafts: (limit = 100) => request<OutreachDraft[]>(`/api/v1/outreach?limit=${limit}`),
  getExecutionDrafts: (executionId: string) =>
    request<OutreachDraft[]>(`/api/v1/outreach/${executionId}`).catch((err) => {
      if (err instanceof ApiError && err.status === 404) return [];
      throw err;
    }),
  editDraft: (draftId: string, payload: { subject?: string | null; body: string; reviewer_notes?: string | null }) =>
    request<OutreachDraft>(`/api/v1/outreach/${draftId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  approveDraft: (draftId: string) =>
    request<OutreachDraft>(`/api/v1/outreach/${draftId}/approve`, { method: "POST" }),
  rejectDraft: (draftId: string, reviewerNotes?: string) =>
    request<OutreachDraft>(`/api/v1/outreach/${draftId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer_notes: reviewerNotes ?? null }),
    }),
};
