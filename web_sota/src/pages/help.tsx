import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, ExternalLink, RefreshCw } from "lucide-react";

interface HelpPayload {
    title?: string;
    summary?: string;
    tools?: string[];
    http_ports?: Record<string, number>;
    env?: Record<string, string>;
    links?: Array<{ label: string; url?: string; path?: string }>;
}

export function Help() {
    const [data, setData] = useState<HelpPayload | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        setError(null);
        try {
            const res = await fetch("/api/help");
            if (!res.ok) {
                setError(`HTTP ${res.status}`);
                setData(null);
                return;
            }
            setData(await res.json());
        } catch (e) {
            setData(null);
            setError(e instanceof Error ? e.message : "Failed to load help");
        }
    };

    useEffect(() => {
        void load();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Help</h2>
                    <p className="text-slate-400">
                        Served from <code className="text-slate-300">GET /api/help</code> on the MCP HTTP listener.
                    </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void load()} className="border-slate-800 text-slate-300">
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            {error ? (
                <p className="text-yellow-400">{error}</p>
            ) : !data ? (
                <p className="text-slate-500">Loading…</p>
            ) : (
                <div className="space-y-4">
                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-white">
                                <BookOpen className="h-5 w-5 text-blue-400" />
                                {data.title}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 text-slate-300">
                            <p className="leading-relaxed">{data.summary}</p>
                            {data.tools && (
                                <div>
                                    <h3 className="mb-2 font-semibold text-white">MCP tools</h3>
                                    <ul className="list-inside list-disc space-y-1 text-sm">
                                        {data.tools.map((t) => (
                                            <li key={t}>{t}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {data.http_ports && (
                                <div>
                                    <h3 className="mb-2 font-semibold text-white">Ports (fleet layout)</h3>
                                    <ul className="font-mono text-sm text-slate-400">
                                        {Object.entries(data.http_ports).map(([k, v]) => (
                                            <li key={k}>
                                                {k}: {v}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {data.env && (
                                <div>
                                    <h3 className="mb-2 font-semibold text-white">Environment (overview)</h3>
                                    <ul className="space-y-1 text-sm text-slate-400">
                                        {Object.entries(data.env).map(([k, v]) => (
                                            <li key={k}>
                                                <code className="text-slate-300">{k}</code> — {v}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {data.links && data.links.length > 0 && (
                                <div className="flex flex-wrap gap-3 pt-2">
                                    {data.links.map((l) =>
                                        l.url ? (
                                            <a
                                                key={l.label}
                                                href={l.url}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="inline-flex items-center gap-1 text-sm text-blue-400 hover:underline"
                                            >
                                                {l.label}
                                                <ExternalLink className="h-3 w-3" />
                                            </a>
                                        ) : (
                                            <span key={l.label} className="text-sm text-slate-500">
                                                {l.label}
                                                {l.path ? ` (${l.path})` : ""}
                                            </span>
                                        ),
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
