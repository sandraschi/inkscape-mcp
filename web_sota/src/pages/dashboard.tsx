import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { Activity, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HealthPayload {
    status?: string;
    server?: string;
    version?: string;
    providers?: {
        ollama?: { available?: boolean };
        inkscape?: { available?: boolean; version_line?: string | null };
    };
}

export function Dashboard() {
    const [h, setH] = useState<HealthPayload | null>(null);
    const [err, setErr] = useState<string | null>(null);

    const load = async () => {
        setErr(null);
        try {
            const res = await fetch("/api/health");
            if (!res.ok) {
                setErr(`HTTP ${res.status}`);
                setH(null);
                return;
            }
            setH(await res.json());
        } catch (e) {
            setH(null);
            setErr(e instanceof Error ? e.message : "Failed");
        }
    };

    useEffect(() => {
        void load();
    }, []);

    const inkOk = h?.providers?.inkscape?.available;
    const ollOk = h?.providers?.ollama?.available;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Overview</h2>
                    <p className="text-slate-400">Quick snapshot from GET /api/health. Details on the Status page.</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void load()} className="border-slate-800 text-slate-300">
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            {err && <p className="text-yellow-400">{err}</p>}

            <div className="grid gap-4 md:grid-cols-3">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Server</CardTitle>
                        <Activity className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-lg font-semibold text-white">{h?.server ?? "—"}</div>
                        <p className="text-xs text-slate-400">{h?.version ?? ""}</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Inkscape CLI</CardTitle>
                        {inkOk ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-red-400" />}
                    </CardHeader>
                    <CardContent>
                        <div className="text-lg font-semibold text-white">{inkOk ? "Available" : "Not found"}</div>
                        <p className="truncate text-xs text-slate-400">{h?.providers?.inkscape?.version_line ?? ""}</p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Ollama (optional)</CardTitle>
                        {ollOk ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-slate-500" />}
                    </CardHeader>
                    <CardContent>
                        <div className="text-lg font-semibold text-white">{ollOk ? "Reachable" : "Off / unreachable"}</div>
                        <p className="text-xs text-slate-400">Only needed for /api/generate-svg</p>
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
