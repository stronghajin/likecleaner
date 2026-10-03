import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../services'
import type { User, UserStatus } from '../services'

interface Session {
  /** undefined while the first check is still loading. */
  user: User | null | undefined
  signIn: () => Promise<User>
  signOut: () => Promise<void>
  /** Re-reads the user (e.g. after the dev panel changes the approval status). */
  refresh: () => Promise<void>
}

const SessionContext = createContext<Session | null>(null)

/** Where each approval status lands after sign-in (SPEC.md 3-2). */
export const HOME_FOR_STATUS: Record<UserStatus, string> = {
  approved: '/liked',
  pending: '/pending',
  rejected: '/denied',
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null | undefined>(undefined)

  const refresh = useCallback(() => api.getCurrentUser().then(setUser, () => setUser(null)), [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const signIn = useCallback(async () => {
    const signedIn = await api.signIn()
    setUser(signedIn)
    return signedIn
  }, [])

  const signOut = useCallback(async () => {
    await api.signOut()
    setUser(null)
  }, [])

  return <SessionContext value={{ user, signIn, signOut, refresh }}>{children}</SessionContext>
}

export function useSession(): Session {
  const session = useContext(SessionContext)
  if (!session) throw new Error('useSession must be used inside SessionProvider')
  return session
}
