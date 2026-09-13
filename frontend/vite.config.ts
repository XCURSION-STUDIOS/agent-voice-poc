import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Keeps the WebRTC signaling endpoint same-origin in local development.
      "/api": "http://localhost:7860",
    },
  },
});
