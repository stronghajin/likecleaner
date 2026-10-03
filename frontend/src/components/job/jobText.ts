import type { ApiErrorInfo, Job } from '../../services'

/** Panel heading for each kind of job. */
export function jobTitle(job: Job): string {
  const target = `"${job.targetPlaylistTitle ?? 'playlist'}"`
  switch (job.type) {
    case 'remove_like':
      return 'Removing likes'
    case 'move':
      return `Moving to ${target}`
    case 'move_and_unlike':
      return `Moving to ${target} and removing likes`
    case 'playlist_remove':
      return `Removing from ${target}`
  }
}

/** "Error 403 · quotaExceeded · The request cannot be completed…" (SPEC.md 8-3). */
export const formatApiError = (e: ApiErrorInfo) => `Error ${e.status} · ${e.reason} · ${e.message}`
