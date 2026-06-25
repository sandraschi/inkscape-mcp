import {
  Activity,
  CheckCircle2,
  Image,
  Layers,
  Loader2,
  RefreshCw,
  Sparkles,
  Wand2,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import API_BASE from "@/lib/api";
import { useZoom } from "@/lib/use-zoom";
import { useBackendStore } from "@/lib/store";

interface ToolGroup {
  name: string;
  category: string;
  operations: string[];
  op_count: number;
}

interface HealthPayload {
  status?: string;
  server?: string;
  version?: string;
  description?: string;
  uptime_seconds?: number;
  backend_port?: number;
  tool_count?: number;
  tools?: string[];
  tool_groups?: ToolGroup[];
  providers?: {
    ollama?: { available?: boolean; base_url?: string; model?: string; models?: string[] };
    inkscape?: { available?: boolean; version_line?: string | null; path?: string | null; actions_api_recommended?: boolean };
    gemini_key?: boolean;
    anthropic_key?: boolean;
  };
}

const RETRY_DELAYS = [1, 2, 4, 8, 16];

const CATEGORY_ICONS: Record<string, typeof Activity> = {
  file_operations: Activity,
  vector_operations: Wand2,
  document_analysis: Activity,
  agent_vision: Image,
  validation: CheckCircle2,
  layer_management: Layers,
  animation: Sparkles,
  system: Activity,
  sim_art: Wand2,
  fab_art: Wand2,
  fleet_handoff: Activity,
};

export function Dashboard() {
  useZoom();
  const setOnline = useBackendStore((s) => s.setOnline);
  const [h, setH] = useState<HealthPayload | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [restarting, setRestarting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (!res.ok) {
        setErr(`HTTP ${res.status}`);
        setH(null);
        setOnline(false);
        return;
      }
      const data: HealthPayload = await res.json();
      setH(data);
      setErr(null);
      setAttempt(0);
      setOnline(true);
    } catch (e) {
      setH(null);
      setErr(e instanceof Error ? e.message : "Failed");
      setOnline(false);
    }
  }, [setOnline]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!err) return;
    if (attempt >= RETRY_DELAYS.length) return;
    const delay = RETRY_DELAYS[attempt] * 1000;
    const timer = setTimeout(() => {
      setAttempt((a) => a + 1);
      void load();
    }, delay);
    return () => clearTimeout(timer);
  }, [err, attempt, load]);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            setAttempt(0);
            setRestarting(false);
            void load();
          }
        });
      } catch { /* not in Tauri */ }
    })();
    return () => { if (unlisten) unlisten(); };
  }, [load]);

  const restartBackend = useCallback(async () => {
    setRestarting(true);
    setErr(null);
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
    } catch {
      setRestarting(false);
    }
  }, []);

  const inkOk = h?.providers?.inkscape?.available;
  const ollOk = h?.providers?.ollama?.available;

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Hero */}
      <Card className="border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900/50 to-blue-950/20" data-testid="hero">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <Activity className="h-6 w-6 text-blue-500" />
                <h2 className="text-2xl font-bold tracking-tight text-white">
                  {h?.server ?? "Inkscape MCP"}
                </h2>
                <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400 font-mono">
                  v{h?.version ?? "—"}
                </span>
              </div>
              <p className="max-w-2xl text-sm text-slate-400">
                {h?.description ?? "AI-powered vector graphics server. Load the backend to see status."}
              </p>
              <div className="flex flex-wrap gap-4 pt-1 text-xs text-slate-500">
                <span>{h?.tool_count ?? 0} tools registered</span>
                {h?.uptime_seconds != null && (
                  <span>Up {Math.floor(h.uptime_seconds / 60)}m {h.uptime_seconds % 60}s</span>
                )}
                {h?.backend_port && <span>Port {h.backend_port}</span>}
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <div className="flex items-center gap-1.5 text-xs" data-testid="backend-dot">
                <span className={`relative flex h-2.5 w-2.5 ${err ? "bg-red-500" : h ? "bg-emerald-500" : "bg-gray-500"} rounded-full`}>
                  {!err && h && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />}
                </span>
                <span className={`${err ? "text-red-400" : h ? "text-emerald-400" : "text-gray-400"}`}>
                  {err ? "Offline" : h ? "Connected" : "Connecting..."}
                </span>
              </div>
              {err ? (
                <Button variant="outline" size="sm" onClick={restartBackend} disabled={restarting}
                  className="border-red-800 text-red-400 hover:bg-red-950">
                  {restarting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : null}
                  {restarting ? "Restarting..." : "Restart"}
                </Button>
              ) : (
                <Button variant="outline" size="sm" onClick={() => void load()}
                  className="border-slate-800 text-slate-300">
                  <RefreshCw className="mr-1 h-3 w-3" />
                  Refresh
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {err && (
        <div className="rounded-lg border border-red-800 bg-red-950/20 px-4 py-3 text-sm text-red-400" data-testid="dashboard-error">
          {err}
        </div>
      )}

      {/* KPI grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-server">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Server</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white">{h?.server ?? "—"}</div>
            <p className="text-xs text-slate-400">{h?.version ?? ""}</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-tools">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Tools</CardTitle>
            <Wand2 className="h-4 w-4 text-violet-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white">{h?.tool_count ?? "—"}</div>
            <p className="text-xs text-slate-400">{h?.tool_groups?.length ?? 0} portmanteau groups</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-inkscape">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Inkscape CLI</CardTitle>
            {inkOk ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-red-400" />}
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white" data-testid="inkscape-status">
              {inkOk ? "Available" : "Not found"}
            </div>
            <p className="truncate text-xs text-slate-400">{h?.providers?.inkscape?.version_line ?? ""}</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-ollama">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Ollama</CardTitle>
            {ollOk ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-slate-500" />}
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white" data-testid="ollama-status">
              {ollOk ? "Reachable" : "Off / unreachable"}
            </div>
            <p className="text-xs text-slate-400">{h?.providers?.ollama?.model ?? "SVG generation only"}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tool category grid */}
      {h?.tool_groups && h.tool_groups.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-300">Tool Categories</h3>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            {h.tool_groups.map((g) => {
              const Icon = CATEGORY_ICONS[g.category] || Activity;
              return (
                <Link
                  key={g.name}
                  to={g.category === "layer_management" ? "/layers" : g.category === "animation" ? "/animation" : "/agent-tools"}
                  className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2.5 transition-colors hover:bg-slate-800"
                >
                  <Icon className="h-4 w-4 shrink-0 text-slate-400" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-slate-200">{g.name}</div>
                    <div className="text-xs text-slate-500">{g.op_count} operations</div>
                  </div>
                  <span className="shrink-0 text-xs text-slate-600">{g.category}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Provider status row */}
      {h?.providers && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-slate-200">Providers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2 text-xs">
                <span className={`h-2 w-2 rounded-full ${inkOk ? "bg-emerald-500" : "bg-slate-600"}`} />
                <span className="text-slate-400">Inkscape</span>
                <span className="text-slate-600">{inkOk ? (h.providers.inkscape?.version_line ?? "found") : "not installed"}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className={`h-2 w-2 rounded-full ${ollOk ? "bg-emerald-500" : "bg-slate-600"}`} />
                <span className="text-slate-400">Ollama</span>
                <span className="text-slate-600">{ollOk ? h.providers.ollama?.base_url : "unreachable"}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className={`h-2 w-2 rounded-full ${h.providers.gemini_key ? "bg-emerald-500" : "bg-slate-600"}`} />
                <span className="text-slate-400">Gemini</span>
                <span className="text-slate-600">{h.providers.gemini_key ? "key set" : "no key"}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className={`h-2 w-2 rounded-full ${h.providers.anthropic_key ? "bg-emerald-500" : "bg-slate-600"}`} />
                <span className="text-slate-400">Anthropic</span>
                <span className="text-slate-600">{h.providers.anthropic_key ? "key set" : "no key"}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick links */}
      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/status" className="text-blue-400 hover:underline">Full status JSON &rarr;</Link>
        <Link to="/agent-tools" className="text-blue-400 hover:underline">Agent Lab &rarr;</Link>
        <Link to="/animation" className="text-blue-400 hover:underline">Animation Studio &rarr;</Link>
        <Link to="/layers" className="text-blue-400 hover:underline">Layer Manager &rarr;</Link>
        <Link to="/logs" className="text-blue-400 hover:underline">Logs &rarr;</Link>
      </div>
    </div>
  );
}
