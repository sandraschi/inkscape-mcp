import {
  type Bot,
  Camera,
  GitPullRequest,
  ImageIcon,
  ScanEye,
  Search,
  Server,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  callTool,
  clearPreviews,
  getBackendHealth,
  loadPreviews,
  type PreviewRecord,
  savePreview,
} from "@/api/mcp";

type TabId =
  | "runtime"
  | "vision"
  | "validation"
  | "gallery"
  | "analysis"
  | "fleet";

function ResultBox({ text }: { text: string | null }) {
  if (!text) return null;
  return (
    <pre className="mt-3 p-3 text-xs bg-slate-900 rounded-lg overflow-x-auto whitespace-pre-wrap border border-slate-800 text-slate-300">
      {text}
    </pre>
  );
}

export function AgentTools() {
  const [tab, setTab] = useState<TabId>("runtime");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [previews, setPreviews] = useState<PreviewRecord[]>([]);

  const [inputPath, setInputPath] = useState(
    "D:/Temp/inkscape_mcp/diagram.svg",
  );
  const [outputPath, setOutputPath] = useState(
    "D:/Temp/inkscape_mcp/review.png",
  );
  const [dpi, setDpi] = useState("192");
  const [dpiList, setDpiList] = useState("96,192,384");

  const [projectPath, setProjectPath] = useState("D:/Unity/MyProject");
  const [stagingDir, setStagingDir] = useState(
    "D:/Temp/fleet_pipeline/inkscape_staging",
  );
  const [skipGimp, setSkipGimp] = useState(false);

  const tabs: { id: TabId; label: string; icon: typeof Bot }[] = [
    { id: "runtime", label: "Runtime", icon: Server },
    { id: "vision", label: "Vision", icon: ScanEye },
    { id: "validation", label: "Validation", icon: ShieldCheck },
    { id: "gallery", label: "Gallery", icon: ImageIcon },
    { id: "analysis", label: "Analysis", icon: Search },
    { id: "fleet", label: "Fleet", icon: GitPullRequest },
  ];

  useEffect(() => {
    setPreviews(loadPreviews());
  }, []);

  const run = async (tool: string, params: Record<string, unknown>) => {
    setLoading(true);
    setResult(null);
    try {
      const res = await callTool(tool, params);
      setResult(JSON.stringify(res, null, 2));

      if (
        tool === "inkscape_render" &&
        params.operation === "export_preview" &&
        res.success &&
        res.data &&
        typeof res.data === "object"
      ) {
        const data = res.data as Record<string, unknown>;
        const record: PreviewRecord = {
          id: crypto.randomUUID(),
          inputPath: String(params.input_path ?? inputPath),
          outputPath: String(data.output_path ?? outputPath),
          capturedAt: new Date().toISOString(),
          dpi: Number(params.dpi ?? dpi),
        };
        savePreview(record);
        setPreviews(loadPreviews());
      }
    } catch (e) {
      setResult(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const checkBackend = async () => {
    const r = await getBackendHealth();
    setBackendOk(r.ok);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Agent Tools
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Phase 1–3: execution mode, vision exports, SVG validation, fleet
            handoff.
          </p>
        </div>
        <button
          type="button"
          onClick={checkBackend}
          className="px-3 py-1.5 text-sm bg-slate-800 text-slate-200 rounded-md hover:bg-slate-700"
        >
          Check backend
        </button>
      </div>

      {backendOk !== null && (
        <p
          className={`text-sm ${backendOk ? "text-emerald-400" : "text-red-400"}`}
        >
          Backend {backendOk ? "online" : "offline"} — run web_sota start.ps1 if
          needed.
        </p>
      )}

      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => {
              setTab(t.id);
              setResult(null);
            }}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.id
                ? "bg-blue-600 text-white"
                : "bg-slate-900 text-slate-400 hover:text-white"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      <div className="border border-slate-800 rounded-lg p-5 bg-slate-950/50 space-y-4">
        {tab === "runtime" && (
          <>
            <h3 className="font-semibold text-white">Runtime guidance</h3>
            <p className="text-sm text-slate-400">
              Hands-In: open SVG in Inkscape GUI or set INKSCAPE_GUI_WATCH=1.
              Hands-Off: batch CLI.
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm"
                onClick={() =>
                  run("inkscape_system", { operation: "execution_mode" })
                }
              >
                Execution mode
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() => run("inkscape_system", { operation: "status" })}
              >
                Server status
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() =>
                  run("inkscape_system", { operation: "diagnostics" })
                }
              >
                Diagnostics
              </button>
            </div>
          </>
        )}

        {tab === "vision" && (
          <>
            <h3 className="font-semibold text-white">Vision exports</h3>
            <label className="block text-sm text-slate-300">
              Input SVG
              <input
                className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                value={inputPath}
                onChange={(e) => setInputPath(e.target.value)}
              />
            </label>
            <label className="block text-sm text-slate-300">
              Output PNG
              <input
                className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                value={outputPath}
                onChange={(e) => setOutputPath(e.target.value)}
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm text-slate-300">
                DPI (export_preview)
                <input
                  className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                  value={dpi}
                  onChange={(e) => setDpi(e.target.value)}
                />
              </label>
              <label className="block text-sm text-slate-300">
                DPI list CSV (export_multi_dpi)
                <input
                  className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                  value={dpiList}
                  onChange={(e) => setDpiList(e.target.value)}
                />
              </label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm"
                onClick={() =>
                  run("inkscape_render", {
                    operation: "export_preview",
                    input_path: inputPath,
                    output_path: outputPath,
                    dpi: Number(dpi) || 96,
                  })
                }
              >
                <Camera className="w-4 h-4 inline mr-1" />
                Export preview
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() =>
                  run("inkscape_render", {
                    operation: "export_multi_dpi",
                    input_path: inputPath,
                    output_path: outputPath,
                    dpi_list: dpiList,
                  })
                }
              >
                Multi-DPI batch
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() =>
                  run("inkscape_render", {
                    operation: "get_document_summary",
                    input_path: inputPath,
                  })
                }
              >
                Document summary
              </button>
            </div>
          </>
        )}

        {tab === "validation" && (
          <>
            <h3 className="font-semibold text-white">SVG validation</h3>
            <label className="block text-sm text-slate-300">
              Input SVG
              <input
                className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                value={inputPath}
                onChange={(e) => setInputPath(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  ["validate_svg", "Full validate"],
                  ["audit_web_svg", "Web audit"],
                  ["check_viewbox", "ViewBox"],
                  ["check_stroke_fill", "Stroke/fill"],
                  ["check_size_limits", "Size limits"],
                ] as const
              ).map(([op, label]) => (
                <button
                  key={op}
                  type="button"
                  disabled={loading}
                  className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                  onClick={() =>
                    run("inkscape_validation", {
                      operation: op,
                      input_path: inputPath,
                    })
                  }
                >
                  {label}
                </button>
              ))}
            </div>
          </>
        )}

        {tab === "gallery" && (
          <>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white">Preview gallery</h3>
              <button
                type="button"
                className="text-sm text-slate-400 hover:text-white"
                onClick={() => {
                  clearPreviews();
                  setPreviews([]);
                }}
              >
                Clear
              </button>
            </div>
            {previews.length === 0 ? (
              <p className="text-sm text-slate-500">
                No previews yet. Run export_preview first.
              </p>
            ) : (
              <ul className="space-y-2 text-sm text-slate-300">
                {previews.map((p) => (
                  <li
                    key={p.id}
                    className="rounded-md border border-slate-800 bg-slate-900/50 p-3"
                  >
                    <div className="font-medium text-white truncate">
                      {p.outputPath}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {p.inputPath} · {p.dpi ?? "?"} DPI ·{" "}
                      {new Date(p.capturedAt).toLocaleString()}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {tab === "analysis" && (
          <>
            <h3 className="font-semibold text-white">Document analysis</h3>
            <label className="block text-sm text-slate-300">
              Input SVG
              <input
                className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                value={inputPath}
                onChange={(e) => setInputPath(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  ["statistics", "Statistics"],
                  ["dimensions", "Dimensions"],
                  ["objects", "Objects"],
                  ["structure", "Structure"],
                  ["quality", "Quality"],
                ] as const
              ).map(([op, label]) => (
                <button
                  key={op}
                  type="button"
                  disabled={loading}
                  className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                  onClick={() =>
                    run("inkscape_analysis", {
                      operation: op,
                      input_path: inputPath,
                    })
                  }
                >
                  {label}
                </button>
              ))}
            </div>
          </>
        )}

        {tab === "fleet" && (
          <>
            <h3 className="font-semibold text-white">Fleet handoff</h3>
            <p className="text-sm text-slate-400">
              inkscape SVG → PNG export → gimp-mcp QA (:10773) → unity3d-mcp
              sprite (:10831)
            </p>
            <label className="block text-sm text-slate-300">
              Unity project path
              <input
                className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
              />
            </label>
            <label className="block text-sm text-slate-300">
              Staging directory
              <input
                className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-md text-sm text-white"
                value={stagingDir}
                onChange={(e) => setStagingDir(e.target.value)}
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={skipGimp}
                onChange={(e) => setSkipGimp(e.target.checked)}
              />
              Skip gimp validation (offline test)
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm"
                onClick={() =>
                  run("inkscape_fleet", {
                    operation: "run_pipeline",
                    svg_path: inputPath,
                    project_path: projectPath,
                    staging_dir: stagingDir,
                    dpi: Number(dpi) || 192,
                    skip_gimp: skipGimp,
                  })
                }
              >
                Run full pipeline
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() =>
                  run("inkscape_fleet", {
                    operation: "push_gimp_raster",
                    svg_path: inputPath,
                    dpi: Number(dpi) || 192,
                    staging_dir: stagingDir,
                  })
                }
              >
                Push to GIMP
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() =>
                  run("inkscape_fleet", {
                    operation: "stage_blender_svg",
                    svg_path: inputPath,
                  })
                }
              >
                Stage for Blender
              </button>
              <button
                type="button"
                disabled={loading}
                className="px-4 py-2 bg-slate-800 text-slate-200 rounded-md text-sm"
                onClick={() =>
                  run("inkscape_fleet", {
                    operation: "list_staging",
                    staging_dir: stagingDir,
                  })
                }
              >
                List staging
              </button>
            </div>
          </>
        )}

        {loading && <p className="text-sm text-blue-400">Running tool…</p>}
        <ResultBox text={result} />
      </div>
    </div>
  );
}
