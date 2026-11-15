import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs on :8000; /api is proxied so the app and API share an origin.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000", "/verify": "http://127.0.0.1:8000", "/survey": "http://127.0.0.1:8000" } },
});
