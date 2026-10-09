import { BookOpen, Loader2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import API_BASE from "@/lib/api";

interface SkillInfo {
  name: string;
  description: string;
}

export function Skills() {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/skills`)
      .then((r) => r.json())
      .then((d) => {
        setSkills(d.skills ?? []);
        if (d.skills?.length > 0) setSelected(d.skills[0].name);
      })
      .catch(() => setSkills([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    fetch(`${API_BASE}/api/skills/${selected}`)
      .then((r) => r.json())
      .then((d) => setContent(d.content ?? ""))
      .catch(() => setContent(""))
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div className="space-y-6" data-testid="skills-page">
      <div className="flex items-center gap-3">
        <Sparkles className="h-6 w-6 text-blue-400" />
        <h1 className="text-2xl font-bold text-slate-100">Skills</h1>
      </div>

      <div className="flex gap-6">
        <div className="w-64 shrink-0 space-y-1">
          {skills.map((s) => (
            <button
              type="button"
              key={s.name}
              data-testid={`skill-select-${s.name}`}
              onClick={() => setSelected(s.name)}
              className={`w-full rounded-lg px-4 py-2.5 text-left text-sm font-medium transition-colors ${
                selected === s.name
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                {s.name}
              </div>
              <p className="mt-0.5 text-xs text-slate-500">{s.description}</p>
            </button>
          ))}
        </div>

        <Card className="flex-1 border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-slate-200 capitalize">
              {selected ?? "Skill"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
              </div>
            ) : (
              <div
                data-testid="skill-content"
                className="prose prose-invert prose-sm max-w-none text-slate-300"
              >
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
