import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../services'
import type { PageSize } from '../components/Pagination'
import type { Video } from '../services'
import { useQuota } from './quota'
import { useSelection } from './selection'

// The liked list is loaded once after sign-in and kept while signed in (SPEC.md 6-1),
// so moving between menus does not reload it (and use quota). Resync loads it again (6-3).

export type SortKey = 'liked' | 'duration_asc' | 'duration_desc' | 'date_desc' | 'date_asc'

/** What the list shows. Kept while signed in, so it survives moving between menus (DECISIONS.md 24). */
export interface LikedVideosView {
  query: string
  /** '' = all channels */
  channel: string
  /** '' = all categories */
  category: string
  sort: SortKey
  pageSize: PageSize
  page: number
}

export const DEFAULT_VIEW: LikedVideosView = {
  query: '',
  channel: '',
  category: '',
  sort: 'liked',
  pageSize: 20,
  page: 1,
}

interface LikedVideosState {
  /** null until the first load finishes. */
  videos: Video[] | null
  loading: boolean
  error: string
  resync: () => Promise<void>
  view: LikedVideosView
  /** Changing anything other than the page goes back to page 1. */
  updateView: (patch: Partial<LikedVideosView>) => void
  /** Selected video IDs. Kept across pages, filters and menus (DECISIONS.md 1). */
  selectedIds: ReadonlySet<string>
  /** Adds videos in order until the limit is reached. Returns false if some could not be added. */
  select: (ids: string[]) => boolean
  deselect: (ids: string[]) => void
  /** Deselects everything, on every page (DECISIONS.md 26). */
  clearSelection: () => void
  /** Takes videos out of the list (and the selection) after their likes were removed. */
  removeVideos: (ids: string[]) => void
}

const LikedVideosContext = createContext<LikedVideosState | null>(null)

export function LikedVideosProvider({ children }: { children: ReactNode }) {
  const { refreshQuota } = useQuota()
  const [videos, setVideos] = useState<Video[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const started = useRef(false)
  const [view, setView] = useState<LikedVideosView>(DEFAULT_VIEW)

  const updateView = useCallback((patch: Partial<LikedVideosView>) => {
    setView((current) => ({ ...current, page: 1, ...patch }))
  }, [])

  const { selectedIds, select, deselect, keepOnly, clear: clearSelection } = useSelection()

  const removeVideos = useCallback(
    (ids: string[]) => {
      if (ids.length === 0) return
      const gone = new Set(ids)
      setVideos((current) =>
        current && current.some((v) => gone.has(v.id)) ? current.filter((v) => !gone.has(v.id)) : current,
      )
      deselect(ids)
    },
    [deselect],
  )

  const resync = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const loaded = await api.getLikedVideos()
      setVideos(loaded)
      // Drop selections for videos that are no longer liked.
      const stillLiked = new Set(loaded.map((v) => v.id))
      keepOnly(stillLiked)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      refreshQuota()
    }
  }, [refreshQuota, keepOnly])

  useEffect(() => {
    // Load once only: every load uses quota.
    if (started.current) return
    started.current = true
    resync()
  }, [resync])

  return (
    <LikedVideosContext
      value={{
        videos,
        loading,
        error,
        resync,
        view,
        updateView,
        selectedIds,
        select,
        deselect,
        clearSelection,
        removeVideos,
      }}
    >
      {children}
    </LikedVideosContext>
  )
}

export function useLikedVideos(): LikedVideosState {
  const state = useContext(LikedVideosContext)
  if (!state) throw new Error('useLikedVideos must be used inside LikedVideosProvider')
  return state
}
