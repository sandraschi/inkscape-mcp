const API_BASE = "http://127.0.0.1:11028";
export default API_BASE;

export interface LlmProvider {
  type: string;
  base_url: string;
  models: string[];
  reachable: boolean;
}

export async function getLlmProviders(refresh = false): Promise<LlmProvider[]> {
  const q = refresh ? "?refresh=1" : "";
  const r = await fetch(`${API_BASE}/api/llm/providers${q}`);
  if (!r.ok) throw new Error(`LLM providers failed: ${r.status}`);
  const body = (await r.json()) as { providers: LlmProvider[] };
  return body.providers ?? [];
}
