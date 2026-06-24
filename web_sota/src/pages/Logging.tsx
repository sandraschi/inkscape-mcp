import { useCallback, useEffect, useRef, useState } from "react";
import API_BASE from "@/lib/api";

type LogEntry = {
  id: string;
  timestamp: string;
  level: string;
  kind: string;
  detail: string;
  meta: Record<string, any>;
};

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"];
const KINDS = ["", "tool_call", "server", "export"];
const LEVEL_COLORS: Record<string, string> = {
  ERROR: "text-red-400 bg-red-950/40",
  WARNING: "text-yellow-400 bg-yellow-950/40",
  INFO: "text-blue-300 bg-blue-950/30",
  DEBUG: "text-slate-500 bg-slate-900/30",
};

export default function Logging() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [level, setLevel] = useState("");
  const [kind, setKind] = useState("");
  const [search, setSearch] = useState("");
  const [sort, _setSort] = useState("desc");
  const [tail, setTail] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showClear, setShowClear] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [userScrolled, setUserScrolled] = useState(false);
  const afterIdRef = useRef<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchLogs = useCallback(
    async (opts: { tail?: boolean; after_id?: string } = {}) => {
      setLoading(true);
      const params = new URLSearchParams();
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      params.set("sort", sort);
      if (level) params.set("level", level);
      if (kind) params.set("kind", kind);
      if (search) params.set("search", search);
      if (opts.after_id) params.set("after_id", opts.after_id);
      try {
        const r = await fetch(`${API_BASE}/api/logs?${params}`);
        const d = await r.json();
        if (opts.tail && opts.after_id) {
          setEntries((prev) => [...prev, ...d.entries].slice(-200));
        } else {
          setEntries(d.entries);
        }
        setTotal(d.total);
        if (d.entries.length > 0) {
          afterIdRef.current = d.entries[d.entries.length - 1].id;
        }
      } catch (e) {
        console.error("Log fetch failed", e);
      } finally {
        setLoading(false);
      }
    },
    [limit, offset, level, kind, search, sort],
  );

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Tail polling
  useEffect(() => {
    if (!tail) return;
    const iv = setInterval(() => {
      if (afterIdRef.current) {
        fetchLogs({ tail: true, after_id: afterIdRef.current });
      } else {
        fetchLogs({ tail: true });
      }
    }, 2000);
    return () => clearInterval(iv);
  }, [tail, fetchLogs]);

  // Auto-scroll
  useEffect(() => {
    if (tail && !userScrolled && endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [entries, tail, userScrolled]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 50;
    setUserScrolled(!atBottom);
  };

  const handleSearch = (val: string) => {
    setSearch(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setSearch(val), 300);
  };

  const handleExport = async (fmt: string) => {
    const params = new URLSearchParams();
    params.set("format", fmt);
    if (level) params.set("level", level);
    if (kind) params.set("kind", kind);
    if (search) params.set("search", search);
    const r = await fetch(`${API_BASE}/api/logs/export?${params}`);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `logs.${fmt}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = async () => {
    await fetch(`${API_BASE}/api/logs`, { method: "DELETE" });
    setShowClear(false);
    setEntries([]);
    setTotal(0);
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="space-y-4">
      {/* Controls bar */}
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-bold text-slate-200 mr-2">Logs</h2>

        <select
          className="h-8 rounded border border-slate-700 bg-slate-800 px-2 text-xs text-slate-300"
          value={level}
          onChange={(e) => {
            setLevel(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">All levels</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>

        <select
          className="h-8 rounded border border-slate-700 bg-slate-800 px-2 text-xs text-slate-300"
          value={kind}
          onChange={(e) => {
            setKind(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">All kinds</option>
          {KINDS.filter(Boolean).map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>

        <input
          className="h-8 w-48 rounded border border-slate-700 bg-slate-800 px-2 text-xs text-slate-300 placeholder:text-slate-500"
          placeholder="Search..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
        />

        <select
          className="h-8 rounded border border-slate-700 bg-slate-800 px-2 text-xs text-slate-300"
          value={limit}
          onChange={(e) => {
            setLimit(Number(e.target.value));
            setOffset(0);
          }}
        >
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
          <option value="200">200</option>
        </select>

        <button
          className={`h-8 rounded px-3 text-xs font-medium ${tail ? "bg-emerald-600 text-white" : "border border-slate-700 text-slate-400 hover:bg-slate-800"}`}
          onClick={() => setTail(!tail)}
        >
          {tail ? "LIVE" : "Tail"}
        </button>

        <button
          className="h-8 rounded border border-slate-700 px-3 text-xs text-slate-400 hover:bg-slate-800"
          onClick={() => handleExport("json")}
        >
          JSON
        </button>
        <button
          className="h-8 rounded border border-slate-700 px-3 text-xs text-slate-400 hover:bg-slate-800"
          onClick={() => handleExport("csv")}
        >
          CSV
        </button>

        <button
          className="h-8 rounded border border-red-800 px-3 text-xs text-red-400 hover:bg-red-950/30"
          onClick={() => setShowClear(true)}
        >
          Clear
        </button>

        <span className="text-xs text-slate-500 ml-auto">{total} entries</span>
      </div>

      {/* Log stream */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-[65vh] overflow-auto rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-xs leading-relaxed"
      >
        {entries.length === 0 && !loading && (
          <div className="text-slate-600 text-center py-12">No log entries</div>
        )}
        {entries.map((e) => (
          <div
            key={e.id}
            className="flex gap-3 py-0.5 hover:bg-slate-900/50 rounded px-1"
          >
            <span className="text-slate-600 w-20 shrink-0">
              {e.timestamp.split(".")[0].split("T")[1] || e.timestamp}
            </span>
            <span
              className={`w-16 shrink-0 text-center rounded text-[10px] font-bold ${LEVEL_COLORS[e.level] || "text-slate-400"}`}
            >
              {e.level}
            </span>
            {e.kind && (
              <span className="text-slate-500 w-16 shrink-0">[{e.kind}]</span>
            )}
            <span className="text-slate-300 break-all">{e.detail}</span>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <button
          className="px-3 py-1 rounded border border-slate-700 hover:bg-slate-800 disabled:opacity-30"
          disabled={offset <= 0}
          onClick={() => setOffset(Math.max(0, offset - limit))}
        >
          Prev
        </button>
        <span>
          Page {currentPage} of {totalPages || 1}
        </span>
        <button
          className="px-3 py-1 rounded border border-slate-700 hover:bg-slate-800 disabled:opacity-30"
          disabled={offset + limit >= total}
          onClick={() => setOffset(offset + limit)}
        >
          Next
        </button>
      </div>

      {/* Clear confirmation */}
      {showClear && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
          onClick={() => setShowClear(false)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-slate-200 mb-2">
              Clear all logs?
            </h3>
            <p className="text-sm text-slate-400 mb-4">
              This cannot be undone. The ring buffer will be emptied.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                className="px-4 py-2 rounded border border-slate-700 text-slate-400 text-sm hover:bg-slate-800"
                onClick={() => setShowClear(false)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded bg-red-700 text-white text-sm hover:bg-red-600"
                onClick={handleClear}
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
