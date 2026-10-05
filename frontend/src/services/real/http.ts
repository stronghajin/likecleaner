// Calls to the FastAPI backend. Same origin: Vite proxies /api in development (DECISIONS.md 35).
import { ApiError } from '../errors'
import { reportError } from '../sessionEvents'
import type { ApiErrorInfo } from '../types'

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as Partial<ApiErrorInfo>
    if (typeof body.reason === 'string' && typeof body.message === 'string') {
      return new ApiError({ status: response.status, reason: body.reason, message: body.message })
    }
  } catch {
    // Not JSON (e.g. the backend is not running and the proxy answered).
  }
  return new ApiError({ status: response.status, reason: 'backendUnavailable', message: 'The server is not responding.' })
}

/**
 * One call to the backend. Failures become ApiError; a 401 or youtubeReauthRequired also ends the session
 * on screen (DECISIONS.md 64), except where the caller handles it (`quietSessionEnd`, e.g. /api/me).
 */
export async function request<T>(
  method: 'GET' | 'POST',
  path: string,
  body?: unknown,
  { quietSessionEnd = false } = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError({ status: 0, reason: 'networkError', message: 'Could not reach the server.' })
  }
  if (!response.ok) {
    const error = await toApiError(response)
    if (!quietSessionEnd) reportError(error)
    throw error
  }
  return (response.status === 204 ? undefined : await response.json()) as T
}
