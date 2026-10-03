// Data shapes shared by the whole app. Screens only ever see these types,
// never the mock data or the real API responses directly.
// Field names follow the DB tables in SPEC.md section 9 where they overlap.

export type UserStatus = 'pending' | 'approved' | 'rejected'

export interface User {
  id: string
  email: string
  name: string
  pictureUrl: string
  status: UserStatus
}

export interface Quota {
  /** Daily limit for the whole GCP project (DAILY_QUOTA). */
  limit: number
  /** Units used today by everyone, including failed calls. */
  used: number
  /** Next reset: midnight US Pacific time (ISO string). */
  resetsAt: string
}

export interface Video {
  id: string
  title: string
  channelId: string
  channelTitle: string
  categoryName: string
  durationSeconds: number
  /** Upload date (ISO string). */
  publishedAt: string
  thumbnailUrl: string
}

export interface Playlist {
  id: string
  title: string
  itemCount: number
}

export type VideoAvailability = 'available' | 'deleted' | 'private'

/** One entry in a playlist. Deleted/private videos have no channel, category, duration or date. */
export interface PlaylistItem {
  /** ID of this entry in the playlist (needed to remove it). */
  playlistItemId: string
  position: number
  videoId: string
  title: string
  availability: VideoAvailability
  channelTitle: string | null
  categoryName: string | null
  durationSeconds: number | null
  publishedAt: string | null
  thumbnailUrl: string | null
}

export type JobType = 'remove_like' | 'move' | 'move_and_unlike' | 'playlist_remove'

/** `stopped` = halted early by a quotaExceeded error. */
export type JobStatus = 'running' | 'completed' | 'stopped'

/** `pending` = not reached yet; the rest are final results (SPEC.md section 9). */
export type JobItemStatus =
  | 'pending'
  | 'success'
  | 'failed'
  | 'skipped'
  | 'rollback_failed'
  | 'not_processed'

export interface ApiErrorInfo {
  /** HTTP status code, e.g. 403 */
  status: number
  /** Error reason, e.g. quotaExceeded */
  reason: string
  message: string
}

export interface JobItem {
  videoId: string
  videoTitle: string
  /** Only for playlist_remove jobs. */
  playlistItemId?: string
  status: JobItemStatus
  error?: ApiErrorInfo
}

export interface Job {
  id: string
  type: JobType
  /** Destination for move jobs, or the playlist being cleaned for playlist_remove. */
  targetPlaylistId?: string
  targetPlaylistTitle?: string
  status: JobStatus
  createdAt: string
  finishedAt?: string
  items: JobItem[]
  /** The error that stopped the job (shown as a popup). */
  fatalError?: ApiErrorInfo
  /** Set while waiting to retry after a 429 rateLimitExceeded (DECISIONS.md 28). */
  rateLimit?: {
    /** Which retry comes next: 1, 2 or 3. */
    attempt: number
    /** When the retry happens (ISO string). */
    retryAt: string
  }
}

export type CreateJobInput =
  | { type: 'remove_like'; videoIds: string[] }
  | { type: 'move' | 'move_and_unlike'; videoIds: string[]; targetPlaylistId: string }
  | { type: 'playlist_remove'; playlistId: string; playlistItemIds: string[] }
