import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Database, BrainCircuit, RefreshCw, Save } from "lucide-react";
import { mcpClient } from "@/common/mcp-client";

interface LocalModels {
    ollama: string[];
    lm_studio: string[];
}

export function Settings() {
    const [loadingModels, setLoadingModels] = useState(false);
    const [models, setModels] = useState<LocalModels>({ ollama: [], lm_studio: [] });
    const [provider, setProvider] = useState("ollama");
    const [selectedModel, setSelectedModel] = useState("");

    const fetchModels = async () => {
        setLoadingModels(true);
        try {
            const response = await mcpClient.callTool("list_local_models");
            if (response && response.content && response.content[0]) {
                try {
                    const result = JSON.parse(response.content[0].text);
                    if (result.success) {
                        setModels(result.result);
                        // Auto-select first model if none selected
                        const available = result.result[provider as keyof LocalModels] || [];
                        if (available.length > 0 && !selectedModel) {
                            setSelectedModel(available[0]);
                        }
                    }
                } catch (e) {
                    console.error("Failed to parse model list:", e);
                }
            }
        } catch (error) {
            console.error("Failed to fetch models:", error);
        } finally {
            setLoadingModels(false);
        }
    };

    useEffect(() => {
        fetchModels();
    }, []);

    const currentModels = models[provider as keyof LocalModels] || [];

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Settings</h2>
                <p className="text-slate-400">Manage Inkscape CLI connections and processing preferences</p>
            </div>

            <div className="grid gap-6">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <BrainCircuit className="h-5 w-5 text-purple-400" />
                            LLM Configuration
                        </CardTitle>
                        <CardDescription className="text-slate-400">Configure local LLM providers for agentic vector operations</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <Label className="text-slate-300">Provider</Label>
                                <Select value={provider} onValueChange={setProvider}>
                                    <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                                        <SelectValue placeholder="Select provider" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                                        <SelectItem value="ollama">Ollama</SelectItem>
                                        <SelectItem value="lm_studio">LM Studio</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <Label className="text-slate-300">Model</Label>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6 text-slate-400 hover:text-white"
                                        onClick={fetchModels}
                                        disabled={loadingModels}
                                    >
                                        <RefreshCw className={cn("h-3 w-3", loadingModels && "animate-spin")} />
                                    </Button>
                                </div>
                                <Select value={selectedModel} onValueChange={setSelectedModel} disabled={loadingModels}>
                                    <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                                        <SelectValue placeholder={loadingModels ? "Loading..." : "Select model"} />
                                    </SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                                        {currentModels.length > 0 ? (
                                            currentModels.map(m => (
                                                <SelectItem key={m} value={m}>{m}</SelectItem>
                                            ))
                                        ) : (
                                            <SelectItem value="none" disabled>No models found</SelectItem>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Database className="h-5 w-5 text-blue-400" />
                            Inkscape CLI Configuration
                        </CardTitle>
                        <CardDescription className="text-slate-400">System path and environment for the Inkscape executable</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">Executable Path</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                                defaultValue="C:\Program Files\Inkscape\bin\inkscape.exe"
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-800">
                                Check Binary
                            </Button>
                            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                                <Save className="mr-2 h-4 w-4" />
                                Save Configuration
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

function cn(...classes: any[]) {
    return classes.filter(Boolean).join(' ');
}
