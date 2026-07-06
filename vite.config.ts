import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  root: "frontend",
  plugins: [react()],
  build: {
    outDir: "../dist",
    emptyOutDir: true
  },
  resolve: {
    alias: {
      "@shared": resolve(__dirname, "frontend/src/shared")
    }
  }
});

