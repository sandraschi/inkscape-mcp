import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ["goliath"],
    port: 11029,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: "http://127.0.0.1:11062",
        changeOrigin: true,
      },
      "/mcp": {
        target: "http://127.0.0.1:11028",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
