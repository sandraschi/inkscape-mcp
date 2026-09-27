import { API_BASE, apiDelete, apiGet, apiPatch, apiPost, apiPut } from "./client";

export interface WorkflowStep {
  tool: string;
  operation: string;
  params: Record<string, unknown>;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  workflow_id: string | null;
  name: string;
  file_path: string;
  thumbnail_path: string | null;
  tags: string[];
  created_at: string;
}

export interface RunResult {
  success: boolean;
  error?: string;
  asset?: Asset;
  step_results: Array<{ tool: string; operation: string; result: unknown }>;
}

export const depotApi = {
  listWorkflows: () => apiGet<Workflow[]>("/api/depot/workflows"),
  getWorkflow: (id: string) => apiGet<Workflow>(`/api/depot/workflows/${id}`),
  createWorkflow: (name: string, description: string, steps: WorkflowStep[]) =>
    apiPost<Workflow>("/api/depot/workflows", { name, description, steps }),
  updateWorkflow: (
    id: string,
    body: Partial<Pick<Workflow, "name" | "description" | "steps">>,
  ) => apiPut<Workflow>(`/api/depot/workflows/${id}`, body),
  deleteWorkflow: (id: string) => apiDelete<{ success: boolean }>(`/api/depot/workflows/${id}`),
  runWorkflow: (id: string) => apiPost<RunResult>(`/api/depot/workflows/${id}/run`),

  listAssets: (workflowId?: string) =>
    apiGet<Asset[]>(`/api/depot/assets${workflowId ? `?workflow_id=${workflowId}` : ""}`),
  getAsset: (id: string) => apiGet<Asset>(`/api/depot/assets/${id}`),
  updateAsset: (id: string, body: Partial<Pick<Asset, "name" | "tags">>) =>
    apiPatch<Asset>(`/api/depot/assets/${id}`, body),
  deleteAsset: (id: string) => apiDelete<{ success: boolean }>(`/api/depot/assets/${id}`),

  fileUrl: (id: string) => `${API_BASE}/api/depot/assets/${id}/file`,
  thumbnailUrl: (id: string) => `${API_BASE}/api/depot/assets/${id}/thumbnail`,
};
