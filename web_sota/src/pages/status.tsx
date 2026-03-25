import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, RefreshCw } from "lucide-react";

export function Status() {
    const [data, setData] = useState<unknown>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("/api/health");
            if (!res.ok) {
                setError(`HTTP ${res.status}`);
                setData(null);
                return;
            }
            setData(await res.json());
        } catch (e) {
            setData(null);
            setError(e instanceof Error ? e.message : "Request failed");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void load();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Server status</h2>
                    <p className="text-slate-400">
                        <code className="text-slate-300">GET /api/health</code> — Inkscape CLI, optional Ollama, API keys (no secrets shown).
                    </p>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void load()}
                    disabled={loading}
                    className="border-slate-800 text-slate-300"
                >
                    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader className="flex flex-row items-center gap-2">
                    <Activity className="h-5 w-5 text-emerald-500" />
                    <CardTitle className="text-white">Health JSON</CardTitle>
                </CardHeader>
                <CardContent>
                    {error ? (
                        <p className="text-yellow-400">{error}</p>
                    ) : (
                        <pre className="max-h-[70vh] overflow-auto rounded-lg border border-slate-800 bg-slate-900 p-4 text-xs text-slate-200">
                            {loading && !data ? "Loading…" : JSON.stringify(data, null, 2)}
                        </pre>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
