// "The session has ended" signal (DECISIONS.md 64): the server answered 401 (signed out, e.g. after
// the 7-day session) or youtubeReauthRequired (the YouTube permission was cut, DECISIONS.md 45).
// The session state listens and sends the user back to the sign-in screen.
import type { ApiErrorInfo } from './types'

type Listener = () => void

const listeners = new Set<Listener>()

/** Returns a function that stops listening. */
export function onSessionEnded(listener: Listener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export const endsSession = (error: ApiErrorInfo) => error.status === 401 || error.reason === 'youtubeReauthRequired'

/** Tells the listeners when `error` means the session is over. */
export function reportError(error: ApiErrorInfo): void {
  if (endsSession(error)) for (const listener of listeners) listener()
}
