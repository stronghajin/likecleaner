import { ApiError } from '../../services'

/** "Error 403 · quotaExceeded · message" (SPEC.md 8-3 format). */
export function errorText(e: unknown): string {
  if (e instanceof ApiError) return `Error ${e.status} · ${e.reason} · ${e.message}`
  return (e as Error)?.message ?? 'Something went wrong.'
}
