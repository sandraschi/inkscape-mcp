import { useState, useEffect, useRef } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
}

interface LogsResponse {
    logs: LogEntry[];
    total?: number;
}

export function Logs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [paused, setPaused] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        if (paused) return;
        try {
            const res = await fetch("/api/logs?limit=500");
            if (!res.ok) {
                setError(`HTTP ${res.status} from /api/logs`);
                return;
            }
            setError(null);
            const data = (await res.json()) as LogsResponse;
            setLogs(data.logs ?? []);
        } catch (e) {
            setError(
                e instanceof Error
                    ? e.message
                    : "Could not reach /api/logs. Start the MCP server with HTTP on port 10847 and use Vite (10846) so /api proxies correctly.",
            );
        }
    };

    useEffect(() => {
        void fetchLogs();
        const id = window.setInterval(() => void fetchLogs(), 2000);
        return () => window.clearInterval(id);
    }, [paused]);

    useEffect(() => {
        if (!paused) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs, paused]);

    const clearRemote = async () => {
        try {
            await fetch("/api/logs", { method: "DELETE" });
            setLogs([]);
        } catch {
            setLogs([]);
        }
    };

    const levelClass = (level: string) => {
        const u = level.toUpperCase();
        if (u === "ERROR") return "text-red-500";
        if (u === "WARN" || u === "WARNING") return "text-yellow-500";
        if (u === "INFO") return "text-blue-500";
        return "text-slate-400";
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Server logs</h2>
                    <p className="text-slate-400">
                        Live tail from <code className="text-slate-300">GET /api/logs</code> (in-memory ring on the MCP process). Pauses polling when
                        checked.
                    </p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <label className="flex items-center gap-2 text-sm text-slate-400">
                        <input type="checkbox" checked={paused} onChange={(e) => setPaused(e.target.checked)} />
                        Pause
                    </label>
                    <Button variant="outline" size="sm" onClick={() => void fetchLogs()} className="border-slate-800 text-slate-300">
                        Refresh
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => void clearRemote()} className="border-slate-800 text-slate-300">
                        Clear buffer
                    </Button>
                </div>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader className="flex flex-row items-center gap-2 space-y-0">
                    <Terminal className="h-5 w-5 text-blue-500" />
                    <CardTitle className="text-white">Log stream</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[500px] overflow-y-auto rounded-lg border border-slate-800 bg-slate-900 p-4 font-mono text-sm">
                        {error ? (
                            <div className="text-yellow-400">{error}</div>
                        ) : logs.length === 0 ? (
                            <div className="flex h-full items-center justify-center text-slate-500">
                                No log lines yet (or buffer empty). Trigger MCP/REST activity to populate.
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {logs.map((log, i) => (
                                    <div key={`${log.timestamp}-${i}`} className="grid grid-cols-[180px_70px_1fr] gap-4">
                                        <span className="text-slate-500">
                                            {log.timestamp.includes("T") ? log.timestamp.split("T")[1].split(".")[0] : log.timestamp}
                                        </span>
                                        <span className={`font-bold ${levelClass(log.level)}`}>{log.level}</span>
                                        <span className="text-slate-300 break-all">{log.message}</span>
                                    </div>
                                ))}
                                <div ref={bottomRef} />
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
