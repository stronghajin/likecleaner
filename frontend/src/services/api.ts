import type { CreateJobInput, Job, Playlist, PlaylistItem, Quota, User, Video } from './types'

/**
 * Everything the screens can ask for. Phase 1 implements this with mock data (`mock/mockApi.ts`);
 * Phase 2 swaps in an implementation that calls the FastAPI backend.
 * Every method rejects with `ApiError` on failure.
 *
 * Each method notes what replaces it in Phase 2:
 *   backend endpoint → YouTube / Google call behind it → quota units (SPEC.md 4-2).
 */
export interface LikeCleanerApi {
  /**
   * Signed-in user (with approval status), or null when signed out.
   * Phase 2: GET /api/me → no YouTube call (session + `users` table) → 0 units.
   */
  getCurrentUser(): Promise<User | null>

  /**
   * Phase 2: GET /api/auth/google/login → Google OAuth step 1 (`openid email profile`), then for
   * approved users GET /api/auth/google/youtube → step 2 (`youtube` scope, access_type=offline)
   * (SPEC.md 3-2) → 0 units. In Phase 2 this becomes a full-page redirect, not a Promise<User>.
   */
  signIn(): Promise<User>

  /**
   * Ends the session only; Google tokens are not revoked (SPEC.md 3-4).
   * Phase 2: POST /api/auth/logout → no Google call → 0 units.
   */
  signOut(): Promise<void>

  /**
   * Phase 2: GET /api/quota → no YouTube call (sums today's `quota_usage` rows, PT day) → 0 units.
   */
  getQuota(): Promise<Quota>

  /**
   * Loads the full liked list from YouTube (uses quota). Call once after sign-in and on Resync;
   * filtering, sorting and paging happen on the returned list.
   * Phase 2: GET /api/likes → `videos.list` (myRating=like, part=snippet,contentDetails,
   * maxResults=50, every page) + `videoCategories.list` → 1 unit per 50 videos + 1
   * (about 21 units for 1,000 likes).
   */
  getLikedVideos(): Promise<Video[]>

  /**
   * Phase 2: GET /api/playlists → `playlists.list` (mine=true, part=snippet,contentDetails,
   * maxResults=50, every page) → 1 unit per 50 playlists.
   */
  getPlaylists(): Promise<Playlist[]>

  /**
   * Loads every item of one playlist (uses quota). Call on open and on Resync.
   * Phase 2: GET /api/playlists/{playlistId}/items → `playlistItems.list` (every page) + `videos.list`
   * (id=…, for category and duration, DECISIONS.md 6) → 1 unit per 50 items + 1 unit per 50
   * available videos.
   */
  getPlaylistItems(playlistId: string): Promise<PlaylistItem[]>

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
