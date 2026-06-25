import * as Dialog from "@radix-ui/react-dialog";
import { ScrollText, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import API_BASE from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function LogModal({ open, onClose }: Props) {
  const [logs, setLogs] = useState<string>("Loading...");

  const fetchLogs = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/logs`);
      if (!r.ok) { setLogs(`HTTP ${r.status}`); return; }
      const data = await r.json();
      setLogs(JSON.stringify(data, null, 2));
    } catch (e) {
      setLogs(String(e));
    }
  }, []);

  useEffect(() => {
    if (open) fetchLogs();
  }, [open, fetchLogs]);

  return (
    <Dialog.Root open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[85vh] w-[90vw] max-w-3xl -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 p-6 shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold text-slate-100">
            <ScrollText className="h-5 w-5 text-amber-500" />
            Server Logs
          </Dialog.Title>

          <Dialog.Close className="absolute right-4 top-4 rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white">
            <X className="h-4 w-4" />
          </Dialog.Close>

          <div className="mt-4">
            <pre className="max-h-[60vh] overflow-auto rounded-lg border border-slate-800 bg-slate-900 p-3 font-mono text-xs text-slate-300">
              {logs}
            </pre>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
