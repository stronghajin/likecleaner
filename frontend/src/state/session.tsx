import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, onSessionEnded } from '../services'
import type { User, UserStatus } from '../services'

interface Session {
  /** undefined while the first check is still loading. */
  user: User | null | undefined
  signIn: () => Promise<User>
  signOut: () => Promise<void>
  /** Re-reads the user (e.g. after the dev panel changes the user status). */
  refresh: () => Promise<void>
  /** True after the server ended the session while the app was open (DECISIONS.md 64). */
  sessionEnded: boolean
}

const SessionContext = createContext<Session | null>(null)

/** Where each user status lands after sign-in (DECISIONS.md 56). */
export const HOME_FOR_STATUS: Record<UserStatus, string> = {
  active: '/liked',
  disabled: '/denied',
  not_registered: '/denied',
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null | undefined>(undefined)
  const [sessionEnded, setSessionEnded] = useState(false)

  const refresh = useCallback(() => api.getCurrentUser().then(setUser, () => setUser(null)), [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // Signed out by the server (7 days passed, or the YouTube permission was cut): back to the sign-in screen.
  // Sign out here too, so the next sign-in starts clean and asks for YouTube access again if needed.
  useEffect(
    () =>
      onSessionEnded(() => {
        setSessionEnded(true)
        api.signOut().catch(() => {})
        setUser(null)
      }),
    [],
  )

  const signIn = useCallback(async () => {
    const signedIn = await api.signIn()
    setSessionEnded(false)
    setUser(signedIn)
    return signedIn
  }, [])

  const signOut = useCallback(async () => {
    await api.signOut()
    setUser(null)
  }, [])

  return <SessionContext value={{ user, signIn, signOut, refresh, sessionEnded }}>{children}</SessionContext>
}

export function useSession(): Session {
  const session = useContext(SessionContext)
  if (!session) throw new Error('useSession must be used inside SessionProvider')
  return session
}
