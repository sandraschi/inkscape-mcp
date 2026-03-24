import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Zap, Loader2, CheckCircle2, AlertCircle, Image as ImageIcon, QrCode, Sliders } from "lucide-react";
import { mcpClient } from "@/common/mcp-client";

interface ActionStatus {
    loading: boolean;
    result: any | null;
    error: string | null;
}

export function Actions() {
    const [status, setStatus] = useState<Record<string, ActionStatus>>({
        trace: { loading: false, result: null, error: null },
        preview: { loading: false, result: null, error: null },
        qr: { loading: false, result: null, error: null },
    });

    const runAction = async (id: string, operation: string, args: any = {}) => {
        setStatus(prev => ({ ...prev, [id]: { loading: true, result: null, error: null } }));
        try {
            const result = await mcpClient.callTool("inkscape_vector", { operation, ...args });
            setStatus(prev => ({ ...prev, [id]: { loading: false, result, error: null } }));
        } catch (error: any) {
            setStatus(prev => ({ ...prev, [id]: { loading: false, result: null, error: error.message } }));
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Vector Actions</h2>
                <p className="text-slate-400">Execute advanced Inkscape vector operations</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <ActionCard
                    title="Trace Bitmap"
                    description="Convert raster images to vector paths using Potrace."
                    icon={ImageIcon}
                    status={status.trace}
                    onRun={() => runAction("trace", "trace_image", { input_path: "input.png", output_path: "output.svg" })}
                />

                <ActionCard
                    title="Render Preview"
                    description="Generate high-DPI PNG previews of SVG documents."
                    icon={Sliders}
                    status={status.preview}
                    onRun={() => runAction("preview", "render_preview", { input_path: "input.svg", output_path: "preview.png", dpi: 300 })}
                />

                <ActionCard
                    title="Generate QR"
                    description="Create QR codes as vector elements in the document."
                    icon={QrCode}
                    status={status.qr}
                    onRun={() => runAction("qr", "generate_barcode_qr", { barcode_data: "https://mcp-central.ai", output_path: "qr.svg" })}
                />
            </div>
        </div>
    );
}

function ActionCard({ title, description, icon: Icon, status, onRun }: any) {
    return (
        <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
                <div className="flex items-center gap-2">
                    <div className="rounded-lg bg-blue-500/10 p-2">
                        <Icon className="h-5 w-5 text-blue-500" />
                    </div>
                    <CardTitle className="text-white">{title}</CardTitle>
                </div>
                <CardDescription className="text-slate-400">{description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <Button
                    onClick={onRun}
                    disabled={status.loading}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                    {status.loading ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Executing...
                        </>
                    ) : (
                        <>
                            <Zap className="mr-2 h-4 w-4" />
                            Run Action
                        </>
                    )}
                </Button>

                {status.result && (
                    <div className="flex items-center gap-2 rounded-md bg-green-500/10 p-3 text-sm text-green-400">
                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                        <span className="truncate">{status.result.summary || "Success"}</span>
                    </div>
                )}

                {status.error && (
                    <div className="flex items-center gap-2 rounded-md bg-red-500/10 p-3 text-sm text-red-400">
                        <AlertCircle className="h-4 w-4 shrink-0" />
                        <span className="truncate">{status.error}</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
