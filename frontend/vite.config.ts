import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Production builds use the real backend only, so the mock is left out (DECISIONS.md 47, 64).
    alias:
      command === 'build'
        ? [
            {
              find: /^\.\/source$/,
              replacement: fileURLToPath(new URL('./src/services/source.production.ts', import.meta.url)),
            },
          ]
        : [],
  },
  server: {
    // One address for the browser: /api goes to the FastAPI backend (DECISIONS.md 35).
    proxy: { '/api': 'http://localhost:8000' },
  },
}))
