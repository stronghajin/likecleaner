// The real backend (Phase 2). Sign-in is connected (P2-3); the rest arrives in P2-4 and P2-5.
import type { LikeCleanerApi } from '../api'
import { ApiError } from '../errors'
import type { User } from '../types'
import { request } from './http'

function notAvailableYet(): Promise<never> {
  return Promise.reject(
    new ApiError({ status: 501, reason: 'notAvailableYet', message: 'This part is not connected to the server yet.' }),
  )
}

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

  getQuota: notAvailableYet,
  getLikedVideos: notAvailableYet,
  getPlaylists: notAvailableYet,
  getPlaylistItems: notAvailableYet,
  createJob: notAvailableYet,
  retryFailedItems: notAvailableYet,
  getLatestJob: notAvailableYet,
}
