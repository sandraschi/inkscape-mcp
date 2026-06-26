import { useCallback, useEffect } from "react";
import { isTauri } from "./is-tauri";

const ZOOM_LEVELS = [0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

export function useZoom() {
  const applyZoom = useCallback(async (level: number) => {
    localStorage.setItem("tauri-zoom", String(level));
    if (isTauri()) {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await (getCurrentWindow() as any).setZoom(level);
    } else {
      const root = document.documentElement;
      root.style.transform = `scale(${level})`;
      root.style.transformOrigin = "top left";
      root.style.width = `${100 / level}%`;
      root.style.height = `${100 / level}%`;
    }
  }, []);

  useEffect(() => {
    const handler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      let idx = ZOOM_LEVELS.indexOf(parseFloat(localStorage.getItem("tauri-zoom") || "1"));
      if (idx < 0) idx = 1;
      const next = e.deltaY < 0 ? Math.min(idx + 1, ZOOM_LEVELS.length - 1) : Math.max(idx - 1, 0);
      if (next !== idx) applyZoom(ZOOM_LEVELS[next]);
    };
    window.addEventListener("wheel", handler, { passive: false });
    const saved = localStorage.getItem("tauri-zoom");
    if (saved) applyZoom(parseFloat(saved));
    return () => window.removeEventListener("wheel", handler);
  }, [applyZoom]);
}
