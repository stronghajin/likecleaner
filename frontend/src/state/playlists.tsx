import { createContext, useCallback, useContext, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { PageSize } from '../components/Pagination'
import { api } from '../services'
import type { Playlist, PlaylistItem } from '../services'
import { useQuota } from './quota'
import { useSelection } from './selection'

// Playlists screen data (SPEC.md 7). Like the liked list, loaded data is kept while signed in so
// moving between menus does not use quota again; Resync reloads the open playlist.

interface PlaylistsState {
  playlists: Playlist[] | null
  playlistsError: string
  /** Loads the playlist list if it has not been loaded yet, or is out of date. */
  ensurePlaylists: () => void

  activeId: string | null
  /** Opens a playlist: clears the selection and loads its items if needed. */
  openPlaylist: (id: string) => void
  /** Items of the open playlist, in playlist order. null while loading. */
  items: PlaylistItem[] | null
  itemsLoading: boolean
  itemsError: string
  resync: () => void

  pageSize: PageSize
  page: number
  setPage: (page: number) => void
  setPageSize: (size: PageSize) => void

  /** Selected playlistItemIds of the open playlist. */
  selection: ReturnType<typeof useSelection>

  /** After a removal job: takes removed entries out without reloading. */
  removeItems: (playlistId: string, playlistItemIds: string[]) => void
  /** After videos were added to a playlist: reload it (and the counts) next time it is shown. */
  invalidate: (playlistId: string) => void
}

const PlaylistsContext = createContext<PlaylistsState | null>(null)

export function PlaylistsProvider({ children }: { children: ReactNode }) {
  const { refreshQuota } = useQuota()
  const [playlists, setPlaylists] = useState<Playlist[] | null>(null)
  const [playlistsError, setPlaylistsError] = useState('')
  const [itemsById, setItemsById] = useState<Record<string, PlaylistItem[]>>({})
  const [activeId, setActiveId] = useState<string | null>(null)
  const [itemsLoading, setItemsLoading] = useState(false)
  const [itemsError, setItemsError] = useState('')
  const [pageSize, setPageSizeState] = useState<PageSize>(20)
  const [page, setPage] = useState(1)
  const selection = useSelection()
  const { clear: clearSelection, keepOnly, deselect } = selection

  const playlistsLoading = useRef(false)
  const playlistsStale = useRef(true)

  const ensurePlaylists = useCallback(() => {
    if (!playlistsStale.current || playlistsLoading.current) return
    playlistsLoading.current = true
    setPlaylistsError('')
    api
      .getPlaylists()
      .then(
        (loaded) => {
          playlistsStale.current = false
          setPlaylists(loaded)
        },
        (e: Error) => setPlaylistsError(e.message),
      )
      .finally(() => {
        playlistsLoading.current = false
        refreshQuota()
      })
  }, [refreshQuota])

  const loadItems = useCallback(
    (id: string, refresh = false) => {
      setItemsLoading(true)
      setItemsError('')
      api
        .getPlaylistItems(id, { refresh })
        .then(
          (loaded) => {
            setItemsById((current) => ({ ...current, [id]: loaded }))
            setPlaylists(
              (current) => current?.map((p) => (p.id === id ? { ...p, itemCount: loaded.length } : p)) ?? null,
            )
            keepOnly(new Set(loaded.map((i) => i.playlistItemId)))
          },
          (e: Error) => setItemsError(e.message),
        )
        .finally(() => {
          setItemsLoading(false)
          refreshQuota()
        })
    },
    [refreshQuota, keepOnly],
  )

  const openPlaylist = useCallback(
    (id: string) => {
      if (id === activeId) return
      setActiveId(id)
      setPage(1)
      clearSelection()
      setItemsError('')
      if (!itemsById[id]) loadItems(id)
    },
    [activeId, itemsById, loadItems, clearSelection],
  )

  const resync = useCallback(() => {
    if (activeId) loadItems(activeId, true)
  }, [activeId, loadItems])

  const removeItems = useCallback(
    (playlistId: string, playlistItemIds: string[]) => {
      if (playlistItemIds.length === 0) return
      const gone = new Set(playlistItemIds)
      const list = itemsById[playlistId]
      if (!list || !list.some((i) => gone.has(i.playlistItemId))) return
      const kept = list.filter((i) => !gone.has(i.playlistItemId)).map((i, position) => ({ ...i, position }))
      setItemsById((current) => ({ ...current, [playlistId]: kept }))
      setPlaylists(
        (current) => current?.map((p) => (p.id === playlistId ? { ...p, itemCount: kept.length } : p)) ?? null,
      )
      deselect(playlistItemIds)
    },
    [itemsById, deselect],
  )

  const invalidate = useCallback(
    (playlistId: string) => {
      playlistsStale.current = true
      setItemsById((current) => {
        if (!current[playlistId]) return current
        const rest = { ...current }
        delete rest[playlistId]
        return rest
      })
      if (playlistId === activeId) loadItems(playlistId)
    },
    [activeId, loadItems],
  )

  const setPageSize = (size: PageSize) => {
    setPageSizeState(size)
    setPage(1)
  }

  return (
    <PlaylistsContext
      value={{
        playlists,
        playlistsError,
        ensurePlaylists,
        activeId,
        openPlaylist,
        items: activeId ? (itemsById[activeId] ?? null) : null,
        itemsLoading,
        itemsError,
        resync,
        pageSize,
        page,
        setPage,
        setPageSize,
        selection,
        removeItems,
        invalidate,
      }}
    >
      {children}
    </PlaylistsContext>
  )
}

export function usePlaylists(): PlaylistsState {
  const state = useContext(PlaylistsContext)
  if (!state) throw new Error('usePlaylists must be used inside PlaylistsProvider')
  return state
}
