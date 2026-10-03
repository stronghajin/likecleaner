// Phase 1 only (DECISIONS.md 14): switches for trying every screen without a backend.
// Removed in Phase 2.
import type { UserStatus } from '../types'
import { load, save } from './storage'

export type FailureMode =
  /** Every call succeeds. */
  | 'none'
  /** Some items fail (and some rollbacks fail) so the failed list and Retry Failed can be tried. */
  | 'some_failures'
  /** Quota runs out halfway through the next job. */
  | 'quota_exceeded'

export type NextAction =
  | 'none'
  /** The next job hits 429 twice, then the retry succeeds. */
  | 'rate_limit_recovers'
  /** The next job hits 429 on every retry and stops. */
  | 'rate_limit_persists'

export interface DevSettings {
  userStatus: UserStatus
  failureMode: FailureMode
  /** One-shot: applies to the next job only, then goes back to 'none'. */
  nextAction: NextAction
}

const KEY = 'likecleaner.mock.devSettings'
const DEFAULTS: DevSettings = { userStatus: 'approved', failureMode: 'none', nextAction: 'none' }

let current: DevSettings = { ...DEFAULTS, ...load<Partial<DevSettings>>(KEY) }

export function getDevSettings(): DevSettings {
  return { ...current }
}

export function setDevSettings(patch: Partial<DevSettings>): DevSettings {
  current = { ...current, ...patch }
  save(KEY, current)
  return getDevSettings()
}
