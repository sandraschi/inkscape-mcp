/**
 * MCP API client for Inkscape MCP webapp Agent Lab.
 * Backend: POST /api/v1/tool on port 10900 (proxied via Vite /api).
 */

const API_BASE = "/api";

export async function getBackendHealth(): Promise<{
  ok: boolean;
  error?: string;
}> {
  try {
    const r = await fetch(`${API_BASE}/health`);
    if (!r.ok) return { ok: false, error: `HTTP ${r.status}` };
    return { ok: true };
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "Network error",
    };
  }
}

interface MCPResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export async function callTool<T>(
  tool: string,
  params: Record<string, unknown> = {},
): Promise<MCPResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}/v1/tool`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool, params }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return (await response.json()) as MCPResponse<T>;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

export interface PreviewRecord {
  id: string;
  inputPath: string;
  outputPath: string;
  capturedAt: string;
  dpi?: number;
}

const GALLERY_KEY = "inkscape_mcp_preview_gallery";

export function loadPreviews(): PreviewRecord[] {
  try {
    const raw = localStorage.getItem(GALLERY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as PreviewRecord[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function savePreview(record: PreviewRecord): void {
  const existing = loadPreviews();
  const next = [record, ...existing].slice(0, 24);
  localStorage.setItem(GALLERY_KEY, JSON.stringify(next));
}

export function clearPreviews(): void {
  localStorage.removeItem(GALLERY_KEY);
}
