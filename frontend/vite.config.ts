import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the FastAPI back-end runs on :8000; proxy /api to it so the
// browser sees a single origin, exactly as on Vercel and in Docker.
export default defineConfig({
  plugins: [react()],
  // Recharts is most of the bundle; one ~600 kB chunk is fine for this app.
  build: { chunkSizeWarningLimit: 800 },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
