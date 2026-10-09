// API base URL resolution (fleet CORS rule, §1F).
//
// Same-origin relative ("") by default so browser tabs go through the vite
// `/api` proxy (works from localhost, LAN names, and Tailscale MagicDNS).
// An absolute backend URL is used ONLY when running inside the Tauri WebView
// (no vite proxy there) or when VITE_API_URL is set explicitly. A hardcoded
// absolute URL in a plain browser tab dies on CORS anywhere off localhost.

function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as unknown as Record<string, unknown>;
  return (
    "__TAURI__" in window ||
    "__TAURI_INTERNALS__" in w ||
    window.location.protocol === "tauri:"
  );
}

const ENV_BASE =
  (typeof import.meta !== "undefined" &&
    (import.meta.env?.VITE_API_URL as string | undefined)) ||
  "";

const TAURI_FALLBACK = "http://127.0.0.1:11028";

const API_BASE: string = ENV_BASE || (isTauri() ? TAURI_FALLBACK : "");

export default API_BASE;
