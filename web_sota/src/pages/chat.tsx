import {
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Download,
  RefreshCw,
  Send,
  Settings2,
  Sparkles,
  StopCircle,
  User,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import API_BASE from "@/lib/api";
import {
  fetchLlmSettings,
  fetchProviders,
  loadSelection,
  type ProviderInfo,
  saveSelection,
  subscribeSelection,
} from "@/lib/llm";

type Role = "user" | "assistant";
type Personality = { id: string; name: string; prompt: string };
interface ToolResultEvent {
  tool: string;
  result: {
    success: boolean;
    tool: string;
    params: Record<string, unknown>;
    result?: string;
    error?: string;
    timing_ms: number;
  };
}
interface Message {
  role: Role;
  content: string;
  timestamp: number;
  toolCalls?: ToolCallCard[];
}
interface ToolCallCard {
  nl_name: string;
  tool: string;
  result: ToolResultEvent["result"] | null;
}

const PERSONALITIES: Personality[] = [
  {
    id: "expert",
    name: "SVG Expert",
    prompt:
      "You are a senior Inkscape/SVG engineer embedded in this MCP server. Answer concisely with practical commands, precise SVG attributes, and vector graphics best practices.\n\n" +
      "This server exposes real tools an agent can call - when a request maps to one, name the specific tool and operation instead of only describing generic GUI steps: " +
      "inkscape_file (load, save, convert, validate, list_formats), " +
      "inkscape_vector (60+ operations incl. trace_image, generate_barcode_qr, apply_boolean, path_simplify, path_clean, object_to_path, optimize_svg, scour_svg, render_preview, export_dxf, text_to_path), " +
      "inkscape_analysis (quality, statistics, dimensions, structure - read-only, call before mutating), " +
      "inkscape_layers (list, create, rename, hide, show, lock), " +
      "inkscape_animation (SMIL preset library, 100% client-side, no Inkscape needed), " +
      "inkscape_render (export_preview, export_multi_dpi, get_document_summary), " +
      "inkscape_validation (validate_svg, check_viewbox, audit_web_svg), " +
      "inkscape_system (status, diagnostics, version, config).",
  },
  {
    id: "artist",
    name: "Vector Artist",
    prompt:
      "You are an expert vector artist. Frame answers around composition, color theory, path precision, and artistic workflow in Inkscape.",
  },
  {
    id: "beginner",
    name: "Beginner",
    prompt:
      "You are a friendly Inkscape tutor. Explain concepts simply with step-by-step guidance, no jargon.",
  },
  {
    id: "custom",
    name: "Custom",
    prompt: "You are a helpful assistant specialized in Inkscape and SVG.",
  },
];

const DEFAULT_ENDPOINTS: Record<string, string> = {
  ollama: "http://127.0.0.1:11434",
  lmstudio: "http://127.0.0.1:1234",
};

function fmt(ts: number) {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("inkscape-chat") || "[]");
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [abort, setAbort] = useState<AbortController | null>(null);
  const [personality, setPersonality] = useState(
    () => localStorage.getItem("inkscape-chat-persona") || "expert",
  );
  // Shared selection (SETTINGS_LLM.md): backend-truth file + cross-tab sync,
  // never a hardcoded default model. AI Settings and Chat read/write the same
  // state, so switching providers there is reflected here without a reload.
  const [provider, setProvider] = useState(() => loadSelection().provider);
  const [model, setModel] = useState(() => loadSelection().model);
  const [endpoint, setEndpoint] = useState(
    () =>
      DEFAULT_ENDPOINTS[loadSelection().provider] ?? DEFAULT_ENDPOINTS.ollama,
  );
  const [showSettings, setShowSettings] = useState(false);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);
  const persona =
    PERSONALITIES.find((p) => p.id === personality) ?? PERSONALITIES[0];

  useEffect(() => {
    localStorage.setItem("inkscape-chat", JSON.stringify(messages.slice(-100)));
  }, [messages]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const refreshProviders = useCallback(async () => {
    setLoadingProviders(true);
    try {
      const { providers: list } = await fetchProviders();
      setProviders(list);
      const match = list.find((p) => p.id === provider);
      if (match) setEndpoint(match.base_url);
    } catch {
      // non-fatal
    } finally {
      setLoadingProviders(false);
    }
  }, [provider]);

  // Backend-truth reconciliation on mount (SETTINGS_LLM.md rule 2): the
  // localStorage mirror used for the initial state above may be stale if AI
  // Settings changed the selection while this page wasn't open.
  useEffect(() => {
    (async () => {
      try {
        const s = await fetchLlmSettings();
        if (s.provider) setProvider(s.provider);
        if (s.model !== undefined) setModel(s.model ?? "");
      } catch {
        // backend truth unavailable: localStorage mirror stands
      }
    })();
  }, []);

  useEffect(() => {
    if (!showSettings) return;
    void refreshProviders();
  }, [showSettings, refreshProviders]);

  // Live-sync: pick up a selection change made elsewhere (AI Settings, or
  // this same page in another tab) without a reload.
  useEffect(
    () =>
      subscribeSelection((sel) => {
        setProvider(sel.provider);
        setModel(sel.model);
      }),
    [],
  );

  const onProviderChange = useCallback(
    (next: string) => {
      // RULE: never auto-pick. Switching provider clears the model until
      // the user (or AI Settings) picks one explicitly.
      setProvider(next);
      setModel("");
      saveSelection(next, "");
      const match = providers.find((p) => p.id === next);
      setEndpoint(
        match?.base_url ?? DEFAULT_ENDPOINTS[next] ?? DEFAULT_ENDPOINTS.ollama,
      );
    },
    [providers],
  );

  const onModelChange = useCallback(
    (next: string) => {
      setModel(next);
      saveSelection(provider, next);
    },
    [provider],
  );

  const activeProvider = providers.find((p) => p.id === provider);
  const modelOptions = activeProvider?.models ?? [];

  const toggleCard = useCallback((idx: number) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || streaming) return;
    // SETTINGS_LLM.md rule 6: send-time guard. No fallback model, ever.
    if (!model) {
      setShowSettings(true);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Pick a model in Settings before chatting.",
          timestamp: Date.now(),
        },
      ]);
      return;
    }
    setInput("");
    const userMsg: Message = {
      role: "user",
      content: q,
      timestamp: Date.now(),
    };
    const botMsg: Message = {
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      toolCalls: [],
    };
    setMessages((prev) => [...prev, userMsg, botMsg]);
    setStreaming(true);
    const history = messages
      .slice(-20)
      .map((m) => ({ role: m.role, content: m.content }));
    const ctrl = new AbortController();
    setAbort(ctrl);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: q,
          provider,
          model,
          endpoint,
          stream: true,
          system_prompt: persona.prompt,
          history,
        }),
        signal: ctrl.signal,
      });
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");
      const dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: !done });
        const lines = buf.split("\n\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed?.startsWith("data: ")) continue;
          const raw = trimmed.slice(6);
          try {
            const event = JSON.parse(raw);
            if (event.type === "text") {
              setMessages((prev) => {
                const c = [...prev];
                const l = c[c.length - 1];
                if (l?.role === "assistant")
                  c[c.length - 1] = {
                    ...l,
                    content: l.content + event.content,
                  };
                return c;
              });
            } else if (event.type === "tool_call") {
              setMessages((prev) => {
                const c = [...prev];
                const l = c[c.length - 1];
                if (l?.role === "assistant" && l.toolCalls)
                  l.toolCalls = [
                    ...l.toolCalls,
                    { nl_name: event.nl_name, tool: event.tool, result: null },
                  ];
                return c;
              });
            } else if (event.type === "tool_result") {
              setMessages((prev) => {
                const c = [...prev];
                const l = c[c.length - 1];
                if (l?.role === "assistant" && l.toolCalls) {
                  const i = l.toolCalls.findIndex(
                    (tc) => tc.tool === event.tool && tc.result === null,
                  );
                  if (i >= 0)
                    l.toolCalls[i] = {
                      ...l.toolCalls[i],
                      result: event.result,
                    };
                }
                return c;
              });
            } else if (event.type === "done") {
              break;
            }
          } catch {
            // skip malformed
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== "AbortError") {
        setMessages((prev) => {
          const c = [...prev];
          const l = c[c.length - 1];
          if (l?.role === "assistant")
            c[c.length - 1] = {
              ...l,
              content: l.content || `Error: ${e.message}`,
            };
          return c;
        });
      }
    } finally {
      setStreaming(false);
      setAbort(null);
    }
  }, [
    input,
    streaming,
    messages,
    provider,
    model,
    endpoint,
    personality,
    persona,
  ]);

  const stop = () => {
    abort?.abort();
    setStreaming(false);
  };

  const exportChat = (fmt: "md" | "json") => {
    const c =
      fmt === "json"
        ? JSON.stringify(messages, null, 2)
        : messages
            .map(
              (m) =>
                `### ${m.role === "user" ? "User" : persona.name}\n${m.content}\n`,
            )
            .join("\n");
    const b = new Blob([c], { type: "text/plain" });
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u;
    a.download = `inkscape-chat.${fmt}`;
    a.click();
    URL.revokeObjectURL(u);
  };

  const suggested = [
    "Create a shield with two lions rampant",
    "Convert this path to a smooth bezier curve",
    "How do I use the trace bitmap feature?",
    "Generate an SVG icon of a gear",
    "Explain the difference between fill and stroke",
    "How to set up a 3D isometric grid?",
  ];

  return (
    <div
      className="flex h-[calc(100vh-8rem)] flex-col space-y-3"
      data-testid="chat-page"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight text-white">
            AI Vector Chat
          </h2>
          <div
            className="flex gap-1 bg-slate-900 rounded-lg p-1 border border-slate-800"
            data-testid="personality-select"
          >
            {PERSONALITIES.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setPersonality(p.id);
                  localStorage.setItem("inkscape-chat-persona", p.id);
                }}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${personality === p.id ? "bg-blue-600 text-white" : "text-slate-300 hover:text-white"}`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            className="p-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-800"
            title="Settings"
          >
            <Settings2 className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-export"
            onClick={() => exportChat("md")}
            className="p-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-800"
            title="Export MD"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-clear"
            onClick={() => {
              setMessages([]);
              localStorage.removeItem("inkscape-chat");
            }}
            className="text-sm text-slate-300 hover:text-white px-2 py-1 rounded-md hover:bg-slate-800"
          >
            Clear
          </button>
        </div>
      </div>

      {showSettings && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 flex flex-wrap gap-3 items-center text-sm">
          <div>
            <label
              htmlFor="chat-provider"
              className="text-sm text-slate-400 block"
            >
              Provider
            </label>
            <div className="relative">
              <select
                id="chat-provider"
                value={provider}
                onChange={(e) => onProviderChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm min-w-[9rem] appearance-none pr-6"
              >
                {providers.length === 0 ? (
                  <option value="ollama">Ollama</option>
                ) : (
                  providers.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label}
                    </option>
                  ))
                )}
              </select>
              {activeProvider && (
                <span
                  className={`absolute right-1.5 top-1/2 -translate-y-1/2 h-2 w-2 rounded-full ${(activeProvider.kind === "local" ? activeProvider.detected : activeProvider.configured) ? "bg-green-500" : "bg-red-500"}`}
                />
              )}
            </div>
          </div>
          {modelOptions.length > 0 && (
            <div>
              <label
                htmlFor="chat-model-select"
                className="text-sm text-slate-400 block"
              >
                Model
              </label>
              <select
                id="chat-model-select"
                value={model}
                onChange={(e) => onModelChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm min-w-[9rem]"
              >
                {modelOptions.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          )}
          {modelOptions.length === 0 && (
            <div>
              <label
                htmlFor="chat-model-input"
                className="text-sm text-slate-400 block"
              >
                Model
              </label>
              <input
                id="chat-model-input"
                value={model}
                onChange={(e) => onModelChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm w-28 font-mono"
              />
            </div>
          )}
          <div>
            <label
              htmlFor="chat-endpoint"
              className="text-sm text-slate-400 block"
            >
              Endpoint
            </label>
            <input
              id="chat-endpoint"
              value={endpoint}
              onChange={(e) => {
                setEndpoint(e.target.value);
                localStorage.setItem("inkscape-chat-endpoint", e.target.value);
              }}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm w-44 font-mono"
            />
          </div>
          <button
            type="button"
            onClick={refreshProviders}
            disabled={loadingProviders}
            className="mt-4 p-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 self-end"
          >
            <RefreshCw
              className={`h-4 w-4 ${loadingProviders ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      )}

      <div
        className="flex-1 overflow-y-auto space-y-3 pr-1"
        data-testid="chat-messages"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <Bot className="h-12 w-12 text-slate-700" />
            <p className="text-slate-400 text-sm max-w-md">
              Ask me about Inkscape — SVG creation, paths, layers, effects, or
              vector design workflows.
            </p>
            <div
              className="flex flex-wrap gap-2 justify-center"
              data-testid="example-prompts"
            >
              {suggested.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setInput(p)}
                  className="px-3 py-1.5 text-sm bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 rounded-lg border border-slate-700/50"
                >
                  <Sparkles className="h-3 w-3 inline mr-1 text-blue-400" />
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              // biome-ignore lint/suspicious/noArrayIndexKey: append-only chat log, never reordered
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {msg.role !== "user" && (
                <div className="h-8 w-8 rounded-full bg-blue-900/50 flex items-center justify-center border border-blue-800/50 shrink-0">
                  <Bot className="h-4 w-4 text-blue-400" />
                </div>
              )}
              <div
                className={`max-w-[80%] space-y-1 ${msg.role === "user" ? "items-end" : ""}`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">
                    {msg.role === "user" ? "You" : persona.name}
                  </span>
                  <span className="text-sm text-slate-600">
                    {fmt(msg.timestamp)}
                  </span>
                </div>
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="space-y-2 mb-2">
                    {msg.toolCalls.map((tc, j) => (
                      <div
                        // biome-ignore lint/suspicious/noArrayIndexKey: append-only per-message list, never reordered
                        key={j}
                        className="bg-slate-900/80 border border-slate-700/60 rounded-lg overflow-hidden text-sm"
                      >
                        <button
                          type="button"
                          onClick={() => toggleCard(i * 100 + j)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-800/50"
                        >
                          {expandedCards.has(i * 100 + j) ? (
                            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-300" />
                          ) : (
                            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-300" />
                          )}
                          {tc.result ? (
                            tc.result.success ? (
                              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-green-500" />
                            ) : (
                              <XCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                            )
                          ) : (
                            <span className="h-3.5 w-3.5 shrink-0 rounded-full bg-blue-500/50 animate-pulse" />
                          )}
                          <span className="text-slate-200 font-medium">
                            {tc.nl_name}
                          </span>
                          {tc.result && (
                            <span className="text-slate-400 ml-auto">
                              {tc.result.timing_ms}ms
                            </span>
                          )}
                        </button>
                        {expandedCards.has(i * 100 + j) && tc.result && (
                          <div className="px-3 pb-2 space-y-1.5 text-slate-300 font-mono border-t border-slate-800 pt-1.5">
                            <div>
                              <span className="text-slate-400">tool: </span>
                              {tc.result.tool}
                            </div>
                            <div>
                              <span className="text-slate-400">params: </span>
                              {JSON.stringify(tc.result.params)}
                            </div>
                            <div>
                              <span className="text-slate-400">timing: </span>
                              {tc.result.timing_ms}ms
                            </div>
                            {tc.result.success ? (
                              <div className="text-emerald-400/80 break-all max-h-32 overflow-y-auto bg-slate-950/50 rounded p-1.5">
                                {tc.result.result?.slice(0, 1000)}
                              </div>
                            ) : (
                              <div className="text-red-400/80">
                                {tc.result.error}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                <div
                  className={`text-sm rounded-xl px-4 py-2.5 ${msg.role === "user" ? "bg-blue-600/20 text-blue-100 border border-blue-700/30" : "bg-slate-800/60 text-slate-200 border border-slate-700/50"}`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    {msg.content ||
                      (i === messages.length - 1 && streaming ? (
                        <span className="animate-pulse">...</span>
                      ) : (
                        ""
                      ))}
                  </div>
                </div>
              </div>
              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 shrink-0">
                  <User className="h-4 w-4 text-slate-300" />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 items-end bg-slate-900/80 border border-slate-800 rounded-xl p-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask about Inkscape or SVG..."
          rows={1}
          data-testid="chat-input"
          className="flex-1 bg-transparent border-0 outline-none text-sm text-slate-200 placeholder-slate-500 resize-none max-h-32 py-1.5 px-2"
        />
        {streaming ? (
          <button
            type="button"
            onClick={stop}
            className="p-2 rounded-lg bg-red-600/20 hover:bg-red-600/40 text-red-400"
          >
            <StopCircle className="h-5 w-5" />
          </button>
        ) : (
          <button
            type="button"
            data-testid="chat-send"
            onClick={send}
            disabled={!input.trim()}
            className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white"
          >
            <Send className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}
