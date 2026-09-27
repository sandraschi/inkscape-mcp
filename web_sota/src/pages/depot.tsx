import { Archive, Loader2, Play, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { depotApi, type Asset, type Workflow, type WorkflowStep } from "@/api/depot";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

function emptyStep(): WorkflowStep {
  return { tool: "inkscape_vector", operation: "create_object", params: {} };
}

function StepEditor({
  steps,
  onChange,
  readOnly,
}: {
  steps: WorkflowStep[];
  onChange: (steps: WorkflowStep[]) => void;
  readOnly: boolean;
}) {
  const update = (i: number, patch: Partial<WorkflowStep>) => {
    const next = steps.map((s, idx) => (idx === i ? { ...s, ...patch } : s));
    onChange(next);
  };
  const updateParamsText = (i: number, text: string) => {
    try {
      update(i, { params: JSON.parse(text || "{}") });
    } catch {
      // ignore invalid JSON while typing - last valid parse wins
    }
  };

  return (
    <div className="space-y-2">
      {steps.map((step, i) => (
        <div
          key={`${step.tool}-${i}`}
          className="grid grid-cols-1 gap-2 rounded-lg border border-slate-800 bg-slate-900/50 p-3 md:grid-cols-[1fr_1fr_2fr_auto]"
        >
          <Input
            value={step.tool}
            disabled={readOnly}
            onChange={(e) => update(i, { tool: e.target.value })}
            placeholder="tool (e.g. inkscape_vector)"
            className="border-slate-800 bg-slate-950 font-mono text-xs text-slate-200"
          />
          <Input
            value={step.operation}
            disabled={readOnly}
            onChange={(e) => update(i, { operation: e.target.value })}
            placeholder="operation"
            className="border-slate-800 bg-slate-950 font-mono text-xs text-slate-200"
          />
          <textarea
            defaultValue={JSON.stringify(step.params, null, 0)}
            disabled={readOnly}
            onChange={(e) => updateParamsText(i, e.target.value)}
            placeholder="{ }"
            rows={1}
            className="rounded-md border border-slate-800 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-200 disabled:opacity-50"
          />
          {!readOnly && (
            <button
              onClick={() => onChange(steps.filter((_, idx) => idx !== i))}
              className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-red-400"
              title="Remove step"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      ))}
      {!readOnly && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => onChange([...steps, emptyStep()])}
          className="border-slate-800 text-slate-300"
        >
          <Plus className="mr-1 h-3 w-3" /> Add step
        </Button>
      )}
    </div>
  );
}

function WorkflowCard({
  workflow,
  onChanged,
}: {
  workflow: Workflow;
  onChanged: () => void;
}) {
  const [steps, setSteps] = useState(workflow.steps);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAsset, setLastAsset] = useState<Asset | null>(null);

  const run = useCallback(async () => {
    setRunning(true);
    setError(null);
    setLastAsset(null);
    try {
      const result = await depotApi.runWorkflow(workflow.id);
      if (!result.success) {
        setError(result.error || "Workflow run failed");
      } else if (result.asset) {
        setLastAsset(result.asset);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }, [workflow.id]);

  const saveEdits = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      await depotApi.updateWorkflow(workflow.id, { steps });
      onChanged();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }, [workflow.id, steps, onChanged]);

  const saveAsNew = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      await depotApi.createWorkflow(`${workflow.name} (copy)`, workflow.description, steps);
      onChanged();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }, [workflow.name, workflow.description, steps, onChanged]);

  const remove = useCallback(async () => {
    try {
      await depotApi.deleteWorkflow(workflow.id);
      onChanged();
    } catch (e: any) {
      setError(e.message);
    }
  }, [workflow.id, onChanged]);

  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-sm text-slate-200">
              {workflow.name}
              {workflow.is_builtin && (
                <Badge variant="outline" className="border-slate-700 text-slate-400">
                  builtin
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="text-sm">{workflow.description}</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={run}
              disabled={running}
              className="bg-blue-600 text-white hover:bg-blue-500"
            >
              {running ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <Play className="mr-1 h-3 w-3" />
              )}
              Run
            </Button>
            {!workflow.is_builtin && (
              <button
                onClick={remove}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-red-400"
                title="Delete workflow"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <StepEditor steps={steps} onChange={setSteps} readOnly={workflow.is_builtin} />
        <div className="flex gap-2">
          {!workflow.is_builtin && (
            <Button
              variant="outline"
              size="sm"
              onClick={saveEdits}
              disabled={saving}
              className="border-slate-800 text-slate-300"
            >
              Save
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={saveAsNew}
            disabled={saving}
            className="border-slate-800 text-slate-300"
          >
            Save as new
          </Button>
        </div>
        {error && (
          <div className="rounded-lg border border-red-800 bg-red-950/20 px-3 py-2 text-sm text-red-400">
            {error}
          </div>
        )}
        {lastAsset && (
          <div className="flex items-center gap-3 rounded-lg border border-emerald-800 bg-emerald-950/20 px-3 py-2">
            {lastAsset.thumbnail_path && (
              <img
                src={depotApi.thumbnailUrl(lastAsset.id)}
                alt={lastAsset.name}
                className="h-16 w-16 rounded border border-slate-800 object-contain bg-white"
              />
            )}
            <span className="text-sm text-emerald-400">
              Produced asset "{lastAsset.name}" - see the Assets tab.
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AssetsGrid() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAssets(await depotApi.listAssets());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const remove = useCallback(
    async (id: string) => {
      await depotApi.deleteAsset(id);
      await load();
    },
    [load],
  );

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-200">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading assets...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/20 px-4 py-2 text-sm text-red-400">
        {error}
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <p className="text-sm text-slate-400">
        No assets yet - run a workflow from the Workflows tab.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {assets.map((asset) => (
        <Card key={asset.id} className="border-slate-800 bg-slate-950/50">
          <CardContent className="space-y-2 p-3">
            <a href={depotApi.fileUrl(asset.id)} target="_blank" rel="noreferrer">
              <div className="flex h-32 w-full items-center justify-center overflow-hidden rounded-md border border-slate-800 bg-white">
                {asset.thumbnail_path ? (
                  <img
                    src={depotApi.thumbnailUrl(asset.id)}
                    alt={asset.name}
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <Archive className="h-6 w-6 text-slate-400" />
                )}
              </div>
            </a>
            <p className="truncate text-xs text-slate-300" title={asset.name}>
              {asset.name}
            </p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-600">
                {new Date(asset.created_at).toLocaleString()}
              </span>
              <button
                onClick={() => remove(asset.id)}
                className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-red-400"
                title="Delete asset"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function Depot() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setWorkflows(await depotApi.listWorkflows());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createBlank = useCallback(async () => {
    await depotApi.createWorkflow("New workflow", "", [emptyStep()]);
    await load();
  }, [load]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 bg-slate-900/50 text-blue-400">
          <Archive className="h-4 w-4" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Depot</h1>
          <p className="text-sm text-slate-200">
            Editable demo workflows and the assets each run produces
          </p>
        </div>
      </div>

      <Tabs defaultValue="workflows" className="w-full">
        <TabsList className="w-full border-b border-slate-800 bg-transparent">
          <TabsTrigger value="workflows">Workflows</TabsTrigger>
          <TabsTrigger value="assets">Assets</TabsTrigger>
        </TabsList>

        <TabsContent value="workflows" className="mt-6 space-y-4">
          <Button
            variant="outline"
            size="sm"
            onClick={createBlank}
            className="border-slate-800 text-slate-300"
          >
            <Plus className="mr-1 h-3 w-3" /> New workflow
          </Button>
          {error && (
            <div className="rounded-lg border border-red-800 bg-red-950/20 px-4 py-2 text-sm text-red-400">
              {error}
            </div>
          )}
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-slate-200">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading workflows...
            </div>
          ) : (
            <div className="space-y-4">
              {workflows.map((wf) => (
                <WorkflowCard key={wf.id} workflow={wf} onChanged={load} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="assets" className="mt-6">
          <AssetsGrid />
        </TabsContent>
      </Tabs>
    </div>
  );
}
