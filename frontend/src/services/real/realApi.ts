// The real backend (Phase 2). Sign-in (P2-3) and reading (P2-4) are connected; jobs arrive in P2-5.
import type { LikeCleanerApi } from '../api'
import { ApiError } from '../errors'
import type { Playlist, PlaylistItem, Quota, User, Video } from '../types'
import { request } from './http'

function notAvailableYet(): Promise<never> {
  return Promise.reject(
    new ApiError({ status: 501, reason: 'notAvailableYet', message: 'This part is not connected to the server yet.' }),
  )
}

const refreshQuery = (refresh?: boolean) => (refresh ? '?refresh=true' : '')

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

  getLikedVideos(options) {
    return request<Video[]>('GET', `/api/likes${refreshQuery(options?.refresh)}`)
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
