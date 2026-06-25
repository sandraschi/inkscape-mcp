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
  if (err) return <p className="text-yellow-400">Failed to load: {err}</p>;
  if (!md) return <p className="text-slate-400">Loading...</p>;
  return (
    <div className="max-w-none [&_h1]:text-xl [&_h1]:font-bold [&_h1]:text-white [&_h1]:mb-4 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_h2]:mt-8 [&_h2]:mb-3 [&_h2]:pb-1 [&_h2]:border-b [&_h2]:border-slate-700 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-slate-100 [&_h3]:mt-6 [&_h3]:mb-2 [&_p]:text-slate-200 [&_p]:text-base [&_p]:leading-relaxed [&_p]:mb-3 [&_ul]:text-slate-200 [&_ul]:space-y-1.5 [&_ul]:mb-4 [&_li>p]:mb-0 [&_ol]:text-slate-200 [&_ol]:space-y-1.5 [&_ol]:mb-4 [&_a]:text-blue-400 [&_a]:underline [&_a:hover]:text-blue-300 [&_code]:text-slate-100 [&_code]:bg-slate-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_pre]:bg-slate-900 [&_pre]:border [&_pre]:border-slate-700 [&_pre]:rounded-lg [&_pre]:p-4 [&_pre]:mb-4 [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_pre_code]:text-sm [&_pre_code]:text-slate-100 [&_strong]:text-white [&_strong]:font-semibold [&_table]:w-full [&_table]:text-slate-200 [&_table]:text-base [&_th]:text-left [&_th]:py-2.5 [&_th]:px-3 [&_th]:font-semibold [&_th]:text-slate-100 [&_th]:border-b [&_th]:border-slate-700 [&_td]:py-2.5 [&_td]:px-3 [&_td]:border-b [&_td]:border-slate-800 [&_tr:last-child>td]:border-b-0 [&_blockquote]:border-l-4 [&_blockquote]:border-blue-600 [&_blockquote]:pl-4 [&_blockquote]:py-1 [&_blockquote]:mb-4 [&_blockquote_p]:text-slate-300 [&_hr]:border-slate-700 [&_hr]:my-8">
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
