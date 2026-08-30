import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/help": "http://127.0.0.1:8080",
      "/health": "http://127.0.0.1:8080",
      "/stats": "http://127.0.0.1:8080",
      "/env": "http://127.0.0.1:8080",
      "/command": "http://127.0.0.1:8080",
      "/file": "http://127.0.0.1:8080",
      "/filepc": "http://127.0.0.1:8080",
      "/commandpc": "http://127.0.0.1:8080",
      "/proc": "http://127.0.0.1:8080",
      "/docker": "http://127.0.0.1:8080",
      "/getfile": "http://127.0.0.1:8080",
    },
  },
});
