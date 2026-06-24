"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { ExternalLink, HelpCircle, LayoutGrid } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import { APPS_CATALOG } from "@/common/apps-catalog";
import API_BASE from "@/lib/api";
import { useBackendStore } from "@/lib/store";

export function Topbar() {
  const online = useBackendStore((s) => s.online);
  const setOnline = useBackendStore((s) => s.setOnline);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  const check = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/health`);
      setOnline(r.ok);
    } catch {
      setOnline(false);
    }
  }, [setOnline]);

  useEffect(() => {
    check();
    intervalRef.current = setInterval(check, 30_000);
    return () => clearInterval(intervalRef.current);
  }, [check]);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          setOnline(event.payload === "ready");
        });
      } catch { /* not in Tauri */ }
    })();
    return () => { if (unlisten) unlisten(); };
  }, [setOnline]);

  const color = online === null ? "slate" : online ? "emerald" : "red";
  const label = online === null ? "Connecting..." : online ? "System Online" : "Offline";

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-800 bg-slate-950/50 px-6 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <h1 className="text-sm font-medium text-slate-400">
          Navigation / <span className="text-slate-100">Control Center</span>
        </h1>
      </div>

      <div className="flex items-center gap-2">
        {/* System Status Indicator */}
        <div className={`mr-4 flex items-center gap-2 rounded-full px-3 py-1 text-xs border ${color === "emerald" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : color === "red" ? "bg-red-500/10 text-red-400 border-red-500/20" : "bg-slate-500/10 text-slate-400 border-slate-500/20"}`}>
          <span className="relative flex h-2 w-2">
            {online && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span className={`relative inline-flex h-2 w-2 rounded-full ${color === "emerald" ? "bg-emerald-500" : color === "red" ? "bg-red-500" : "bg-slate-500"}`}></span>
          </span>
          {label}
        </div>

        {/* Global Apps Navigation */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button type="button" className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900/50 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-700">
              <LayoutGrid className="h-4 w-4" />
              Apps
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="z-50 min-w-[220px] animate-in fade-in zoom-in-95 data-[side=bottom]:slide-in-from-top-2 rounded-md border border-slate-800 bg-slate-950 p-1 shadow-xl"
              sideOffset={5}
              align="end"
            >
              {APPS_CATALOG.filter((a) => a.url).map((app) => (
                <DropdownMenu.Item key={app.id} className="outline-none">
                  <a
                    href={app.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                  >
                    <span className="text-base">{app.icon}</span>
                    <span>{app.label}</span>
                    <span className="text-xs text-slate-600">{app.description}</span>
                    <ExternalLink className="ml-auto h-3 w-3 opacity-50" />
                  </a>
                </DropdownMenu.Item>
              ))}
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>

        <button type="button" className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 bg-slate-900/50 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors">
          <HelpCircle className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
