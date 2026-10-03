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

export interface DevSettings {
  userStatus: UserStatus
  failureMode: FailureMode
}

const KEY = 'likecleaner.mock.devSettings'
const DEFAULTS: DevSettings = { userStatus: 'approved', failureMode: 'none' }

let current: DevSettings = { ...DEFAULTS, ...load<Partial<DevSettings>>(KEY) }

export function getDevSettings(): DevSettings {
  return { ...current }
}

export function setDevSettings(patch: Partial<DevSettings>): DevSettings {
  current = { ...current, ...patch }
  save(KEY, current)
  return getDevSettings()
}
