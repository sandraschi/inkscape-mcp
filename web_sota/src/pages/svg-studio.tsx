import React, { useState, useRef, useCallback } from 'react';
import {
    Wand2, Download, RefreshCw, Copy, Loader2, Sparkles,
    PenTool, Star, Layers, Settings2, ChevronDown, ChevronUp,
    AlertCircle, CheckCircle, X, History, Eye,
} from 'lucide-react';
import { cn } from '@/common/utils';

// ─────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────

interface GeneratedSvg {
    id: string;
    prompt: string;
    style: string;
    dimensions: string;
    quality: string;
    svgContent: string;
    svgPath?: string;
    fileSize?: string;
    generatedAt: Date;
    steps?: number;
}

interface ApiResult {
    success: boolean;
    svg_content?: string;
    svg_path?: string;
    file_size_kb?: number;
    steps_taken?: number;
    error?: string;
    message?: string;
}

// ─────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────

const STYLE_PRESETS = [
    { id: 'heraldic', label: 'Heraldic', icon: '⚜️', desc: 'Crests, shields, coats of arms' },
    { id: 'geometric', label: 'Geometric', icon: '🔷', desc: 'Clean shapes, patterns' },
    { id: 'organic', label: 'Organic', icon: '🌿', desc: 'Natural, flowing forms' },
    { id: 'abstract', label: 'Abstract', icon: '🎨', desc: 'Artistic, conceptual' },
    { id: 'technical', label: 'Technical', icon: '⚙️', desc: 'Diagrams, schematics' },
];

const DIMENSION_PRESETS = ['800x600', '600x800', '500x500', '1200x800', '400x400'];
const QUALITY_PRESETS = ['draft', 'standard', 'high', 'ultra'];

const POST_PROC_OPTIONS = [
    { id: 'simplify', label: 'Simplify paths' },
    { id: 'optimize', label: 'Optimize (scour)' },
    { id: 'clean_ids', label: 'Clean up IDs' },
    { id: 'remove_invisible', label: 'Remove invisible elements' },
];

const EXAMPLE_PROMPTS = [
    'Royal crest of Trumponia with two asses rampant',
    'Minimalist mountain range at sunset, gradients',
    'Celtic knot interlace pattern in forest green and gold',
    'Art deco city skyline in black and silver',
    'Geometric mandala with 12-fold symmetry, navy and copper',
    'Steampunk gear mechanism cross-section diagram',
    'Coat of arms: azure field, three gold stars, wolf rampant',
];

// ─────────────────────────────────────────────────────────────────
// API helper — calls the backend /api/generate-svg endpoint
// ─────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10760';

async function callGenerateSvg(params: {
    description: string;
    style_preset: string;
    dimensions: string;
    quality: string;
    post_processing: string[];
    max_steps: number;
}): Promise<ApiResult> {
    const res = await fetch(`${API_BASE}/api/generate-svg`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return res.json();
}

// ─────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────

function SvgPreview({ svg, onCopy }: { svg: string; onCopy: () => void }) {
    const previewRef = useRef<HTMLDivElement>(null);

    const downloadSvg = useCallback(() => {
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `inkscape-mcp-${Date.now()}.svg`;
        a.click();
        URL.revokeObjectURL(url);
    }, [svg]);

    return (
        <div className="relative flex h-full min-h-[320px] w-full items-center justify-center overflow-hidden rounded-xl border border-slate-700 bg-slate-900">
            {/* checkerboard bg for transparency */}
            <div className="absolute inset-0 opacity-20 checkerboard-bg" />
            <div
                ref={previewRef}
                className="relative z-10 max-h-full max-w-full p-4"
                dangerouslySetInnerHTML={{ __html: svg }}
            />
            {/* Action buttons */}
            <div className="absolute bottom-3 right-3 z-20 flex gap-2">
                <button
                    onClick={onCopy}
                    aria-label="Copy SVG source"
                    className="flex items-center gap-1.5 rounded-lg bg-slate-800/90 px-3 py-1.5 text-xs text-slate-300 backdrop-blur-sm hover:bg-slate-700 hover:text-white transition-colors"
                >
                    <Copy className="h-3.5 w-3.5" />
                    Copy
                </button>
                <button
                    onClick={downloadSvg}
                    aria-label="Download SVG"
                    className="flex items-center gap-1.5 rounded-lg bg-blue-600/90 px-3 py-1.5 text-xs text-white backdrop-blur-sm hover:bg-blue-500 transition-colors"
                >
                    <Download className="h-3.5 w-3.5" />
                    Download
                </button>
            </div>
        </div>
    );
}

function HistoryThumb({
    item,
    onSelect,
    onDelete,
}: {
    item: GeneratedSvg;
    onSelect: () => void;
    onDelete: () => void;
}) {
    return (
        <div className="group relative overflow-hidden rounded-lg border border-slate-700 bg-slate-900 hover:border-blue-500/60 transition-colors">
            <button
                onClick={onSelect}
                aria-label={`Select SVG: ${item.prompt}`}
                className="block w-full cursor-pointer text-left"
            >
                <div
                    className="flex h-24 w-full items-center justify-center overflow-hidden p-2"
                    dangerouslySetInnerHTML={{ __html: item.svgContent }}
                />
                <div className="border-t border-slate-700 px-2 py-1">
                    <p className="truncate text-xs text-slate-400">{item.prompt}</p>
                    <p className="text-[10px] text-slate-600">{item.style} · {item.dimensions}</p>
                </div>
            </button>
            <button
                aria-label="Remove from history"
                onClick={(e) => { e.stopPropagation(); onDelete(); }}
                className="absolute right-1 top-1 hidden rounded bg-slate-900/80 p-0.5 text-slate-500 hover:text-red-400 group-hover:flex"
            >
                <X className="h-3 w-3" />
            </button>
        </div>
    );
}


// ─────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────

export function SvgStudio() {
    const [prompt, setPrompt] = useState('');
    const [style, setStyle] = useState('geometric');
    const [dimensions, setDimensions] = useState('800x600');
    const [quality, setQuality] = useState('standard');
    const [postProc, setPostProc] = useState<string[]>([]);
    const [maxSteps, setMaxSteps] = useState(5);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [copiedMsg, setCopiedMsg] = useState(false);

    const [current, setCurrent] = useState<GeneratedSvg | null>(null);
    const [history, setHistory] = useState<GeneratedSvg[]>([]);
    const [activeHistoryItem, setActiveHistoryItem] = useState<GeneratedSvg | null>(null);

    const displayedSvg = activeHistoryItem ?? current;

    const togglePostProc = (id: string) => {
        setPostProc((prev) =>
            prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
        );
    };

    const handleGenerate = async () => {
        if (!prompt.trim()) return;
        setLoading(true);
        setError(null);
        setActiveHistoryItem(null);
        try {
            const result = await callGenerateSvg({
                description: prompt,
                style_preset: style,
                dimensions,
                quality,
                post_processing: postProc,
                max_steps: maxSteps,
            });

            if (!result.success) {
                setError(result.error || result.message || 'Generation failed');
                return;
            }

            const svgContent = result.svg_content ?? '';
            if (!svgContent) {
                setError('Server returned empty SVG content.');
                return;
            }

            const newItem: GeneratedSvg = {
                id: crypto.randomUUID(),
                prompt,
                style,
                dimensions,
                quality,
                svgContent,
                svgPath: result.svg_path,
                fileSize: result.file_size_kb ? `${result.file_size_kb} KB` : undefined,
                generatedAt: new Date(),
                steps: result.steps_taken,
            };
            setCurrent(newItem);
            setHistory((prev) => [newItem, ...prev.slice(0, 29)]); // keep last 30
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = useCallback(() => {
        if (!displayedSvg) return;
        navigator.clipboard.writeText(displayedSvg.svgContent).then(() => {
            setCopiedMsg(true);
            setTimeout(() => setCopiedMsg(false), 2000);
        });
    }, [displayedSvg]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleGenerate();
    };

    return (
        <div className="space-y-6">
            {/* ── Page header ── */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 shadow-lg shadow-purple-900/40">
                        <PenTool className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">SVG Studio</h1>
                        <p className="text-sm text-slate-400">
                            AI-powered vector generation via Inkscape MCP + SEP-1577 sampling
                        </p>
                    </div>
                </div>
                {copiedMsg && (
                    <div className="flex items-center gap-1.5 rounded-lg bg-emerald-900/60 px-3 py-1.5 text-xs text-emerald-400">
                        <CheckCircle className="h-3.5 w-3.5" /> Copied!
                    </div>
                )}
            </div>

            {/* ── Main grid ── */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.4fr]">

                {/* ── Left: Generator controls ── */}
                <div className="space-y-5">

                    {/* Prompt */}
                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
                        <label className="mb-2 block text-sm font-medium text-slate-300">
                            Describe your SVG
                        </label>
                        <textarea
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="e.g. Royal crest of Trumponia with two asses rampant, azure field, gold charges, motto scroll reading 'Semper Absurdus'"
                            rows={4}
                            className="w-full resize-none rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50"
                        />
                        {/* Example prompts */}
                        <details className="mt-2">
                            <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-400 select-none">
                                Example prompts ▾
                            </summary>
                            <div className="mt-2 space-y-1">
                                {EXAMPLE_PROMPTS.map((ex) => (
                                    <button
                                        key={ex}
                                        onClick={() => setPrompt(ex)}
                                        className="block w-full rounded px-2 py-1 text-left text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                                    >
                                        {ex}
                                    </button>
                                ))}
                            </div>
                        </details>
                    </div>

                    {/* Style presets */}
                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
                        <p className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300">
                            <Star className="h-4 w-4 text-amber-400" />
                            Style Preset
                        </p>
                        <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                            {STYLE_PRESETS.map((s) => (
                                <button
                                    key={s.id}
                                    onClick={() => setStyle(s.id)}
                                    title={s.desc}
                                    className={cn(
                                        'flex flex-col items-center gap-1 rounded-lg border px-2 py-3 text-xs transition-all',
                                        style === s.id
                                            ? 'border-blue-500 bg-blue-500/10 text-blue-300 shadow-sm shadow-blue-900/30'
                                            : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-600 hover:text-slate-300',
                                    )}
                                >
                                    <span className="text-lg leading-none">{s.icon}</span>
                                    <span className="font-medium">{s.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Dimensions + Quality */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
                            <p className="mb-2 text-xs font-medium text-slate-400">Dimensions</p>
                            <div className="flex flex-wrap gap-2">
                                {DIMENSION_PRESETS.map((d) => (
                                    <button
                                        key={d}
                                        onClick={() => setDimensions(d)}
                                        className={cn(
                                            'rounded px-2.5 py-1 text-xs font-mono transition-colors',
                                            dimensions === d
                                                ? 'bg-blue-600 text-white'
                                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700',
                                        )}
                                    >
                                        {d}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
                            <p className="mb-2 text-xs font-medium text-slate-400">Quality</p>
                            <div className="flex flex-wrap gap-2">
                                {QUALITY_PRESETS.map((q) => (
                                    <button
                                        key={q}
                                        onClick={() => setQuality(q)}
                                        className={cn(
                                            'rounded px-2.5 py-1 text-xs capitalize transition-colors',
                                            quality === q
                                                ? 'bg-emerald-600 text-white'
                                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700',
                                        )}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Advanced options toggle */}
                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
                        <button
                            onClick={() => setShowAdvanced((v) => !v)}
                            className="flex w-full items-center justify-between px-5 py-3 text-sm text-slate-400 hover:text-slate-300 transition-colors"
                        >
                            <span className="flex items-center gap-2">
                                <Settings2 className="h-4 w-4" />
                                Advanced options
                            </span>
                            {showAdvanced ? (
                                <ChevronUp className="h-4 w-4" />
                            ) : (
                                <ChevronDown className="h-4 w-4" />
                            )}
                        </button>
                        {showAdvanced && (
                            <div className="border-t border-slate-800 px-5 pb-4 pt-3 space-y-4">
                                <div>
                                    <p className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-400">
                                        <Layers className="h-3.5 w-3.5" />
                                        Post-processing (Inkscape)
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        {POST_PROC_OPTIONS.map((opt) => (
                                            <label
                                                key={opt.id}
                                                className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-600 hover:text-slate-300 transition-colors"
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={postProc.includes(opt.id)}
                                                    onChange={() => togglePostProc(opt.id)}
                                                    className="accent-blue-500"
                                                />
                                                {opt.label}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="max-steps-range" className="mb-1 block text-xs font-medium text-slate-400">
                                        SEP-1577 max steps: {maxSteps}
                                    </label>
                                    <input
                                        id="max-steps-range"
                                        title="Maximum SEP-1577 reasoning steps"
                                        type="range"
                                        min={1}
                                        max={10}
                                        value={maxSteps}
                                        onChange={(e) => setMaxSteps(Number(e.target.value))}
                                        className="w-full accent-blue-500"
                                    />
                                    <p className="mt-1 text-[10px] text-slate-600">
                                        More steps = more capability probing = richer SVG
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Generate button */}
                    <button
                        onClick={handleGenerate}
                        disabled={loading || !prompt.trim()}
                        className={cn(
                            'relative w-full overflow-hidden rounded-xl py-3.5 text-sm font-semibold transition-all',
                            'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg shadow-purple-900/30',
                            'hover:from-purple-500 hover:to-blue-500 hover:shadow-purple-800/40',
                            'disabled:opacity-50 disabled:cursor-not-allowed',
                            loading && 'animate-pulse',
                        )}
                    >
                        <span className="flex items-center justify-center gap-2">
                            {loading ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Generating via SEP-1577…
                                </>
                            ) : (
                                <>
                                    <Wand2 className="h-4 w-4" />
                                    Generate SVG
                                    <Sparkles className="h-3.5 w-3.5 text-yellow-300" />
                                </>
                            )}
                        </span>
                        <span className="absolute bottom-1 right-3 text-[10px] text-white/40">
                            Ctrl+Enter
                        </span>
                    </button>

                    {/* Error banner */}
                    {error && (
                        <div className="flex items-start gap-2 rounded-xl border border-red-800/60 bg-red-900/20 px-4 py-3 text-sm text-red-400">
                            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                            <div className="flex-1 break-words">{error}</div>
                            <button
                                onClick={() => setError(null)}
                                aria-label="Dismiss error"
                                className="shrink-0 text-red-600 hover:text-red-400"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                    )}
                </div>

                {/* ── Right: Preview + history ── */}
                <div className="flex flex-col gap-5">

                    {/* Preview panel */}
                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
                        <div className="mb-3 flex items-center justify-between">
                            <p className="flex items-center gap-2 text-sm font-medium text-slate-300">
                                <Eye className="h-4 w-4 text-blue-400" />
                                Preview
                                {displayedSvg && (
                                    <span className="text-xs text-slate-500">
                                        — {displayedSvg.prompt.slice(0, 40)}{displayedSvg.prompt.length > 40 ? '…' : ''}
                                    </span>
                                )}
                            </p>
                            {displayedSvg && (
                                <div className="flex items-center gap-3 text-xs text-slate-500">
                                    {displayedSvg.fileSize && <span>{displayedSvg.fileSize}</span>}
                                    {displayedSvg.steps && <span>{displayedSvg.steps} SEP-1577 steps</span>}
                                    {activeHistoryItem && (
                                        <button
                                            onClick={() => setActiveHistoryItem(null)}
                                            className="flex items-center gap-1 rounded px-2 py-0.5 text-xs text-blue-400 hover:bg-slate-800"
                                        >
                                            <RefreshCw className="h-3 w-3" />
                                            Latest
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>

                        {displayedSvg ? (
                            <SvgPreview svg={displayedSvg.svgContent} onCopy={handleCopy} />
                        ) : (
                            <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/40 text-center">
                                <div className="space-y-2">
                                    <Wand2 className="mx-auto h-8 w-8 text-slate-600" />
                                    <p className="text-sm text-slate-500">
                                        Your generated SVG will appear here
                                    </p>
                                    <p className="text-xs text-slate-600">
                                        Requires a sampling-capable client (Claude Desktop, Antigravity)
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* History panel */}
                    {history.length > 0 && (
                        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
                            <p className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300">
                                <History className="h-4 w-4 text-slate-400" />
                                Recent ({history.length})
                            </p>
                            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
                                {history.slice(0, 10).map((item) => (
                                    <HistoryThumb
                                        key={item.id}
                                        item={item}
                                        onSelect={() =>
                                            setActiveHistoryItem(
                                                activeHistoryItem?.id === item.id ? null : item,
                                            )
                                        }
                                        onDelete={() =>
                                            setHistory((prev) =>
                                                prev.filter((h) => h.id !== item.id),
                                            )
                                        }
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
