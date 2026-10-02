// Vite configuration for the PolicyLens frontend.
//
// The proxy forwards any request starting with /api to the FastAPI backend.
// That way the browser sees one origin, so we don't need CORS setup on the server.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
