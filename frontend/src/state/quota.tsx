import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../services'
import type { Quota } from '../services'
import { useSession } from './session'

/** The quota is shared by every user, so it is re-read regularly (SPEC.md 4-3). */
const REFRESH_MS = 30_000

interface QuotaState {
  quota: Quota | null
  /** Call after anything that may have used quota. */
  refreshQuota: () => void
}

const QuotaContext = createContext<QuotaState | null>(null)

/** Reads the quota only while an active user is signed in. */
export function QuotaProvider({ children }: { children: ReactNode }) {
  const { user } = useSession()
  const active = user?.status === 'active'
  const [quota, setQuota] = useState<Quota | null>(null)

  const refreshQuota = useCallback(() => {
    api.getQuota().then(setQuota, () => {})
  }, [])

  useEffect(() => {
    if (!active) return
    refreshQuota()
    const timer = setInterval(refreshQuota, REFRESH_MS)
    return () => clearInterval(timer)
  }, [active, refreshQuota])

  return <QuotaContext value={{ quota, refreshQuota }}>{children}</QuotaContext>
}

export function useQuota(): QuotaState {
  const state = useContext(QuotaContext)
  if (!state) throw new Error('useQuota must be used inside QuotaProvider')
  return state
}
