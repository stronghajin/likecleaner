// The only door between screens and data. Screens import from 'services', never from 'services/mock'.
// Phase 2: replace `mockApi` with the real backend implementation and delete `devTools`.
import type { LikeCleanerApi } from './api'
import { getDevSettings, setDevSettings } from './mock/devSettings'
import { mockApi, resetMockData, setQuotaLeft } from './mock/mockApi'

export const api: LikeCleanerApi = mockApi

/** Phase 1 only: switches for the DEV panel (DECISIONS.md 14, 28). */
export const devTools = { getDevSettings, setDevSettings, resetMockData, setQuotaLeft }
export type { DevSettings, FailureMode, NextAction } from './mock/devSettings'

export type { LikeCleanerApi } from './api'
export { ApiError } from './errors'
export { isRetryable, summarizeJob } from './jobSummary'
export type { JobCounts } from './jobSummary'
export { estimateUnits, MAX_SELECTION, maxAffordableItems, QUOTA_COST } from './quotaEstimate'
export type * from './types'
