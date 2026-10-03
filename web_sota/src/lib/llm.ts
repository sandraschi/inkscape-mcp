import { API_BASE, apiGet, apiPost } from "@/api/client";

export type ProviderKind = "local" | "cloud";
export type ModelSource = "live" | "curated" | "none";

export interface ProviderInfo {
  id: string;
  label: string;
  kind: ProviderKind;
  base_url: string;
  needs_key: boolean;
  key_env: string | null;
  configured: boolean;
  detected?: boolean;
  models?: string[];
}

export interface ModelsResponse {
  provider: string;
  models: string[];
  source: ModelSource;
  note?: string;
  error?: string;
  /** True when the names are curated stand-ins (no key) — never a success. */
  key_missing?: boolean;
}

export interface OnboardingState {
  locals: Array<{ id: string; label: string; port: number | null }>;
  clouds_configured: string[];
  recommendation: { path: string; reason: string };
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

const PROVIDER_KEY = "llm_provider";
const MODEL_KEY = "llm_model";
const ONBOARDED_KEY = "llm_onboarded";

function storageGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function storageSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* quota */
  }
}

export function loadSelection(): { provider: string; model: string } {
  return {
    provider: storageGet(PROVIDER_KEY) || "ollama",
    model: storageGet(MODEL_KEY) || "",
  };
}

const SELECTION_EVENT = "llm-selection-changed";

export type Selection = { provider: string; model: string };

export function saveSelection(provider: string, model: string) {
  storageSet(PROVIDER_KEY, provider);
  storageSet(MODEL_KEY, model);
  // Same-tab broadcast (the "storage" event only fires across tabs).
  try {
    window.dispatchEvent(
      new CustomEvent(SELECTION_EVENT, { detail: { provider, model } }),
    );
  } catch {
    /* non-DOM */
  }
}

/** Live-sync hook: fires when any tab/page saves a new LLM selection. */
export function subscribeSelection(cb: (sel: Selection) => void): () => void {
  const onStorage = (e: StorageEvent) => {
    if (e.key === PROVIDER_KEY || e.key === MODEL_KEY) cb(loadSelection());
  };
  const onCustom = (e: Event) => {
    const d = (e as CustomEvent).detail as Selection | undefined;
    if (d && typeof d.provider === "string" && typeof d.model === "string")
      cb({ provider: d.provider, model: d.model });
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(SELECTION_EVENT, onCustom);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(SELECTION_EVENT, onCustom);
  };
}

export interface SavedLlmSettings {
  provider?: string;
  endpoint?: string;
  model?: string;
}

/** Backend truth (AI Settings page owns it): what is actually selected server-side. */
export function fetchLlmSettings(): Promise<SavedLlmSettings> {
  return apiGet<SavedLlmSettings>("/api/settings/llm");
}

export function isOnboarded(): boolean {
  return storageGet(ONBOARDED_KEY) === "1";
}

export function markOnboarded() {
  storageSet(ONBOARDED_KEY, "1");
}

export function fetchProviders(): Promise<{ providers: ProviderInfo[] }> {
  return apiGet<{ providers: ProviderInfo[] }>("/api/llm/providers");
}

export function fetchModels(provider: string): Promise<ModelsResponse> {
  return apiGet<ModelsResponse>(
    `/api/llm/models?provider=${encodeURIComponent(provider)}`,
  );
}

export function fetchOnboarding(): Promise<OnboardingState> {
  return apiGet<OnboardingState>("/api/llm/onboarding");
}

export interface TestResult {
  success: boolean;
  /** True only for a live list. Curated-without-key is ok:false by design. */
  ok: boolean;
  provider: string;
  models: string[];
  source: ModelSource;
  note?: string;
  error?: string;
}

/**
 * Validate a provider without saving anything. Pass the card's typed key
 * (if any) — it travels in the POST body only and is never persisted.
 * A Test that ignores the typed key reports curated names as success;
 * that lie is BUG-042 (giskard-mcp 2026-09-21).
 */
export function testProvider(
  provider: string,
  apiKey?: string,
  endpoint?: string,
): Promise<TestResult> {
  return apiPost<TestResult>("/api/llm/test", {
    provider,
    ...(apiKey ? { api_key: apiKey } : {}),
    ...(endpoint ? { endpoint } : {}),
  });
}

export interface LlmSwitchResult {
  evicted: string[];
  warmed: boolean;
  engine: boolean;
}

export function unloadLlm(body: {
  provider: string;
  endpoint?: string;
}): Promise<{ success: boolean; evicted: string[] }> {
  return apiPost("/api/llm/unload", body);
}

export interface LoadedModel {
  name: string;
  size_vram_mb: number;
  expires_at: string;
}

export interface GpuInfo {
  index: number;
  name: string;
  total_mb: number;
  used_mb: number;
  free_mb: number;
}

/** Live GPU VRAM telemetry ([] when the backend has no GPU / driver). */
export async function fetchGpus(): Promise<GpuInfo[]> {
  try {
    const d = await apiGet<{ gpus?: GpuInfo[] }>("/api/llm/gpus");
    return d.gpus ?? [];
  } catch {
    return [];
  }
}

/** Models currently resident on the local engine (Settings KPI, evict planning). */
export function fetchLoaded(
  provider: string,
  endpoint?: string,
): Promise<{ success: boolean; engine: boolean; models: LoadedModel[] }> {
  const qs =
    `?provider=${encodeURIComponent(provider)}` +
    (endpoint ? `&endpoint=${encodeURIComponent(endpoint)}` : "");
  return apiGet(`/api/llm/loaded${qs}`);
}

export function saveLlmSettings(body: {
  provider: string;
  endpoint?: string;
  model: string;
  api_key?: string;
  /** false: attach api_key to `provider` without changing the active
   * provider/model pair (BUG-043). Defaults true (backend-side) for the
   * Settings page's own "make this the active pair" flow. */
  select?: boolean;
}): Promise<{
  success: boolean;
  key_saved?: boolean;
  switch?: LlmSwitchResult;
}> {
  return apiPost("/api/settings/llm", body);
}

export function startInstall(
  engine: string,
): Promise<{ engine: string; started: boolean; reason?: string }> {
  return apiPost("/api/llm/install", { engine });
}

export function installStatus(
  engine: string,
): Promise<{ engine: string; state: string; output?: string }> {
  return apiGet(`/api/llm/install/status?engine=${encodeURIComponent(engine)}`);
}

export async function chatComplete(
  provider: string,
  model: string,
  messages: ChatMessage[],
): Promise<string> {
  const d = await apiPost<{ content: string }>("/api/llm/chat", {
    provider,
    model,
    messages,
  });
  return d.content;
}

/** Stream assistant tokens via SSE; calls onToken per delta. Falls back to non-stream. */
export async function streamChat(
  provider: string,
  model: string,
  messages: ChatMessage[],
  onToken: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  let r: Response;
  try {
    r = await fetch(`${API_BASE}/api/llm/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, model, messages }),
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    throw e;
  }
  if (!r.ok || !r.body) {
    const text = await chatComplete(provider, model, messages);
    onToken(text);
    return;
  }
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (payload === "[DONE]" || payload === "") continue;
      try {
        const chunk = JSON.parse(payload) as {
          choices?: Array<{ delta?: { content?: string } }>;
        };
        const text = chunk.choices?.[0]?.delta?.content ?? "";
        if (text) onToken(text);
      } catch {
        /* keep-alive or partial frame */
      }
    }
  }
}
