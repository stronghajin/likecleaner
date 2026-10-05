// The only door between screens and data. Screens import from 'services', never from 'services/mock' or 'services/real'.
import { isMockMode } from './source'

/**
 * Mock or real backend (DECISIONS.md 47): `api`, `isMockMode` and the DEV panel's `devTools`.
 * Production builds always use the real backend, without any mock code (DECISIONS.md 64).
 */
export { api, devTools, isMockMode } from './source'

/** How often a running job is polled: 1.5 s against the real backend (DECISIONS.md 48). */
export const JOB_POLL_MS = isMockMode ? 700 : 1500

export type { DevSettings, FailureMode, NextAction } from './mock/devSettings'

export type { LikeCleanerApi, LikedLoadOptions, LoadOptions } from './api'
export { ApiError } from './errors'
export { onSessionEnded } from './sessionEvents'
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
