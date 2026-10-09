import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: "http://localhost:11029",
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      // main.py --mode http boots InkscapeMCPServer, a second server class
      // with its own hand-duplicated MCP tool registration - not what
      // actually ships. fleet-start.config.ps1's real UvicornTarget is
      // inkscape_mcp.server:app; e2e was silently testing a fork of it.
      command:
        "uv run python -m uvicorn inkscape_mcp.server:app --host 127.0.0.1 --port 11028",
      port: 11028,
      timeout: 45000,
      reuseExistingServer: true,
      env: {
        INKSCAPE_PATH: "C:\\Program Files\\Inkscape\\bin\\inkscape.exe",
        WEB_PORT: "11028",
      },
    },
    {
      // Nothing previously started this at all - "Frontend loads" only ever
      // passed if someone already had `bun run dev` running by hand.
      command: "bun run dev",
      port: 11029,
      timeout: 45000,
      reuseExistingServer: true,
    },
  ],
});
