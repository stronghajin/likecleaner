import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // One address for the browser: /api goes to the FastAPI backend (DECISIONS.md 35).
    proxy: { '/api': 'http://localhost:8000' },
  },
})
