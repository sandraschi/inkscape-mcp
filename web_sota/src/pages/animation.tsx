import { Download, Eye, Play, Sparkles } from "lucide-react";
import { useCallback, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Preset {
  id: string;
  label: string;
  icon: string;
  desc: string;
}

const PRESETS: Preset[] = [
  { id: "bounce", label: "Bounce", icon: "↕", desc: "Bouncing motion" },
  { id: "fade_in", label: "Fade In", icon: "◐", desc: "Fade from transparent" },
  { id: "fade_out", label: "Fade Out", icon: "◑", desc: "Fade to transparent" },
  { id: "slide", label: "Slide In", icon: "→", desc: "Slide from left" },
  { id: "rotate", label: "Rotate", icon: "↻", desc: "Continuous rotation" },
  { id: "pulse", label: "Pulse", icon: "⊙", desc: "Size pulsing" },
  { id: "shake", label: "Shake", icon: "≈", desc: "Vibration shake" },
];

function buildSvg(presetId: string, dur: number, fill: string, size: number, shape: string): string {
  const cx = 200, cy = 200, r = size;
  const w = 400, h = 400;
  switch (presetId) {
    case "bounce": {
      const rise = cy - r * 4;
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><${shape} cx="${cx}" cy="${cy}" r="${r}" fill="${fill}"><animate attributeName="cy" values="${cy};${rise};${cy}" dur="${dur}s" repeatCount="indefinite" calcMode="spline" keySplines="0.33 0 0.66 1;0.33 0 0.66 1" keyTimes="0;0.5;1"/></${shape}></svg>`;
    }
    case "fade_in":
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><rect x="50" y="50" width="${w - 100}" height="${h - 100}" rx="10" fill="${fill}"><animate attributeName="opacity" values="0;1" dur="${dur}s" fill="freeze"/></rect></svg>`;
    case "fade_out":
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><rect x="50" y="50" width="${w - 100}" height="${h - 100}" rx="10" fill="${fill}"><animate attributeName="opacity" values="1;0" dur="${dur}s" fill="freeze"/></rect></svg>`;
    case "slide":
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><${shape} cx="${cx}" cy="${cy}" r="${r}" fill="${fill}"><animate attributeName="cx" values="${r};${cx}" dur="${dur}s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1"/></${shape}></svg>`;
    case "rotate":
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><g><animateTransform attributeName="transform" type="rotate" from="0 ${cx} ${cy}" to="360 ${cx} ${cy}" dur="${dur}s" repeatCount="indefinite"/><${shape} cx="${cx}" cy="${cy}" r="${r}" fill="${fill}"/></g></svg>`;
    case "pulse":
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><${shape} cx="${cx}" cy="${cy}" r="${r}" fill="${fill}"><animate attributeName="r" values="${r};${r * 1.5};${r}" dur="${dur}s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0.6;1" dur="${dur}s" repeatCount="indefinite"/></${shape}></svg>`;
    case "shake": {
      const amp = r * 0.3;
      const vals = Array.from({ length: 16 }, (_, i) => `${cx + amp * Math.sin(i * Math.PI / 4)}`).join(";");
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/><${shape} cx="${cx}" cy="${cy}" r="${r}" fill="${fill}"><animate attributeName="cx" values="${cx};${vals}" dur="${dur}s" repeatCount="indefinite"/></${shape}></svg>`;
    }
    default:
      return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="#1e293b"/></svg>`;
  }
}

export function AnimationStudio() {
  const [presetId, setPresetId] = useState("bounce");
  const [duration, setDuration] = useState("2");
  const [color, setColor] = useState("#4488ff");
  const [size, setSize] = useState("50");
  const [shape, setShape] = useState("circle");
  const svgRef = useRef<HTMLImageElement>(null);
  const [, setKey] = useState(0);

  const svgContent = useMemo(
    () => buildSvg(presetId, parseFloat(duration) || 2, color, parseInt(size) || 50, shape),
    [presetId, duration, color, size, shape],
  );

  const svgBlob = useMemo(() => {
    const blob = new Blob([svgContent], { type: "image/svg+xml" });
    return URL.createObjectURL(blob);
  }, [svgContent]);

  const refresh = useCallback(() => setKey((k) => k + 1), []);
  const download = useCallback(() => {
    const a = document.createElement("a");
    a.href = svgBlob;
    a.download = `animation_${presetId}.svg`;
    a.click();
  }, [svgBlob, presetId]);

  const preset = PRESETS.find((p) => p.id === presetId);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <Sparkles className="h-6 w-6 text-purple-500" />
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Animation Studio</h1>
          <p className="text-sm text-slate-400">
            Generate SVG animations with SMIL presets — no Inkscape needed
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Preview */}
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-slate-200">
              <Eye className="h-4 w-4 text-purple-400" /> Preview
            </CardTitle>
            <CardDescription className="text-xs">
              {preset?.label || "Animation preview"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center rounded-lg border border-slate-800 bg-slate-950">
              <img
                ref={svgRef}
                src={svgBlob}
                alt="Animation preview"
                className="h-auto max-w-full"
                onLoad={refresh}
              />
            </div>
            <div className="mt-4 flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={refresh}
                className="border-slate-800 text-slate-300"
              >
                <Play className="mr-1 h-3 w-3" /> Restart
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={download}
                className="border-slate-800 text-slate-300"
              >
                <Download className="mr-1 h-3 w-3" /> Download SVG
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Controls */}
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-slate-200">
              <Play className="h-4 w-4 text-purple-400" /> Controls
            </CardTitle>
            <CardDescription className="text-xs">
              Configure animation parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs text-slate-400">Preset</Label>
              <Select value={presetId} onValueChange={setPresetId}>
                <SelectTrigger className="border-slate-800 bg-slate-900 text-sm text-slate-200">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-slate-800 bg-slate-950">
                  {PRESETS.map((p) => (
                    <SelectItem key={p.id} value={p.id} className="text-slate-200">
                      <span className="mr-2">{p.icon}</span> {p.label} — {p.desc}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-xs text-slate-400">Duration (seconds)</Label>
              <Input
                type="number"
                min="0.5"
                max="10"
                step="0.5"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="border-slate-800 bg-slate-900 text-slate-200"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-xs text-slate-400">Color</Label>
              <div className="flex gap-2">
                <Input
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="h-10 w-16 border-slate-800 bg-slate-900"
                />
                <Input
                  type="text"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="flex-1 border-slate-800 bg-slate-900 text-slate-200 font-mono text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">Size</Label>
                <Input
                  type="number"
                  min="10"
                  max="150"
                  value={size}
                  onChange={(e) => setSize(e.target.value)}
                  className="border-slate-800 bg-slate-900 text-slate-200"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">Shape</Label>
                <Select value={shape} onValueChange={setShape}>
                  <SelectTrigger className="border-slate-800 bg-slate-900 text-sm text-slate-200">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="border-slate-800 bg-slate-950">
                    <SelectItem value="circle" className="text-slate-200">Circle</SelectItem>
                    <SelectItem value="rect" className="text-slate-200">Square</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Preset Gallery */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-sm text-slate-200">
            Animation Presets
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {PRESETS.map((p) => (
              <button
                key={p.id}
                onClick={() => setPresetId(p.id)}
                className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-colors hover:bg-slate-800 ${
                  presetId === p.id
                    ? "border-purple-500/50 bg-purple-950/20"
                    : "border-slate-800 bg-slate-900/50"
                }`}
              >
                <span className="text-lg">{p.icon}</span>
                <div>
                  <div className="text-sm font-medium text-slate-200">{p.label}</div>
                  <div className="text-xs text-slate-500">{p.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
