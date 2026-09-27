import { useState } from "react";
import { Link } from "react-router-dom";
import { apiDelete } from "@/api/client";
import { cn } from "@/common/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  installStatus,
  type ProviderInfo,
  saveLlmSettings,
  startInstall,
  testProvider as runTest,
} from "@/lib/llm";

type Props = {
  providers: ProviderInfo[];
  probing: boolean;
  selected: string;
  /** Called after any mutation (key save/clear, install) with the affected id. */
  onChanged: (providerId: string) => Promise<void> | void;
};

/**
 * Canonical fleet provider cards (local free vs cloud paid, status dots, key
 * entry, Test, one-click Ollama install). Vendored from mcp-central-docs.
 */
export function LlmProviderCards({
  providers,
  probing,
  selected,
  onChanged,
}: Props) {
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [cardMsg, setCardMsg] = useState<Record<string, string>>({});
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState<string | null>(null);

  const localProviders = providers.filter((p) => p.kind === "local");
  const cloudProviders = providers.filter((p) => p.kind === "cloud");

  function statusDot(p: ProviderInfo) {
    if (p.kind === "local") {
      if (probing)
        return (
          <span className="h-2 w-2 rounded-full bg-slate-500 animate-pulse" />
        );
      return p.detected ? (
        <span className="h-2 w-2 rounded-full bg-green-500" />
      ) : (
        <span className="h-2 w-2 rounded-full bg-slate-600" />
      );
    }
    return p.configured ? (
      <span className="h-2 w-2 rounded-full bg-green-500" />
    ) : (
      <span className="h-2 w-2 rounded-full bg-amber-500" />
    );
  }

  function statusText(p: ProviderInfo): string {
    if (p.kind === "local") {
      if (probing) return "Probing…";
      return p.detected
        ? `Detected · ${p.models?.length ?? 0} models`
        : "Not found";
    }
    return p.configured ? "Key configured" : "Missing key";
  }

  async function saveKey(id: string) {
    const key = keyInputs[id]?.trim();
    if (!key) return;
    setCardMsg((m) => ({ ...m, [id]: "Saving…" }));
    try {
      // No-auto-pick (BUG-030): saving a key must not select a model, and
      // select:false (BUG-043) keeps this card's key from hijacking whatever
      // provider/model is currently active elsewhere (e.g. Ollama).
      await saveLlmSettings({
        provider: id,
        model: "",
        api_key: key,
        select: false,
      });
      setKeyInputs((k) => ({ ...k, [id]: "" }));
      await onChanged(id);
      setCardMsg((m) => ({ ...m, [id]: "Key saved." }));
    } catch (e) {
      setCardMsg((m) => ({
        ...m,
        [id]: e instanceof Error ? e.message : String(e),
      }));
    }
  }

  async function clearKey(id: string) {
    setCardMsg((m) => ({ ...m, [id]: "Clearing…" }));
    try {
      await apiDelete(
        `/api/settings/llm/key?provider=${encodeURIComponent(id)}`,
      );
      await onChanged(id);
      setCardMsg((m) => ({ ...m, [id]: "Key cleared." }));
    } catch (e) {
      setCardMsg((m) => ({
        ...m,
        [id]: e instanceof Error ? e.message : String(e),
      }));
    }
  }

  async function testProvider(id: string) {
    setCardMsg((m) => ({ ...m, [id]: "Testing…" }));
    try {
      // Offer the card's typed key (if any): testing without it reports
      // curated names as success while status stays unkeyed (BUG-042).
      // Key travels in the POST body, never saved.
      const typed = keyInputs[id]?.trim() || undefined;
      const t = await runTest(id, typed);
      if (t.ok) {
        setCardMsg((m2) => ({
          ...m2,
          [id]: `Key valid — ${t.models.length} live model(s).${typed ? " Save key to keep it." : ""}`,
        }));
      } else {
        setCardMsg((m2) => ({
          ...m2,
          [id]: t.note || t.error || "Not reachable — check the endpoint.",
        }));
      }
    } catch (e) {
      setCardMsg((m) => ({
        ...m,
        [id]: e instanceof Error ? e.message : String(e),
      }));
    }
  }

  async function installOllama() {
    setInstalling(true);
    setInstallMsg("Starting winget install…");
    try {
      await startInstall("ollama");
      for (let i = 0; i < 120; i++) {
        await new Promise((r) => setTimeout(r, 5000));
        const st = await installStatus("ollama");
        if (st.state === "done") {
          setInstallMsg("Installed. Re-probing…");
          await onChanged("ollama");
          setInstallMsg(
            "Ollama installed and detected. Pull a model: ollama pull qwen3:32b",
          );
          break;
        }
        if (st.state === "error") {
          setInstallMsg(
            `Install failed: ${(st.output ?? "").slice(-300) || "see backend logs"}`,
          );
          break;
        }
        setInstallMsg(`Installing… (${i * 5 + 5}s)`);
      }
    } catch (e) {
      setInstallMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setInstalling(false);
    }
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {localProviders.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-slate-400 font-medium">
            Local engines (free)
          </p>
          {localProviders.map((p) => (
            <Card
              key={p.id}
              data-testid={`llm-provider-card-${p.id}`}
              className={cn(
                "border-slate-800 bg-slate-950/50 p-4 space-y-2",
                p.id === selected && "border-blue-600/50",
              )}
            >
              <div className="flex items-center gap-2">
                {statusDot(p)}
                <span className="text-sm font-semibold text-slate-200">
                  {p.label}
                </span>
                <span className="text-[10px] rounded bg-slate-800 px-1.5 py-0.5 text-slate-400">
                  local · free
                </span>
                <span className="text-xs text-slate-400 ml-auto">
                  {statusText(p)}
                </span>
              </div>
              {p.id === "ollama" && !p.detected && !probing && (
                <div className="text-xs text-slate-400 rounded border border-slate-800 px-2 py-1.5 space-y-2">
                  <p>
                    Not running. Manual:{" "}
                    <code className="font-mono">
                      winget install -e --id Ollama.Ollama
                    </code>{" "}
                    then{" "}
                    <code className="font-mono">ollama pull qwen3:32b</code> —
                    or see the{" "}
                    <Link to="/skills" className="underline">
                      skills page
                    </Link>
                    .
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      data-testid="llm-install-ollama"
                      disabled={installing}
                      onClick={() => void installOllama()}
                    >
                      {installing ? "Installing…" : "Install Ollama now"}
                    </Button>
                    {installMsg && <span>{installMsg}</span>}
                  </div>
                </div>
              )}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  data-testid={`llm-test-${p.id}`}
                  onClick={() => void testProvider(p.id)}
                >
                  Test
                </Button>
                {cardMsg[p.id] && (
                  <span className="text-xs text-slate-400 self-center">
                    {cardMsg[p.id]}
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {cloudProviders.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-slate-400 font-medium">Cloud (API key)</p>
          {cloudProviders.map((p) => (
            <Card
              key={p.id}
              data-testid={`llm-provider-card-${p.id}`}
              className={cn(
                "border-slate-800 bg-slate-950/50 p-4 space-y-2",
                p.id === selected && "border-blue-600/50",
              )}
            >
              <div className="flex items-center gap-2">
                {statusDot(p)}
                <span className="text-sm font-semibold text-slate-200">
                  {p.label}
                </span>
                <span className="text-[10px] rounded bg-slate-800 px-1.5 py-0.5 text-slate-400">
                  cloud · paid
                </span>
                <span className="text-xs text-slate-400 ml-auto">
                  {statusText(p)}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type={showKeys[p.id] ? "text" : "password"}
                  value={keyInputs[p.id] ?? ""}
                  onChange={(e) =>
                    setKeyInputs((k) => ({ ...k, [p.id]: e.target.value }))
                  }
                  placeholder={
                    p.configured ? "•••••••• configured" : `Paste ${p.key_env}`
                  }
                  aria-label={`${p.label} API key`}
                  data-testid={`llm-key-${p.id}`}
                  className="flex-1 min-w-40 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs font-mono text-slate-200"
                />
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    setShowKeys((s) => ({ ...s, [p.id]: !s[p.id] }))
                  }
                >
                  {showKeys[p.id] ? "Hide" : "Show"}
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={!keyInputs[p.id]?.trim()}
                  onClick={() => void saveKey(p.id)}
                >
                  Save key
                </Button>
                {p.configured && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void clearKey(p.id)}
                  >
                    Clear
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  data-testid={`llm-test-${p.id}`}
                  onClick={() => void testProvider(p.id)}
                >
                  Test
                </Button>
                {cardMsg[p.id] && (
                  <span className="text-xs text-slate-400 self-center">
                    {cardMsg[p.id]}
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
