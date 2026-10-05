// Production build: the real backend only. Replaces `source.ts` at build time (vite.config.ts, DECISIONS.md 64),
// so the mock and the DEV panel tools are not in the files we ship.
import type { LikeCleanerApi } from './api'
import type { devTools as DevTools } from './source'
import { realApi } from './real/realApi'

export const isMockMode = false

export const api: LikeCleanerApi = realApi

function mockOnly(): never {
  throw new Error('The DEV panel tools exist only in mock mode.')
}

export const devTools: typeof DevTools = {
  getDevSettings: mockOnly,
  setDevSettings: mockOnly,
  resetMockData: mockOnly,
  setQuotaLeft: mockOnly,
}
