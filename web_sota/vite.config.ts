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
    allowedHosts: ['goliath'],
    port: 10899,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      '/mcp': {
        target: 'http://127.0.0.1:10900',
        changeOrigin: true,
        ws: true,
      },
      '/api': {
        target: 'http://127.0.0.1:10900',
        changeOrigin: true,
      },
    }
  }
});
