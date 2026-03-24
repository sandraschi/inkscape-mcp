import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LogEntry {
    timestamp: string;
    level: "INFO" | "WARN" | "ERROR" | "DEBUG";
    message: string;
}

export function Logs() {
    const [logs, setLogs] = useState<LogEntry[]>([]);

    useEffect(() => {
        // Sync logs from the FastMCP bridge (simulated for now)
        const initialLogs: LogEntry[] = [
            { timestamp: new Date().toISOString(), level: "INFO", message: "Inkscape-MCP Server started on port 10842" },
            { timestamp: new Date().toISOString(), level: "INFO", message: "FastMCP bridge connected on port 8000" },
            { timestamp: new Date().toISOString(), level: "WARN", message: "Inkscape 1.0 found, 1.2+ recommended for full Actions support" },
        ];
        setLogs(initialLogs);
    }, []);

    const clearLogs = () => setLogs([]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">System Logs</h2>
                    <p className="text-slate-400">Real-time monitoring of Inkscape operations and bridge activity</p>
                </div>
                <Button variant="outline" size="sm" onClick={clearLogs} className="border-slate-800 text-slate-300">
                    Clear Logs
                </Button>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader className="flex flex-row items-center gap-2 space-y-0">
                    <Terminal className="h-5 w-5 text-blue-500" />
                    <CardTitle className="text-white">Live Stream</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[500px] overflow-y-auto rounded-lg border border-slate-800 bg-slate-900 p-4 font-mono text-sm">
                        {logs.length === 0 ? (
                            <div className="flex h-full items-center justify-center text-slate-500">
                                No active logs...
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {logs.map((log, i) => (
                                    <div key={i} className="grid grid-cols-[180px_60px_1fr] gap-4">
                                        <span className="text-slate-500">{log.timestamp.split('T')[1].split('.')[0]}</span>
                                        <span className={cn(
                                            "font-bold",
                                            log.level === "ERROR" ? "text-red-500" :
                                                log.level === "WARN" ? "text-yellow-500" :
                                                    log.level === "INFO" ? "text-blue-500" : "text-slate-400"
                                        )}>
                                            {log.level}
                                        </span>
                                        <span className="text-slate-300">{log.message}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

function cn(...classes: string[]) {
    return classes.filter(Boolean).join(' ');
}
