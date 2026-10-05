import type { JobType } from './types'

// Unit cost per YouTube API call (SPEC.md section 4-2).
export const QUOTA_COST = {
  listPage: 1,
  rate: 50,
  insert: 50,
  delete: 50,
} as const

export const MAX_SELECTION = 100
export const LIST_PAGE_SIZE = 50

export const pagesFor = (count: number) => Math.max(1, Math.ceil(count / LIST_PAGE_SIZE))

/**
 * Worst-case units for an action (SPEC.md 4-3): includes lookup calls, excludes rollback.
 * `targetItemCount` is the destination playlist size, needed for the duplicate check of move jobs.
 * Move jobs also count one failed "add at the top" call, in case the playlist is auto-sorted (SPEC.md 6-6).
 */
export function estimateUnits(type: JobType, count: number, targetItemCount = 0): number {
  const moveSetup = pagesFor(targetItemCount) * QUOTA_COST.listPage + QUOTA_COST.insert
  switch (type) {
    case 'remove_like':
      return count * QUOTA_COST.rate
    case 'move':
      return moveSetup + count * QUOTA_COST.insert
    case 'move_and_unlike':
      return moveSetup + count * (QUOTA_COST.insert + QUOTA_COST.rate)
    case 'playlist_remove':
      return count * QUOTA_COST.delete
  }
}

/** How many items fit in the remaining quota ("You can process up to N items today."). */
export function maxAffordableItems(type: JobType, unitsLeft: number, targetItemCount = 0): number {
  const fixed = estimateUnits(type, 0, targetItemCount)
  const perItem = estimateUnits(type, 1, targetItemCount) - fixed
  return Math.max(0, Math.min(MAX_SELECTION, Math.floor((unitsLeft - fixed) / perItem)))
}

/**
 * Loading the liked list (DECISIONS.md 59, 61): the like count, then per 50 likes one LL page and one
 * videos.list, plus about one category call. `likedCount` = liked entries read last time.
 */
export const likesLoadUnits = (likedCount: number) => pagesFor(likedCount) * 2 * QUOTA_COST.listPage + 2 * QUOTA_COST.listPage

/** YouTube hands out about 5,000 likes at most, so a first load costs about this much at most (202, rounded). */
export const FIRST_LIKES_LOAD_UNITS = 200

/** Loading one playlist (DECISIONS.md 6): playlistItems.list pages + videos.list pages for watchable videos. */
export function playlistLoadUnits(itemCount: number, watchableCount: number): number {
  return (pagesFor(itemCount) + (watchableCount > 0 ? pagesFor(watchableCount) : 0)) * QUOTA_COST.listPage
}
