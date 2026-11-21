import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: the FastAPI layer runs on :8000 (uvicorn dejavu.api:app).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
