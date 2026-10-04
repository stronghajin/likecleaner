// The real backend (Phase 2). Sign-in (P2-3) and reading (P2-4) are connected; jobs arrive in P2-5.
import type { LikeCleanerApi } from '../api'
import { ApiError } from '../errors'
import type { ApiErrorInfo, LikedVideosResult, Playlist, PlaylistItem, Quota, User } from '../types'
import { request } from './http'

function notAvailableYet(): Promise<never> {
  return Promise.reject(
    new ApiError({ status: 501, reason: 'notAvailableYet', message: 'This part is not connected to the server yet.' }),
  )
}

const refreshQuery = (refresh?: boolean) => (refresh ? '?refresh=true' : '')

/** Progress of the background liked-list load on the server (DECISIONS.md 59). */
interface LikesLoadStatus {
  state: 'idle' | 'loading' | 'ready' | 'error'
  loaded: number
  hiddenUnavailable: number
  error: ApiErrorInfo | null
}

const LIKES_POLL_MS = 1000
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const realApi: LikeCleanerApi = {
  async getCurrentUser() {
    try {
      return await request<User>('GET', '/api/me')
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return null
      throw e
    }
  },

  signIn() {
    // Full-page trip through Google; the app reloads at "/" afterwards, so this never resolves.
    window.location.assign('/api/auth/google/login')
    return new Promise<User>(() => {})
  },

  async signOut() {
    await request<void>('POST', '/api/auth/logout')
  },

  getQuota() {
    return request<Quota>('GET', '/api/quota')
  },

  async getLikedVideos(options) {
    // Start (or join) the load, follow its progress, then fetch the finished list.
    let status = await request<LikesLoadStatus>('POST', `/api/likes/load${refreshQuery(options?.refresh)}`)
    while (status.state === 'loading') {
      options?.onProgress?.(status.loaded)
      await wait(LIKES_POLL_MS)
      status = await request<LikesLoadStatus>('GET', '/api/likes/status')
    }
    if (status.state === 'error' && status.error) throw new ApiError(status.error)
    options?.onProgress?.(status.loaded)
    return request<LikedVideosResult>('GET', '/api/likes')
  },

  getPlaylists() {
    return request<Playlist[]>('GET', '/api/playlists')
  },

  getPlaylistItems(playlistId, options) {
    return request<PlaylistItem[]>(
      'GET',
      `/api/playlists/${encodeURIComponent(playlistId)}/items${refreshQuery(options?.refresh)}`,
    )
  },

  createJob: notAvailableYet,
  retryFailedItems: notAvailableYet,
  getLatestJob: notAvailableYet,
}
