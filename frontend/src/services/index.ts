// The only door between screens and data. Screens import from 'services', never from 'services/mock' or 'services/real'.
import type { LikeCleanerApi } from './api'
import { getDevSettings, setDevSettings } from './mock/devSettings'
import { mockApi, resetMockData, setQuotaLeft } from './mock/mockApi'
import { realApi } from './real/realApi'

/**
 * Mock or real backend (DECISIONS.md 47). `npm run dev` = mock, `npm run dev:real` = real.
 * Production builds always use the real backend.
 */
export const isMockMode = import.meta.env.DEV && import.meta.env.VITE_API_MODE !== 'real'

export const api: LikeCleanerApi = isMockMode ? mockApi : realApi

/** Mock mode only: switches for the DEV panel (DECISIONS.md 14, 28, 47). */
export const devTools = { getDevSettings, setDevSettings, resetMockData, setQuotaLeft }
export type { DevSettings, FailureMode, NextAction } from './mock/devSettings'

export type { LikeCleanerApi, LikedLoadOptions, LoadOptions } from './api'
export { ApiError } from './errors'
export { isRetryable, summarizeJob } from './jobSummary'
export type { JobCounts } from './jobSummary'
export {
  estimateUnits,
  FIRST_LIKES_LOAD_UNITS,
  likesLoadUnits,
  MAX_SELECTION,
  maxAffordableItems,
  playlistLoadUnits,
  QUOTA_COST,
} from './quotaEstimate'
export type * from './types'
