import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Flask backend (port 5000) serves the built app from dist/ in
// production; during development Vite proxies the JSON API and file
// routes so the SPA can be worked on with `npm run dev` alone.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/documents": "http://127.0.0.1:5000",
      "/page_image": "http://127.0.0.1:5000",
      "/reports": "http://127.0.0.1:5000",
      "/receipt": "http://127.0.0.1:5000",
      "/agent": "http://127.0.0.1:5000",
      "/ingest": "http://127.0.0.1:5000",
      "/pipeline": "http://127.0.0.1:5000",
    },
  },
  build: { outDir: "dist" },
});
