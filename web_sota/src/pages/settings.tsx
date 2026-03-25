import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, Server, Info } from "lucide-react";

interface HealthPayload {
    status?: string;
    server?: string;
    version?: string;
    providers?: {
        ollama?: { available?: boolean; base_url?: string; model?: string; models?: string[] };
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

    const load = async () => {
        setError(null);
        try {
            const res = await fetch("/api/health");
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

    useEffect(() => {
        void load();
    }, []);

    const ink = health?.providers?.inkscape;
    const oll = health?.providers?.ollama;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Settings</h2>
                    <p className="text-slate-400">Read-only snapshot from the running server. Change Inkscape or Ollama via environment and restart.</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void load()} className="border-slate-800 text-slate-300">
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            {error && <p className="text-yellow-400">{error}</p>}

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                        <Server className="h-5 w-5 text-blue-400" />
                        Process &amp; Inkscape
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        {health?.server} {health?.version} — {health?.status}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-300">
                    <div>
                        <span className="text-slate-500">Inkscape executable: </span>
                        <code className="break-all text-slate-200">{ink?.path ?? "—"}</code>
                    </div>
                    <div>
                        <span className="text-slate-500">CLI detected: </span>
                        {ink?.available ? "yes" : "no"}
                    </div>
                    {ink?.version_line && (
                        <div>
                            <span className="text-slate-500">Version: </span>
                            {ink.version_line}
                        </div>
                    )}
                    {ink?.actions_api_recommended === false && (
                        <p className="text-yellow-500">Inkscape below 1.2: some Actions may be limited.</p>
                    )}
                </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Optional Ollama (REST / generate-svg)</CardTitle>
                    <CardDescription className="text-slate-400">
                        Not required for MCP tool use. Listed models come from <code className="text-slate-300">/api/health</code> probing Ollama.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-slate-300">
                    <div>
                        <span className="text-slate-500">Reachable: </span>
                        {oll?.available ? "yes" : "no"}
                    </div>
                    <div>
                        <span className="text-slate-500">Base URL: </span>
                        <code className="text-slate-200">{oll?.base_url ?? "—"}</code>
                    </div>
                    <div>
                        <span className="text-slate-500">Default model env: </span>
                        <code className="text-slate-200">{oll?.model ?? "—"}</code>
                    </div>
                    <div>
                        <span className="text-slate-500">Models (tags): </span>
                        {oll?.models && oll.models.length > 0 ? (
                            <ul className="mt-1 list-inside list-disc font-mono text-xs text-slate-400">
                                {oll.models.slice(0, 20).map((m) => (
                                    <li key={m}>{m}</li>
                                ))}
                                {oll.models.length > 20 && <li>…</li>}
                            </ul>
                        ) : (
                            <span className="text-slate-500">none (Ollama not running or not installed)</span>
                        )}
                    </div>
                </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                        <Info className="h-5 w-5 text-slate-400" />
                        Configure outside this UI
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-slate-400">
                    <p>Set <code className="text-slate-300">INKSCAPE_PATH</code>, <code className="text-slate-300">OLLAMA_BASE_URL</code>,</p>
                    <p>
                        <code className="text-slate-300">MCP_PORT</code> (default 10847 with this repo&apos;s CLI), then restart the server. MCP clients
                        (Cursor, Claude) use their own JSON config — see repo <code className="text-slate-300">docs/IDE_MCP.md</code>.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
