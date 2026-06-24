import { Activity, CheckCircle2, Loader2, RefreshCw, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import API_BASE from "@/lib/api";
import { useZoom } from "@/lib/use-zoom";
import { useBackendStore } from "@/lib/store";

interface HealthPayload {
  status?: string;
  server?: string;
  version?: string;
  uptime_seconds?: number;
  tool_count?: number;
  providers?: {
    ollama?: { available?: boolean; base_url?: string; model?: string };
    inkscape?: { available?: boolean; version_line?: string | null };
  };
}

const RETRY_DELAYS = [1, 2, 4, 8, 16];

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
      const data = await res.json();
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

  useEffect(() => {
    void load();
  }, [load]);

  // Exponential backoff retry when backend is unreachable
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

  // Tauri backend-status event listener (instant refresh when backend comes online)
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
      } catch {
        // Not in Tauri — HTTP polling handles it
      }
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
      setRestarting(false); // not in Tauri
    }
  }, []);

  const inkOk = h?.providers?.inkscape?.available;
  const ollOk = h?.providers?.ollama?.available;

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Overview
          </h2>
          <p className="text-slate-400">
            Quick snapshot from GET /api/health. Details on the Status page.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <span className={`inline-block h-2 w-2 rounded-full ${err ? "bg-red-500" : h ? "bg-green-500" : "bg-gray-500"} animate-pulse`} data-testid="backend-dot" />
            <span className="text-slate-400">{err ? "Offline" : h ? "Connected" : "Connecting..."}</span>
          </div>
          {err && (
            <Button variant="outline" size="sm" onClick={restartBackend} disabled={restarting} className="border-red-800 text-red-400 hover:bg-red-950">
              {restarting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : null}
              {restarting ? "Restarting..." : "Restart Backend"}
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => void load()} className="border-slate-800 text-slate-300">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {err && <p className="text-yellow-400" data-testid="dashboard-error">{err}</p>}

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-server">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Server
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white">
              {h?.server ?? "—"}
            </div>
            <p className="text-xs text-slate-400">{h?.version ?? ""}</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-tools">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Tools
            </CardTitle>
            <Activity className="h-4 w-4 text-violet-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white">
              {h?.tool_count ?? "—"}
            </div>
            <p className="text-xs text-slate-400">
              {h?.uptime_seconds != null ? `${Math.floor(h.uptime_seconds / 60)}m uptime` : ""}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-inkscape">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Inkscape CLI
            </CardTitle>
            {inkOk ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ) : (
              <XCircle className="h-4 w-4 text-red-400" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white" data-testid="inkscape-status">
              {inkOk ? "Available" : "Not found"}
            </div>
            <p className="truncate text-xs text-slate-400">
              {h?.providers?.inkscape?.version_line ?? ""}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-ollama">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Ollama (optional)
            </CardTitle>
            {ollOk ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ) : (
              <XCircle className="h-4 w-4 text-slate-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-white" data-testid="ollama-status">
              {ollOk ? "Reachable" : "Off / unreachable"}
            </div>
            <p className="text-xs text-slate-400">
              Only needed for /api/generate-svg
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/status" className="text-blue-400 hover:underline">
          Full status JSON →
        </Link>
        <Link to="/logs" className="text-blue-400 hover:underline">
          Logs →
        </Link>
        <Link to="/help" className="text-blue-400 hover:underline">
          Help →
        </Link>
      </div>
    </div>
  );
}
