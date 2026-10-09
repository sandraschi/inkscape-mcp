import { Loader2, RefreshCw, Server, Settings2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/api/client";
import { ActiveLlmCard } from "@/components/llm/ActiveLlmCard";
import { LlmOnboarding } from "@/components/llm/LlmOnboarding";
import { LlmProviderCards } from "@/components/llm/LlmProviderCards";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import API_BASE from "@/lib/api";
import {
  fetchLlmSettings,
  fetchProviders,
  loadSelection,
  type ProviderInfo,
} from "@/lib/llm";

interface ServerSettingField {
  value: string;
  source: string;
  note?: string;
}

interface ServerSettingsPayload {
  inkscape_path: ServerSettingField;
  ollama_base_url: ServerSettingField;
  ollama_model: ServerSettingField;
  mcp_port: ServerSettingField;
}

interface HealthPayload {
  status?: string;
  server?: string;
  version?: string;
  providers?: {
    inkscape?: {
      available?: boolean;
      path?: string | null;
      version_line?: string | null;
      actions_api_recommended?: boolean;
    };
  };
}

export function Settings() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [serverSettings, setServerSettings] =
    useState<ServerSettingsPayload | null>(null);
  const [form, setForm] = useState({ inkscape_path: "", mcp_port: "" });
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [probing, setProbing] = useState(true);
  const [llmSelected, setLlmSelected] = useState("ollama");

  const refreshProviders = useCallback(async () => {
    try {
      const pv = await fetchProviders();
      setProviders(pv.providers);
    } catch {
      /* keep previous list */
    }
  }, []);

  const load = async () => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (!res.ok) {
        setError(`HTTP ${res.status}`);
        setHealth(null);
        return;
      }
      setHealth(await res.json());
    } catch (e) {
      setHealth(null);
      setError(e instanceof Error ? e.message : "Failed to load /api/health");
    }
  };

  const loadServerSettings = useCallback(async () => {
    try {
      const s = await apiGet<ServerSettingsPayload>("/api/settings/server");
      setServerSettings(s);
      setForm({
        inkscape_path: s.inkscape_path.value,
        mcp_port: s.mcp_port.value,
      });
    } catch {
      /* keep previous state */
    }
  }, []);

  useEffect(() => {
    void load();
    void loadServerSettings();
    (async () => {
      await refreshProviders();
      const prev = loadSelection();
      if (prev.provider) setLlmSelected(prev.provider);
      try {
        const s = await fetchLlmSettings();
        if (s.provider) setLlmSelected(s.provider);
      } catch {
        /* backend truth unavailable: local mirror stands */
      }
      setProbing(false);
    })();
  }, [loadServerSettings, refreshProviders]);

  const handleCardsChanged = useCallback(async () => {
    await refreshProviders();
  }, [refreshProviders]);

  const saveServerSettings = useCallback(async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      // Only send fields that actually changed - sending all four every time
      // would re-pin already-correct values as "saved" overrides (blocking
      // e.g. future Inkscape auto-detection) and fire mcp_port's
      // restart_required on every save regardless of whether it changed.
      const changed: Record<string, string> = {};
      if (serverSettings) {
        for (const key of Object.keys(form) as Array<keyof typeof form>) {
          if (form[key] !== serverSettings[key].value) changed[key] = form[key];
        }
      } else {
        Object.assign(changed, form);
      }
      if (Object.keys(changed).length === 0) {
        setSaveMsg("Nothing changed.");
        return;
      }
      const res = await apiPost<{
        success: boolean;
        error?: string;
        restart_required?: boolean;
      }>("/api/settings/server", changed);
      if (!res.success) {
        setSaveMsg(res.error || "Save failed.");
      } else {
        setSaveMsg(
          res.restart_required
            ? "Saved. MCP_PORT takes effect on next restart — this page is served on the current port."
            : "Saved and applied immediately.",
        );
        await loadServerSettings();
        await load();
      }
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }, [form, loadServerSettings]);

  const ink = health?.providers?.inkscape;

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Settings
          </h2>
          <p className="text-slate-300">
            Server-level config (Inkscape path, MCP port) plus local and cloud
            LLM providers used by Chat and agent tools.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          data-testid="settings-refresh"
          onClick={() => void load()}
          className="border-slate-800 text-slate-300"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error && <p className="text-yellow-400">{error}</p>}

      <Card
        data-testid="settings-server-card"
        className="border-slate-800 bg-slate-950/50"
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Server className="h-5 w-5 text-blue-400" />
            Process &amp; Inkscape
          </CardTitle>
          <CardDescription className="text-slate-300">
            {health?.server} {health?.version} — {health?.status}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-300">
          <div>
            <span className="text-slate-400">Inkscape executable: </span>
            <code className="break-all text-slate-200">{ink?.path ?? "—"}</code>
          </div>
          <div>
            <span className="text-slate-400">CLI detected: </span>
            {ink?.available ? "yes" : "no"}
          </div>
          {ink?.version_line && (
            <div>
              <span className="text-slate-400">Version: </span>
              {ink.version_line}
            </div>
          )}
          {ink?.actions_api_recommended === false && (
            <p className="text-yellow-500">
              Inkscape below 1.2: some Actions may be limited.
            </p>
          )}
        </CardContent>
      </Card>

      <LlmOnboarding mode="full" />
      <ActiveLlmCard />
      <LlmProviderCards
        providers={providers}
        probing={probing}
        selected={llmSelected}
        onChanged={handleCardsChanged}
      />

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Settings2 className="h-5 w-5 text-blue-400" />
            Server Configuration
          </CardTitle>
          <CardDescription className="text-slate-300">
            Inkscape path applies immediately, no restart (MCP port needs one).
            MCP clients (Cursor, Claude) use their own JSON config — see repo{" "}
            <code className="text-slate-300">docs/IDE_MCP.md</code>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="space-y-1">
            <label
              className="text-xs text-slate-400"
              htmlFor="set-inkscape-path"
            >
              Inkscape executable path
            </label>
            <Input
              id="set-inkscape-path"
              value={form.inkscape_path}
              onChange={(e) =>
                setForm((f) => ({ ...f, inkscape_path: e.target.value }))
              }
              placeholder="C:\Program Files\Inkscape\bin\inkscape.exe"
              className="border-slate-800 bg-slate-900 font-mono text-xs text-slate-200"
            />
            {serverSettings && (
              <p className="text-xs text-slate-500">
                source: {serverSettings.inkscape_path.source}
              </p>
            )}
          </div>
          <div className="space-y-1">
            <label className="text-xs text-slate-400" htmlFor="set-mcp-port">
              MCP HTTP port
            </label>
            <Input
              id="set-mcp-port"
              value={form.mcp_port}
              onChange={(e) =>
                setForm((f) => ({ ...f, mcp_port: e.target.value }))
              }
              placeholder="11027"
              className="border-slate-800 bg-slate-900 font-mono text-xs text-slate-200 max-w-32"
            />
            <p className="text-xs text-slate-500">
              {serverSettings?.mcp_port.note ?? "Takes effect on next restart."}
            </p>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <Button
              onClick={saveServerSettings}
              disabled={saving}
              className="bg-blue-600 text-white hover:bg-blue-500"
            >
              {saving ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : null}
              Save
            </Button>
            {saveMsg && (
              <span className="text-xs text-slate-400">{saveMsg}</span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
