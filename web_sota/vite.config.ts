import path from "path";
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
    port: 10846,
    host: "127.0.0.1",
    proxy: {
      '/mcp': {
        target: 'http://localhost:10847',
        changeOrigin: true,
        ws: true,
      }
    }
  }
});
