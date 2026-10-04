/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 'real' = use the FastAPI backend in development (`npm run dev:real`). */
  readonly VITE_API_MODE?: 'mock' | 'real'
}
