import type { ApiErrorInfo } from './types'

/** Thrown by every service call that fails. Screens show status, reason and message. */
export class ApiError extends Error implements ApiErrorInfo {
  status: number
  reason: string

  constructor({ status, reason, message }: ApiErrorInfo) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.reason = reason
  }

  toInfo(): ApiErrorInfo {
    return { status: this.status, reason: this.reason, message: this.message }
  }
}
