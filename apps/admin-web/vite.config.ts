import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  server: {
    port: 5174,
    proxy: {
      "/api": "http://127.0.0.1:9100",
      "/auth": "http://127.0.0.1:9100",
    },
  },
});
