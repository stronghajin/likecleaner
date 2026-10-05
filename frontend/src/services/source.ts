// Where the data comes from in development: the mock or the real backend (DECISIONS.md 47).
// Production builds swap this file for `source.production.ts` (see vite.config.ts), so no mock code ships.
import type { LikeCleanerApi } from './api'
import { getDevSettings, setDevSettings } from './mock/devSettings'
import { mockApi, resetMockData, setQuotaLeft } from './mock/mockApi'
import { realApi } from './real/realApi'

/** `npm run dev` = mock, `npm run dev:real` = real. */
export const isMockMode = import.meta.env.DEV && import.meta.env.VITE_API_MODE !== 'real'

export const api: LikeCleanerApi = isMockMode ? mockApi : realApi

/** Mock mode only: switches for the DEV panel (DECISIONS.md 14, 28, 47). */
export const devTools = { getDevSettings, setDevSettings, resetMockData, setQuotaLeft }
