// Phase 1 stand-in for the backend. It behaves like the real service will:
// network delay, quota accounting, one background job at a time, item-by-item processing,
// rollback for "move and remove likes", and errors. State is kept in localStorage so a
// running job and its results survive a page reload.
import type { LikeCleanerApi } from '../api'
import { ApiError } from '../errors'
import { isRetryable } from '../jobSummary'
import { estimateUnits, maxAffordableItems, MAX_SELECTION, pagesFor, QUOTA_COST } from '../quotaEstimate'
import type { ApiErrorInfo, CreateJobInput, Job, JobItem, Playlist, PlaylistItem, User, Video } from '../types'
import { avatarFor, generateAccount, thumbnailFor } from './data'
import type { MockAccount, MockPlaylist, MockPlaylistItem } from './data'
import { getDevSettings, setDevSettings } from './devSettings'
import { load, save } from './storage'

const STATE_KEY = 'likecleaner.mock.state.v1'
const DAILY_QUOTA = 10_000
/** Units "other users" already used today in a fresh mock (header shows 7,450 / 10,000). */
const INITIAL_USED = 2_550
/** Time the worker spends on each job item. */
const ITEM_DELAY_MS = 350
/** Chance that a write call fails in `some_failures` mode. */
const FAILURE_CHANCE = 0.15
const KEEP_JOBS = 20
/** Waits before each automatic retry after a 429 (DECISIONS.md 28). */
const RATE_LIMIT_BACKOFF_S = [2, 4, 8]
/** Which item of a test job hits the 429, so some progress shows first. */
const RATE_LIMIT_ITEM_INDEX = 2

const MOCK_USER = {
  id: 'mock-user-1',
  email: 'alex.kim@example.com',
  name: 'Alex Kim',
  pictureUrl: avatarFor('Alex Kim'),
}

interface MockState {
  account: MockAccount
  signedIn: boolean
  quota: { dayPt: string; used: number }
  jobs: Job[]
  /** When the worker last processed an item; used to catch up after the tab was closed. */
  workerLastTick: number
  /** Dev-panel 429 tests: per job, which item gets 429 and how many more times. */
  rateLimitPlans?: Record<string, { itemIndex: number; failuresLeft: number }>
}

// ---------- errors ----------

const ERR = {
  quotaExceeded: {
    status: 403,
    reason: 'quotaExceeded',
    message: 'The request cannot be completed because you have exceeded your quota.',
  },
  videoNotFound: {
    status: 404,
    reason: 'videoNotFound',
    message: 'The video that you are trying to rate cannot be found.',
  },
  playlistItemNotFound: {
    status: 404,
    reason: 'playlistItemNotFound',
    message: 'The playlist item identified with the request cannot be found.',
  },
  backendError: { status: 500, reason: 'backendError', message: 'Backend Error' },
  rateLimitExceeded: { status: 429, reason: 'rateLimitExceeded', message: 'Rate Limit Exceeded' },
  manualSortRequired: {
    status: 400,
    reason: 'manualSortRequired',
    message: 'The playlist must be manually sorted to set the position of items.',
  },
  notSignedIn: { status: 401, reason: 'notSignedIn', message: 'Please sign in to continue.' },
  accessDenied: {
    status: 403,
    reason: 'accessDenied',
    message: "This Google account doesn't have access to LikeCleaner.",
  },
  playlistNotFound: {
    status: 404,
    reason: 'playlistNotFound',
    message: 'The playlist could not be found.',
  },
  jobNotFound: { status: 404, reason: 'jobNotFound', message: 'The job could not be found.' },
  jobAlreadyRunning: {
    status: 409,
    reason: 'jobAlreadyRunning',
    message: 'Another job is already running. Wait for it to finish.',
  },
  noItems: { status: 400, reason: 'noItems', message: 'Select at least one video.' },
  tooManyItems: {
    status: 400,
    reason: 'tooManyItems',
    message: `You can select up to ${MAX_SELECTION} videos at a time.`,
  },
  nothingToRetry: { status: 400, reason: 'nothingToRetry', message: 'There are no failed items to retry.' },
} satisfies Record<string, ApiErrorInfo>

const isQuotaError = (e: ApiErrorInfo | null | undefined) => e?.reason === 'quotaExceeded'

// ---------- time (quota resets at midnight US Pacific) ----------

function pacificParts(date: Date) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Los_Angeles',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? '0'
  return { day: `${get('year')}-${get('month')}-${get('day')}`, h: +get('hour'), m: +get('minute'), s: +get('second') }
}

const todayPacific = () => pacificParts(new Date()).day

function nextResetIso(): string {
  const now = new Date()
  const { h, m, s } = pacificParts(now)
  const msIntoDay = ((h * 60 + m) * 60 + s) * 1000 + now.getMilliseconds()
  return new Date(now.getTime() + 86_400_000 - msIntoDay).toISOString()
}

// ---------- state ----------

function freshState(): MockState {
  return {
    account: generateAccount(),
    signedIn: false,
    quota: { dayPt: todayPacific(), used: INITIAL_USED },
    jobs: [],
    workerLastTick: Date.now(),
  }
}

let state: MockState = load<MockState>(STATE_KEY) ?? freshState()
const persist = () => save(STATE_KEY, state)

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))
/** Pretend some liked videos were deleted or made private (DECISIONS.md 59). */
const MOCK_HIDDEN_LIKES = 3
const latency = (base = 250) => wait(base + Math.random() * 250)
const clone = <T>(value: T): T => structuredClone(value)

function rolloverQuota() {
  const today = todayPacific()
  if (state.quota.dayPt !== today) state.quota = { dayPt: today, used: 0 }
}

/**
 * One YouTube API call: charges `units` (failed calls are charged too, SPEC.md 4-1)
 * and returns an error, or null on success. Calls over the limit return quotaExceeded.
 */
function callYouTube(units: number, failWith?: ApiErrorInfo): ApiErrorInfo | null {
  rolloverQuota()
  if (state.quota.used + units > DAILY_QUOTA) return ERR.quotaExceeded
  state.quota.used += units
  return failWith ?? null
}

/** In `some_failures` mode, returns `error` some of the time. */
function maybeFail(error: ApiErrorInfo, chance = FAILURE_CHANCE): ApiErrorInfo | undefined {
  return getDevSettings().failureMode === 'some_failures' && Math.random() < chance ? error : undefined
}

function requireActive() {
  if (!state.signedIn) throw new ApiError(ERR.notSignedIn)
  if (getDevSettings().userStatus !== 'active') throw new ApiError(ERR.accessDenied)
}

/** For read calls: charge quota or throw. */
function chargeOrThrow(units: number) {
  const err = callYouTube(units)
  if (err) {
    persist()
    throw new ApiError(err)
  }
}

function findPlaylist(id: string | undefined): MockPlaylist {
  const playlist = state.account.playlists.find((p) => p.id === id)
  if (!playlist) throw new ApiError(ERR.playlistNotFound)
  return playlist
}

const unavailableTitle = (kind: 'deleted' | 'private') => (kind === 'deleted' ? 'Deleted video' : 'Private video')

function toVideo(id: string): Video {
  const v = state.account.videos[id]
  return { ...v, thumbnailUrl: thumbnailFor(v.channelTitle) }
}

function toPlaylistItem(item: MockPlaylistItem, position: number): PlaylistItem {
  if (item.unavailable) {
    return {
      playlistItemId: item.id,
      position,
      videoId: item.videoId,
      title: unavailableTitle(item.unavailable),
      availability: item.unavailable,
      channelTitle: null,
      categoryName: null,
      durationSeconds: null,
      publishedAt: null,
      thumbnailUrl: null,
    }
  }
  const v = toVideo(item.videoId)
  return {
    playlistItemId: item.id,
    position,
    videoId: v.id,
    title: v.title,
    availability: 'available',
    channelTitle: v.channelTitle,
    categoryName: v.categoryName,
    durationSeconds: v.durationSeconds,
    publishedAt: v.publishedAt,
    thumbnailUrl: v.thumbnailUrl,
  }
}

// ---------- background worker ----------

let workerTimer: ReturnType<typeof setTimeout> | null = null
/** Move jobs whose duplicate check (playlistItems.list) has already been charged. */
const checkedJobs = new Set<string>()
/** Playlists that refused `position=0` once; later adds skip the doomed first attempt. */
const autoSortedPlaylists = new Set<string>()
let itemSeq = 0

const runningJob = () => state.jobs.find((j) => j.status === 'running')

function scheduleWorker() {
  if (!workerTimer && runningJob()) workerTimer = setTimeout(workerTick, ITEM_DELAY_MS)
}

function workerTick() {
  workerTimer = null
  processNextItem()
  state.workerLastTick = Date.now()
  persist()
  scheduleWorker()
}

function finish(job: Job, status: Job['status']) {
  job.status = status
  job.finishedAt = new Date().toISOString()
}

function processNextItem() {
  const job = runningJob()
  if (!job) return
  const index = job.items.findIndex((i) => i.status === 'pending')
  if (index === -1) return finish(job, 'completed')

  // Waiting out a 429 before the next automatic retry.
  if (job.rateLimit && Date.now() < Date.parse(job.rateLimit.retryAt)) return

  if (getDevSettings().failureMode === 'quota_exceeded' && index >= Math.floor(job.items.length / 2)) {
    state.quota.used = DAILY_QUOTA
  }

  const fatal = rateLimitedCall(job, index) ?? processItem(job, job.items[index])
  if (fatal?.reason === 'rateLimitExceeded' && job.items[index].status === 'pending') {
    // 429: retry the same item after 2 s, 4 s, 8 s; after the third retry fails, stop (DECISIONS.md 28).
    const retriesDone = job.rateLimit?.attempt ?? 0
    if (retriesDone < RATE_LIMIT_BACKOFF_S.length) {
      job.rateLimit = {
        attempt: retriesDone + 1,
        retryAt: new Date(Date.now() + RATE_LIMIT_BACKOFF_S[retriesDone] * 1000).toISOString(),
      }
      return
    }
  }
  if (job.items[index].status !== 'pending' || !fatal) delete job.rateLimit

  if (fatal) {
    // quotaExceeded, or 429 after all retries: stop and mark everything left as not processed (SPEC.md 8-3).
    delete job.rateLimit
    job.fatalError = fatal
    for (const item of job.items) if (item.status === 'pending') item.status = 'not_processed'
    finish(job, 'stopped')
  } else if (job.items.every((i) => i.status !== 'pending')) {
    finish(job, 'completed')
  }
}

/**
 * Dev-panel 429 test: the planned item's first API call gets 429 (and still uses quota,
 * like any failed call). Returns the 429, or null when this call goes through normally.
 */
function rateLimitedCall(job: Job, index: number): ApiErrorInfo | null {
  const plan = state.rateLimitPlans?.[job.id]
  if (!plan || plan.itemIndex !== index || plan.failuresLeft <= 0) return null
  plan.failuresLeft -= 1
  return callYouTube(QUOTA_COST.rate, ERR.rateLimitExceeded)
}

const removeLike = (videoId: string) => {
  state.account.likedIds = state.account.likedIds.filter((id) => id !== videoId)
}

function fail(item: JobItem, error: ApiErrorInfo): null {
  item.status = 'failed'
  item.error = error
  return null
}

/** Unlikes one video. Returns a fatal (quota) error, or null. */
function unlikeItem(item: JobItem): ApiErrorInfo | null {
  const err = callYouTube(QUOTA_COST.rate, maybeFail(ERR.videoNotFound))
  if (isQuotaError(err)) return err
  if (err) return fail(item, err)
  removeLike(item.videoId)
  item.status = 'success'
  return null
}

/** Processes one item. Leaves it `pending` and returns the error if the job must stop. */
function processItem(job: Job, item: JobItem): ApiErrorInfo | null {
  if (job.type === 'remove_like') return unlikeItem(item)

  const playlist = state.account.playlists.find((p) => p.id === job.targetPlaylistId)
  if (!playlist) return fail(item, ERR.playlistNotFound)

  if (job.type === 'playlist_remove') {
    const err = callYouTube(QUOTA_COST.delete, maybeFail(ERR.playlistItemNotFound))
    if (isQuotaError(err)) return err
    if (err) return fail(item, err)
    playlist.items = playlist.items.filter((i) => i.id !== item.playlistItemId)
    item.status = 'success'
    return null
  }

  // move / move_and_unlike: check what is already in the playlist once, at the start
  // (playlistItems.list pages + videos.list pages for details, like the backend, DECISIONS.md 63).
  if (!checkedJobs.has(job.id)) {
    const available = playlist.items.filter((i) => !i.unavailable).length
    const err = callYouTube((pagesFor(playlist.items.length) + (available ? pagesFor(available) : 0)) * QUOTA_COST.listPage)
    if (err) return err
    checkedJobs.add(job.id)
  }

  if (playlist.items.some((i) => i.videoId === item.videoId)) {
    if (job.type === 'move') {
      item.status = 'skipped'
      return null
    }
    return unlikeItem(item) // already there: only remove the like
  }

  // 1. Add at the top; auto-sorted playlists refuse a position, so add again without one.
  let atTop = !autoSortedPlaylists.has(playlist.id)
  let err = atTop
    ? callYouTube(QUOTA_COST.insert, playlist.manualSort ? maybeFail(ERR.backendError) : ERR.manualSortRequired)
    : callYouTube(QUOTA_COST.insert, maybeFail(ERR.backendError))
  if (err?.reason === 'manualSortRequired') {
    autoSortedPlaylists.add(playlist.id)
    atTop = false
    err = callYouTube(QUOTA_COST.insert, maybeFail(ERR.backendError))
  }
  if (isQuotaError(err)) return err
  if (err) return fail(item, err)
  const added: MockPlaylistItem = { id: `PLI${Date.now().toString(36)}${itemSeq++}`, videoId: item.videoId }
  if (atTop) playlist.items.unshift(added)
  else playlist.items.push(added)

  if (job.type === 'move') {
    item.status = 'success'
    return null
  }

  // 2. Remove the like. 3. If that fails, take the video back out of the playlist (SPEC.md 6-7).
  const unlikeErr = callYouTube(QUOTA_COST.rate, maybeFail(ERR.backendError))
  if (!unlikeErr) {
    removeLike(item.videoId)
    item.status = 'success'
    return null
  }
  const rollbackErr = callYouTube(QUOTA_COST.delete, maybeFail(ERR.backendError, 0.3))
  if (!rollbackErr) {
    playlist.items = playlist.items.filter((i) => i.id !== added.id)
    fail(item, unlikeErr)
  } else {
    // 4. The only state the user has to check by hand.
    item.status = 'rollback_failed'
    item.error = rollbackErr
  }
  return isQuotaError(unlikeErr) || isQuotaError(rollbackErr) ? ERR.quotaExceeded : null
}

/** Jobs keep running while the tab is closed: on load, process what would have happened meanwhile. */
function catchUp() {
  const missedTicks = Math.floor((Date.now() - state.workerLastTick) / ITEM_DELAY_MS)
  for (let i = 0; i < missedTicks && runningJob(); i++) processNextItem()
  state.workerLastTick = Date.now()
  persist()
  scheduleWorker()
}

catchUp()

// ---------- jobs ----------

function buildItems(input: CreateJobInput): { items: JobItem[]; playlist?: MockPlaylist } {
  if (input.type === 'playlist_remove') {
    const playlist = findPlaylist(input.playlistId)
    const items = [...new Set(input.playlistItemIds)].map((playlistItemId): JobItem => {
      const entry = playlist.items.find((i) => i.id === playlistItemId)
      if (!entry) throw new ApiError(ERR.playlistItemNotFound)
      const title = entry.unavailable ? unavailableTitle(entry.unavailable) : state.account.videos[entry.videoId].title
      return { videoId: entry.videoId, videoTitle: title, playlistItemId, status: 'pending' }
    })
    return { items, playlist }
  }
  const playlist = input.type === 'remove_like' ? undefined : findPlaylist(input.targetPlaylistId)
  const items = [...new Set(input.videoIds)].map((videoId): JobItem => ({
    videoId,
    videoTitle: state.account.videos[videoId]?.title ?? videoId,
    status: 'pending',
  }))
  return { items, playlist }
}

// ---------- the API ----------

const currentUser = (): User => ({ ...MOCK_USER, status: getDevSettings().userStatus })

export const mockApi: LikeCleanerApi = {
  async getCurrentUser() {
    await latency(150)
    return state.signedIn ? currentUser() : null
  },

  async signIn() {
    await latency(400)
    state.signedIn = true
    persist()
    return currentUser()
  },

  async signOut() {
    await latency(150)
    state.signedIn = false
    persist()
  },

  async getQuota() {
    await latency(100)
    rolloverQuota()
    const resetsAt = nextResetIso()
    return {
      limit: DAILY_QUOTA,
      used: state.quota.used,
      remaining: Math.max(0, DAILY_QUOTA - state.quota.used),
      resetsAt,
      resetsInSeconds: Math.max(0, Math.round((Date.parse(resetsAt) - Date.now()) / 1000)),
    }
  },

  async getLikedVideos(options) {
    requireActive()
    // Like the real loader: one page of 50 at a time, with progress (DECISIONS.md 59).
    const total = state.account.likedIds.length + MOCK_HIDDEN_LIKES
    for (let loaded = 0; loaded < total; loaded = Math.min(total, loaded + 50)) {
      options?.onProgress?.(loaded)
      await latency(80)
    }
    options?.onProgress?.(total)
    requireActive()
    // The like count, playlistItems.list(LL) + videos.list per page, and one videoCategories.list call
    chargeOrThrow(pagesFor(total) * 2 * QUOTA_COST.listPage + 2 * QUOTA_COST.listPage)
    persist()
    // The mock account is small enough to read whole, so there is no "about 5,000" notice.
    return { videos: state.account.likedIds.map(toVideo), hiddenUnavailable: MOCK_HIDDEN_LIKES, totalLiked: total }
  },

  async getPlaylists() {
    await latency()
    requireActive()
    chargeOrThrow(pagesFor(state.account.playlists.length) * QUOTA_COST.listPage)
    persist()
    return state.account.playlists.map((p): Playlist => ({ id: p.id, title: p.title, itemCount: p.items.length }))
  },

  async getPlaylistItems(playlistId) {
    await latency(500)
    requireActive()
    const playlist = findPlaylist(playlistId)
    // playlistItems.list pages + videos.list pages for category and duration (DECISIONS.md 6)
    const available = playlist.items.filter((i) => !i.unavailable).length
    chargeOrThrow((pagesFor(playlist.items.length) + (available ? pagesFor(available) : 0)) * QUOTA_COST.listPage)
    persist()
    return playlist.items.map(toPlaylistItem)
  },

  async createJob(input) {
    await latency()
    requireActive()
    if (runningJob()) throw new ApiError(ERR.jobAlreadyRunning)

    const { items, playlist } = buildItems(input)
    if (items.length === 0) throw new ApiError(ERR.noItems)
    if (items.length > MAX_SELECTION) throw new ApiError(ERR.tooManyItems)

    rolloverQuota()
    const unitsLeft = DAILY_QUOTA - state.quota.used
    const targetSize = playlist?.items.length ?? 0
    if (estimateUnits(input.type, items.length, targetSize) > unitsLeft) {
      const max = maxAffordableItems(input.type, unitsLeft, targetSize)
      throw new ApiError({
        status: 403,
        reason: 'notEnoughQuota',
        message: `Not enough quota. You can process up to ${max} items today.`,
      })
    }

    const job: Job = {
      id: `job_${Date.now().toString(36)}`,
      type: input.type,
      targetPlaylistId: playlist?.id,
      targetPlaylistTitle: playlist?.title,
      status: 'running',
      createdAt: new Date().toISOString(),
      items,
    }
    state.jobs = [...state.jobs, job].slice(-KEEP_JOBS)

    // Dev panel "Next action": 429 test for this job only (DECISIONS.md 28).
    const { nextAction } = getDevSettings()
    if (nextAction !== 'none') {
      state.rateLimitPlans = {
        [job.id]: {
          itemIndex: Math.min(RATE_LIMIT_ITEM_INDEX, items.length - 1),
          // recovers: fails on the first try and the first retry, then the second retry succeeds.
          failuresLeft: nextAction === 'rate_limit_recovers' ? 2 : RATE_LIMIT_BACKOFF_S.length + 1,
        },
      }
      setDevSettings({ nextAction: 'none' })
    }
    state.workerLastTick = Date.now()
    persist()
    scheduleWorker()
    return clone(job)
  },

  async retryFailedItems(jobId) {
    const job = state.jobs.find((j) => j.id === jobId)
    if (!job) throw new ApiError(ERR.jobNotFound)
    const retry = job.items.filter((i) => isRetryable(i.status))
    if (retry.length === 0) throw new ApiError(ERR.nothingToRetry)
    if (job.type === 'playlist_remove') {
      return mockApi.createJob({
        type: 'playlist_remove',
        playlistId: job.targetPlaylistId!,
        playlistItemIds: retry.map((i) => i.playlistItemId!),
      })
    }
    const videoIds = retry.map((i) => i.videoId)
    return job.type === 'remove_like'
      ? mockApi.createJob({ type: 'remove_like', videoIds })
      : mockApi.createJob({ type: job.type, videoIds, targetPlaylistId: job.targetPlaylistId! })
  },

  async getLatestJob() {
    await latency(100)
    const job = state.jobs.at(-1)
    return job ? clone(job) : null
  },
}

// ---------- Phase 1 dev tools (DECISIONS.md 14) ----------

/** Puts the fake YouTube account, quota and jobs back to their starting state. */
export function resetMockData() {
  if (workerTimer) clearTimeout(workerTimer)
  workerTimer = null
  checkedJobs.clear()
  autoSortedPlaylists.clear()
  state = freshState()
  persist()
}

/** Sets today's remaining quota, to try the "Not enough quota" warnings. */
export function setQuotaLeft(unitsLeft: number) {
  rolloverQuota()
  state.quota.used = DAILY_QUOTA - Math.max(0, Math.min(DAILY_QUOTA, unitsLeft))
  persist()
}
