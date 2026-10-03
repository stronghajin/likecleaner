import type { CreateJobInput, Job, Playlist, PlaylistItem, Quota, User, Video } from './types'

/**
 * Everything the screens can ask for. Phase 1 implements this with mock data;
 * Phase 2 swaps in an implementation that calls the FastAPI backend.
 * Every method rejects with `ApiError` on failure.
 */
export interface LikeCleanerApi {
  /** Signed-in user (with approval status), or null when signed out. */
  getCurrentUser(): Promise<User | null>
  signIn(): Promise<User>
  /** Ends the session only; Google tokens are not revoked. */
  signOut(): Promise<void>

  getQuota(): Promise<Quota>

  /**
   * Loads the full liked list from YouTube (uses quota). Call once after sign-in and on Resync;
   * filtering, sorting and paging happen on the returned list.
   */
  getLikedVideos(): Promise<Video[]>
  getPlaylists(): Promise<Playlist[]>
  /** Loads every item of one playlist (uses quota). Call on open and on Resync. */
  getPlaylistItems(playlistId: string): Promise<PlaylistItem[]>

  /** Starts a background job. Fails if a job is already running or quota is not enough. */
  createJob(input: CreateJobInput): Promise<Job>
  /** Starts a new job with the failed and not-processed items of `jobId`. */
  retryFailedItems(jobId: string): Promise<Job>
  /** The most recent job (running or finished), or null. Poll this while a job runs. */
  getLatestJob(): Promise<Job | null>
}
