import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, MessageSquare } from "lucide-react";

interface Msg {
    role: "user" | "assistant";
    text: string;
}

export function Chat() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<Msg[]>([
        {
            role: "assistant",
            text: "This panel sends a note to POST /api/chat. It does not run a local LLM. Use the MCP server from Cursor or Claude for real tool calls.",
        },
    ]);
    const [loading, setLoading] = useState(false);

    const send = async () => {
        const text = input.trim();
        if (!text || loading) return;
        setInput("");
        setMessages((m) => [...m, { role: "user", text }]);
        setLoading(true);
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text }),
            });
            const data = (await res.json()) as { reply?: string; echo?: string };
            if (!res.ok) {
                setMessages((m) => [...m, { role: "assistant", text: `Error: HTTP ${res.status}` }]);
                return;
            }
            setMessages((m) => [...m, { role: "assistant", text: data.reply ?? JSON.stringify(data) }]);
        } catch (e) {
            setMessages((m) => [
                ...m,
                { role: "assistant", text: e instanceof Error ? e.message : "Request failed" },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Notes to server</h2>
                <p className="text-slate-400">
                    Not a local LLM chat. Messages call <code className="text-slate-300">POST /api/chat</code> and log server-side. For vector work, use MCP
                    in your IDE.
                </p>
            </div>

            <Card className="flex flex-1 flex-col overflow-hidden border-slate-800 bg-slate-950/50">
                <CardContent className="flex flex-1 flex-col overflow-hidden p-0">
                    <div className="flex-1 space-y-4 overflow-y-auto p-4">
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`max-w-[85%] rounded-lg border px-4 py-2 text-sm ${
                                        msg.role === "user"
                                            ? "border-blue-800 bg-blue-950/40 text-slate-200"
                                            : "border-slate-700 bg-slate-900/80 text-slate-300"
                                    }`}
                                >
                                    {msg.role === "assistant" && (
                                        <MessageSquare className="mb-1 inline h-4 w-4 text-slate-500" />
                                    )}
                                    <p className="whitespace-pre-wrap">{msg.text}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="border-t border-slate-800 bg-slate-900/30 p-4">
                        <div className="flex gap-2">
                            <textarea
                                className="min-h-[44px] flex-1 resize-y rounded-md border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                placeholder="Optional note (logged; no local model)…"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        void send();
                                    }
                                }}
                                rows={2}
                            />
                            <Button size="icon" className="shrink-0 bg-blue-600 hover:bg-blue-700" onClick={() => void send()} disabled={loading}>
                                <Send className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
