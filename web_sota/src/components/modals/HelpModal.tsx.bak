import * as Dialog from "@radix-ui/react-dialog";
import { CircleHelp, X } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function HelpModal({ open, onClose }: Props) {
  return (
    <Dialog.Root open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[85vh] w-[90vw] max-w-2xl -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-6 shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold text-slate-100">
            <CircleHelp className="h-5 w-5 text-blue-500" />
            Inkscape MCP — Help
          </Dialog.Title>

          <Dialog.Close className="absolute right-4 top-4 rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white">
            <X className="h-4 w-4" />
          </Dialog.Close>

          <div className="mt-4 space-y-4 text-sm text-slate-400">
            <section>
              <h3 className="mb-1 font-medium text-slate-200">What is Inkscape MCP?</h3>
              <p>AI-powered vector graphics server that exposes Inkscape through the Model Context Protocol. Use with Claude Desktop, Cursor, or any MCP client to create and edit SVG files.</p>
            </section>

            <section>
              <h3 className="mb-1 font-medium text-slate-200">Key Tools</h3>
              <ul className="list-inside list-disc space-y-1">
                <li><strong className="text-slate-300">inkscape_vector</strong> — primitives, paths, booleans, LPEs, text, inspect</li>
                <li><strong className="text-slate-300">inkscape_layers</strong> — create, rename, hide/show, lock, reorder layers</li>
                <li><strong className="text-slate-300">inkscape_animation</strong> — SMIL presets, element/transform/motion animation</li>
                <li><strong className="text-slate-300">inkscape_file</strong> — load, save, convert, validate SVG files</li>
                <li><strong className="text-slate-300">inkscape_analysis</strong> — statistics, validate, dimensions, object listing</li>
                <li><strong className="text-slate-300">inkscape_system</strong> — status, diagnostics, hands-in command, extensions</li>
              </ul>
            </section>

            <section>
              <h3 className="mb-1 font-medium text-slate-200">Prerequisites</h3>
              <ul className="list-inside list-disc space-y-1">
                <li>Inkscape 1.0+ (1.2+ recommended for Actions API)</li>
                <li>Python 3.12+ with uv</li>
                <li>Optional: Ollama for AI-assisted SVG generation</li>
              </ul>
            </section>

            <section>
              <h3 className="mb-1 font-medium text-slate-200">Links</h3>
              <ul className="list-inside list-disc space-y-1">
                <li><a href="https://github.com/sandraschi/inkscape-mcp" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">GitHub</a></li>
                <li><a href="https://inkscape.org" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">Inkscape</a></li>
              </ul>
            </section>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
