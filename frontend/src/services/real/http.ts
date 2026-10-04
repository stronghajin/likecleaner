// Calls to the FastAPI backend. Same origin: Vite proxies /api in development (DECISIONS.md 35).
import { ApiError } from '../errors'
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

export async function request<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
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
  if (!response.ok) throw await toApiError(response)
  return (response.status === 204 ? undefined : await response.json()) as T
}
