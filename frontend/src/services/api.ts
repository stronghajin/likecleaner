import type { CreateJobInput, Job, LikedVideosResult, Playlist, PlaylistItem, Quota, User } from './types'

/**
 * Everything the screens can ask for. Phase 1 implements this with mock data (`mock/mockApi.ts`);
 * Phase 2 swaps in an implementation that calls the FastAPI backend.
 * Every method rejects with `ApiError` on failure.
 *
 * Each method notes what replaces it in Phase 2:
 *   backend endpoint → YouTube / Google call behind it → quota units (SPEC.md 4-2).
 */
export interface LoadOptions {
  /** Resync: load again from YouTube even if the server still has the list in memory. */
  refresh?: boolean
}

export interface LikedLoadOptions extends LoadOptions {
  /** Called while loading with how many liked entries have been read so far. */
  onProgress?: (loaded: number) => void
}

export interface LikeCleanerApi {
  /**
   * Signed-in user (with status, DECISIONS.md 56), or null when signed out.
   * Phase 2: GET /api/me → no YouTube call (session + `users` table) → 0 units.
   */
  getCurrentUser(): Promise<User | null>

  /**
   * Phase 2: GET /api/auth/google/login → Google OAuth step 1 (`openid email profile`), then for
   * active users GET /api/auth/google/youtube → step 2 (`youtube` scope, access_type=offline)
   * (SPEC.md 3-2) → 0 units. In Phase 2 this becomes a full-page redirect, not a Promise<User>.
   */
  signIn(): Promise<User>

  /**
   * Ends the session only; Google tokens are not revoked (SPEC.md 3-4).
   * Phase 2: POST /api/auth/logout → no Google call → 0 units.
   */
  signOut(): Promise<void>

  /**
   * GET /api/quota → no YouTube call (sums today's `quota_usage` rows, PT day) → 0 units.
   */
  getQuota(): Promise<Quota>

  /**
   * Loads every liked video (uses quota). Call once after sign-in and on Resync (`refresh: true`);
   * filtering, sorting and paging happen on the returned list. Without `refresh` the server may answer
   * from its memory at 0 units (DECISIONS.md 58). Deleted/private videos are only counted (DECISIONS.md 59).
   * Real API: POST /api/likes/load, GET /api/likes/status until ready, GET /api/likes →
   * `playlistItems.list` (playlistId=LL, every page) + `videos.list` (id=…, per page) +
   * `videoCategories.list` → about 2 units per 50 likes + 1 (about 195 units for 4,900 likes).
   */
  getLikedVideos(options?: LikedLoadOptions): Promise<LikedVideosResult>

  /**
   * Phase 2: GET /api/playlists → `playlists.list` (mine=true, part=snippet,contentDetails,
   * maxResults=50, every page) → 1 unit per 50 playlists.
   */
  getPlaylists(): Promise<Playlist[]>

  /**
   * Loads every item of one playlist (uses quota). Call on open and on Resync (`refresh: true`).
   * Without `refresh` the server may answer from its memory at 0 units (DECISIONS.md 58).
   * Phase 2: GET /api/playlists/{playlistId}/items → `playlistItems.list` (every page) + `videos.list`
   * (id=…, for category and duration, DECISIONS.md 6) → 1 unit per 50 items + 1 unit per 50
   * available videos.
   */
  getPlaylistItems(playlistId: string, options?: LoadOptions): Promise<PlaylistItem[]>

  /**
   * Starts a background job. Fails if a job is already running or quota is not enough.
   * Phase 2: POST /api/jobs → the background worker calls, one item at a time:
   *   - remove_like: `videos.rate` (rating=none) → 50 per video
   *   - move: `playlistItems.list` (duplicate check) + `playlistItems.insert` (position=0) → 1 per 50
   *     playlist items + 50 per video (+50 once if the playlist is auto-sorted, DECISIONS.md 30)
   *   - move_and_unlike: the same as move + `videos.rate` → +50 per video; if that fails,
   *     `playlistItems.delete` rolls the add back → +50 (SPEC.md 6-7)
   *   - playlist_remove: `playlistItems.delete` → 50 per item
   *   A 429 is retried after 2 s, 4 s and 8 s, and each retry is charged too (DECISIONS.md 28).
   */
  createJob(input: CreateJobInput): Promise<Job>

  /**
   * Starts a new job with the failed and not-processed items of `jobId` (DECISIONS.md 10).
   * Phase 2: POST /api/jobs/{jobId}/retry → same YouTube calls and units as createJob for those items.
   */
  retryFailedItems(jobId: string): Promise<Job>

  /**
   * The most recent job (running or finished), or null. Poll this while a job runs.
   * Phase 2: GET /api/jobs/latest → no YouTube call (`jobs` and `job_items` tables) → 0 units.
   */
  getLatestJob(): Promise<Job | null>
}
