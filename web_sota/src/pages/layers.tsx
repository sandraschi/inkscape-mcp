import { EyeOff, Eye, Loader2, Lock, Plus, Unlock } from "lucide-react";
import { useCallback, useState } from "react";
import API_BASE from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface Layer {
  id: string;
  label: string | null;
  visible: boolean;
  locked: boolean;
  style?: string | null;
}

async function callTool(tool: string, params: Record<string, any>) {
  const r = await fetch(`${API_BASE}/api/v1/tool`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, params }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export function LayerManager() {
  const [inputPath, setInputPath] = useState("");
  const [layers, setLayers] = useState<Layer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newLabel, setNewLabel] = useState("");

  const load = useCallback(async () => {
    if (!inputPath) return;
    setLoading(true);
    setError(null);
    try {
      const r = await callTool("inkscape_layers", { operation: "list", input_path: inputPath });
      setLayers(r?.result?.data?.layers || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [inputPath]);

  const doOp = useCallback(
    async (operation: string, extra: Record<string, any> = {}) => {
      setLoading(true);
      setError(null);
      try {
        const r = await callTool("inkscape_layers", {
          operation,
          input_path: inputPath,
          ...extra,
        });
        if (r?.result?.data?.layers) {
          setLayers(r.result.data.layers);
        } else {
          await load();
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [inputPath, load],
  );

  const createLayer = useCallback(async () => {
    if (!newLabel || !inputPath) return;
    setLoading(true);
    setError(null);
    try {
      await callTool("inkscape_layers", {
        operation: "create",
        input_path: inputPath,
        label: newLabel,
      });
      setNewLabel("");
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [inputPath, newLabel, load]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 bg-slate-900/50 text-blue-400">
          <Eye className="h-4 w-4" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Layer Manager</h1>
          <p className="text-sm text-slate-400">
            List, create, rename, hide/show, and lock/unlock layers
          </p>
        </div>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-sm text-slate-200">SVG File</CardTitle>
          <CardDescription className="text-xs">
            Path to an SVG file on the server
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              value={inputPath}
              onChange={(e) => setInputPath(e.target.value)}
              placeholder="/path/to/document.svg"
              className="flex-1 border-slate-800 bg-slate-900 font-mono text-xs text-slate-200"
            />
            <Button
              variant="outline"
              onClick={load}
              disabled={!inputPath || loading}
              className="border-slate-800 text-slate-300"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Load"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/20 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Create Layer */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm text-slate-200">
            <Plus className="h-4 w-4 text-emerald-400" /> New Layer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder="Layer name"
              className="flex-1 border-slate-800 bg-slate-900 text-sm text-slate-200"
              onKeyDown={(e) => e.key === "Enter" && createLayer()}
            />
            <Button
              variant="outline"
              onClick={createLayer}
              disabled={!newLabel || !inputPath || loading}
              className="border-slate-800 text-slate-300"
            >
              <Plus className="mr-1 h-3 w-3" /> Create
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Layer List */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-sm text-slate-200">
            Layers ({layers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {layers.length === 0 && !loading && (
            <p className="text-sm text-slate-500">
              No layers loaded. Enter an SVG path and click Load.
            </p>
          )}
          {loading && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading...
            </div>
          )}
          <div className="space-y-2">
            {layers.map((layer) => (
              <div
                key={layer.id}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      layer.visible ? "bg-emerald-500" : "bg-slate-600"
                    }`}
                  />
                  <div>
                    <span className="text-sm font-medium text-slate-200">
                      {layer.label || layer.id}
                    </span>
                    <span className="ml-2 text-xs text-slate-600">{layer.id}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {layer.visible ? (
                    <button
                      onClick={() => doOp("hide", { layer_id: layer.id })}
                      className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
                      title="Hide"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => doOp("show", { layer_id: layer.id })}
                      className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
                      title="Show"
                    >
                      <EyeOff className="h-4 w-4" />
                    </button>
                  )}
                  {layer.locked ? (
                    <button
                      onClick={() => doOp("unlock", { layer_id: layer.id })}
                      className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
                      title="Unlock"
                    >
                      <Lock className="h-4 w-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => doOp("lock", { layer_id: layer.id })}
                      className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
                      title="Lock"
                    >
                      <Unlock className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
