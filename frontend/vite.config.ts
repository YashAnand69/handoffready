import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:8877", changeOrigin: true } },
  },
  test: { environment: "jsdom" },
});
