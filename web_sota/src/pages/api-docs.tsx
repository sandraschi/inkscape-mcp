import { Code2, ExternalLink } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import API_BASE from "@/lib/api";

const BACKEND_DOCS = `${API_BASE}/docs`;

export function ApiDocs() {
  const [view, setView] = useState<"swagger" | "redoc">("swagger");
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const injectDarkTheme = () => {
      try {
        const doc = iframeRef.current?.contentDocument;
        if (!doc) return;
        const style = doc.createElement("style");
        style.textContent = `
          :root { --bg: #0f172a; --text: #e2e8f0; }
          body { background: var(--bg); color: var(--text); }
        `;
        doc.head.appendChild(style);
      } catch {
        // cross-origin may block — safe to ignore
      }
    };
    const timer = setTimeout(injectDarkTheme, 1000);
    return () => clearTimeout(timer);
  }, [view]);

  return (
    <div className="space-y-6" data-testid="api-docs-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Code2 className="h-6 w-6 text-blue-400" />
          <h1 className="text-2xl font-bold text-slate-100">API Docs</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-slate-700 overflow-hidden">
            <button
              type="button"
              onClick={() => setView("swagger")}
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                view === "swagger"
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Swagger
            </button>
            <button
              type="button"
              onClick={() => setView("redoc")}
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                view === "redoc"
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              ReDoc
            </button>
          </div>
          <a
            href={`${BACKEND_DOCS}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-400 hover:text-white hover:border-slate-600 transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            Open in browser
          </a>
        </div>
      </div>

      <Card className="border-slate-800 bg-slate-900/50">
        <CardContent className="p-0">
          <iframe
            ref={iframeRef}
            src={view === "swagger" ? `${BACKEND_DOCS}` : `${API_BASE}/redoc`}
            className="h-[70vh] w-full rounded-lg"
            title="API Documentation"
          />
        </CardContent>
      </Card>
    </div>
  );
}
