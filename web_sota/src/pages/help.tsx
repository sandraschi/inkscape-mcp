import { BookOpen, Bug, Cpu, HelpCircle, Settings, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import API_BASE from "@/lib/api";

const TABS = [
  { id: "overview", label: "Overview", icon: BookOpen },
  { id: "inkscape", label: "Inkscape", icon: Wrench },
  { id: "tools", label: "Tools", icon: Cpu },
  { id: "config", label: "Configuration", icon: Settings },
  { id: "troubleshooting", label: "Troubleshooting", icon: Bug },
];

function Markdown({ path }: { path: string }) {
  const [md, setMd] = useState("");
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    setMd("");
    setErr(null);
    fetch(`${API_BASE}/api/docs/${path}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then(setMd)
      .catch((e) => setErr(e.message));
  }, [path]);
  if (err) return <p className="text-yellow-400 text-sm">Failed to load: {err}</p>;
  if (!md) return <p className="text-slate-500 text-sm">Loading...</p>;
  return (
    <div className="prose prose-invert max-w-none text-sm prose-headings:text-slate-100 prose-headings:font-semibold prose-h2:text-base prose-h2:mt-6 prose-h2:border-b prose-h2:border-slate-800 prose-h2:pb-1 prose-h3:text-sm prose-a:text-blue-400 prose-code:text-slate-200 prose-code:bg-slate-900 prose-code:px-1 prose-code:rounded prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-800 prose-li:text-slate-300 prose-strong:text-slate-200">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
    </div>
  );
}

export function Help() {
  const [tab, setTab] = useState("overview");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <HelpCircle className="h-6 w-6 text-blue-500" />
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Help</h2>
          <p className="text-sm text-slate-400">
            Documentation served from the <code className="text-xs text-slate-500">docs/</code> directory
          </p>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab} className="w-full">
        <TabsList className="w-full border-b border-slate-800 bg-transparent">
          {TABS.map((t) => (
            <TabsTrigger
              key={t.id}
              value={t.id}
              className="flex items-center gap-2 rounded-none border-b-2 border-transparent px-4 py-2.5 text-sm text-slate-400 transition-colors data-[state=active]:border-blue-500 data-[state=active]:text-slate-100"
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <Markdown path="README.md" />
        </TabsContent>
        <TabsContent value="inkscape" className="mt-6">
          <Markdown path="INKSCAPE.md" />
        </TabsContent>
        <TabsContent value="tools" className="mt-6">
          <Markdown path="TOOLS.md" />
        </TabsContent>
        <TabsContent value="config" className="mt-6">
          <Markdown path="CONFIGURATION.md" />
        </TabsContent>
        <TabsContent value="troubleshooting" className="mt-6">
          <Markdown path="TROUBLESHOOTING.md" />
        </TabsContent>
      </Tabs>
    </div>
  );
}
