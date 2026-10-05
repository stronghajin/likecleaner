import { useEffect, useMemo, useState } from 'react'
import MoveToPlaylistDialog from '../components/actions/MoveToPlaylistDialog'
import RemoveLikeDialog from '../components/actions/RemoveLikeDialog'
import Button from '../components/Button'
import Pagination from '../components/Pagination'
import ResyncButton from '../components/ResyncButton'
import Select from '../components/Select'
import SelectionBar from '../components/SelectionBar'
import VideoTable from '../components/VideoTable'
import { FIRST_LIKES_LOAD_UNITS, likesLoadUnits, MAX_SELECTION } from '../services'
import type { Job, Video } from '../services'
import { useJob } from '../state/job'
import { DEFAULT_VIEW, useLikedVideos } from '../state/likedVideos'
import type { SortKey } from '../state/likedVideos'
import { formatNumber } from '../utils/format'

// Liked Videos (SPEC.md 6-1 to 6-3): search, channel and category filters, sorting and paging,
// all done on the already loaded list, so none of it uses quota. Selection and the action bar: 6-4.

const LIMIT_NOTICE = `You can select up to ${MAX_SELECTION} videos at a time.`
const NOTICE_MS = 4000
const JOB_RUNNING_HINT = 'Available when the current job finishes'

const SORTS: { value: SortKey; label: string }[] = [
  { value: 'liked', label: 'Recently liked' }, // YouTube's own order (DECISIONS.md 3)
  { value: 'duration_asc', label: 'Duration: shortest first' },
  { value: 'duration_desc', label: 'Duration: longest first' },
  { value: 'date_desc', label: 'Upload date: newest first' },
  { value: 'date_asc', label: 'Upload date: oldest first' },
]

const COMPARE: Record<Exclude<SortKey, 'liked'>, (a: Video, b: Video) => number> = {
  duration_asc: (a, b) => a.durationSeconds - b.durationSeconds,
  duration_desc: (a, b) => b.durationSeconds - a.durationSeconds,
  date_desc: (a, b) => b.publishedAt.localeCompare(a.publishedAt),
  date_asc: (a, b) => a.publishedAt.localeCompare(b.publishedAt),
}

/** Options for a filter dropdown: each distinct value with how many videos have it, A to Z. */
function countBy(videos: Video[], key: (v: Video) => string): { value: string; count: number }[] {
  const counts = new Map<string, number>()
  for (const v of videos) counts.set(key(v), (counts.get(key(v)) ?? 0) + 1)
  return [...counts].map(([value, count]) => ({ value, count })).sort((a, b) => a.value.localeCompare(b.value))
}

/** Shown when YouTube did not hand out every like (DECISIONS.md 61). */
const limitNotice = (total: number) =>
  `YouTube lets us read about 5,000 of your ${formatNumber(total)} liked videos. Remove some likes and press Resync to reach older ones.`

/** "Loading your liked videos… 1,250 loaded" (DECISIONS.md 59). */
function loadingText(progress: number | null): string {
  return progress ? `Loading your liked videos… ${formatNumber(progress)} loaded` : 'Loading your liked videos…'
}

export default function LikedVideosPage() {
  const {
    videos,
    loading,
    progress,
    hiddenUnavailable,
    likesBeyondLimit,
    error,
    resync,
    view,
    updateView,
    selectedIds,
    select,
    deselect,
    clearSelection,
  } =
    useLikedVideos()
  const { running, trackJob } = useJob()
  const [dialog, setDialog] = useState<'remove' | 'move' | null>(null)
  const { query, channel, category, sort, pageSize, page } = view
  const [notice, setNotice] = useState('')

  useEffect(() => {
    if (!notice) return
    const timer = setTimeout(() => setNotice(''), NOTICE_MS)
    return () => clearTimeout(timer)
  }, [notice])

  const onJobStarted = (job: Job) => {
    setDialog(null)
    clearSelection()
    trackJob(job)
  }

  /** Selects, or shows the limit message when the 100 limit stops some of them (DECISIONS.md 2). */
  const trySelect = (ids: string[]) => {
    if (!select(ids)) setNotice(LIMIT_NOTICE)
  }

  const all = useMemo(() => videos ?? [], [videos])
  const channels = useMemo(() => countBy(all, (v) => v.channelTitle), [all])
  // Selected videos in the order they were selected, for the confirm dialogs (DECISIONS.md 29).
  const selectedEntries = useMemo(() => {
    const byId = new Map(all.map((v) => [v.id, v]))
    return [...selectedIds].map((id) => ({ id, title: byId.get(id)?.title ?? id }))
  }, [all, selectedIds])
  const categories = useMemo(() => countBy(all, (v) => v.categoryName), [all])

  const filtered = useMemo(() => {
    const words = query.trim().toLowerCase()
    const result = all.filter(
      (v) =>
        (!words || v.title.toLowerCase().includes(words)) &&
        (!channel || v.channelTitle === channel) &&
        (!category || v.categoryName === category),
    )
    return sort === 'liked' ? result : [...result].sort(COMPARE[sort])
  }, [all, query, channel, category, sort])

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const start = (currentPage - 1) * pageSize
  const pageRows = filtered.slice(start, start + pageSize)
  const isFiltered = query.trim() !== '' || channel !== '' || category !== ''
  const canReset = isFiltered || sort !== DEFAULT_VIEW.sort

  const pageIds = pageRows.map((v) => v.id)
  const pageAllSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id))
  const pageNoneSelected = pageIds.every((id) => !selectedIds.has(id))

  const toggle = (id: string) => (selectedIds.has(id) ? deselect([id]) : trySelect([id]))

  const resetFilters = () =>
    updateView({
      query: DEFAULT_VIEW.query,
      channel: DEFAULT_VIEW.channel,
      category: DEFAULT_VIEW.category,
      sort: DEFAULT_VIEW.sort,
    })

  return (
    <>
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold">Liked Videos</h1>
        {videos && (
          <p className="text-muted">
            <span className="font-bold text-accent">Liked videos:</span> {formatNumber(videos.length)}
          </p>
        )}
      </div>

      {/* Search, filters, sort */}
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => updateView({ query: e.target.value })}
          placeholder="Search titles"
          aria-label="Search titles"
          className="h-9 w-72 rounded-sm border bg-panel px-3 outline-none placeholder:text-muted hover:border-muted focus:border-muted"
        />
        <Select
          aria-label="Channel"
          value={channel}
          onChange={(e) => updateView({ channel: e.target.value })}
          className="w-56"
        >
          <option value="">All channels</option>
          {channels.map((c) => (
            <option key={c.value} value={c.value}>
              {c.value} ({c.count})
            </option>
          ))}
        </Select>
        <Select
          aria-label="Category"
          value={category}
          onChange={(e) => updateView({ category: e.target.value })}
          className="w-56"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.value} value={c.value}>
              {c.value} ({c.count})
            </option>
          ))}
        </Select>
        <Select
          aria-label="Sort"
          value={sort}
          onChange={(e) => updateView({ sort: e.target.value as SortKey })}
          className="w-56"
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>
        <Button variant="ghost" className="h-9 py-0" onClick={resetFilters} disabled={!canReset}>
          Reset filters
        </Button>
      </div>

      {/* Selection, then count, paging and Resync, above the list (DECISIONS.md 23) */}
      {videos && (
        <div className="mt-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Button className="h-9 py-0" onClick={() => trySelect(pageIds)} disabled={pageAllSelected}>
              Select all
            </Button>
            <Button className="h-9 py-0" onClick={() => deselect(pageIds)} disabled={pageNoneSelected}>
              Deselect all
            </Button>
            {channel && (
              <Button className="h-9 py-0" onClick={() => trySelect(filtered.map((v) => v.id))}>
                Select all from this channel
              </Button>
            )}
          </div>
          <div className="flex items-center gap-4">
            {hiddenUnavailable > 0 && (
              <span className="text-xs text-muted tabular-nums">
                {formatNumber(hiddenUnavailable)} unavailable {hiddenUnavailable === 1 ? 'video' : 'videos'} hidden
              </span>
            )}
            <span className="text-muted tabular-nums">
              {filtered.length === 0
                ? '0 videos'
                : `${formatNumber(start + 1)}–${formatNumber(start + pageRows.length)} of ${formatNumber(filtered.length)}`}
            </span>
            <Pagination
              page={currentPage}
              pageCount={pageCount}
              pageSize={pageSize}
              onPageChange={(p) => updateView({ page: p })}
              onPageSizeChange={(size) => updateView({ pageSize: size })}
            />
            <ResyncButton
              units={likesLoadUnits(videos.length + hiddenUnavailable)}
              onClick={resync}
              loading={loading}
              jobRunning={running}
            />
          </div>
        </div>
      )}
      {videos && error && <p className="mt-2 text-right text-danger">{error}</p>}

      {videos && likesBeyondLimit > 0 && (
        <p className="mt-3 text-muted">{limitNotice(videos.length + hiddenUnavailable + likesBeyondLimit)}</p>
      )}

      {/* Resync of a long list takes a while: show how far it got (DECISIONS.md 59). */}
      {videos && loading && <p className="mt-3 text-xs text-muted">{loadingText(progress)}</p>}

      <div className="mt-3 border bg-panel">
        {!videos && loading && (
          <div className="p-6">
            <p className="text-muted">{loadingText(progress)}</p>
            {/* DECISIONS.md 62: the first load is not free either. */}
            <p className="mt-1 text-xs text-muted">
              The first load after sign-in uses up to about {formatNumber(FIRST_LIKES_LOAD_UNITS)} units of today's quota.
            </p>
          </div>
        )}
        {!videos && error && (
          <div className="flex items-center gap-4 p-6">
            <p className="text-danger">{error}</p>
            <Button onClick={resync}>Try again</Button>
          </div>
        )}
        {videos && filtered.length === 0 && (
          <p className="p-6 text-muted">{isFiltered ? 'No videos match your filters.' : 'You have no liked videos.'}</p>
        )}
        {videos && filtered.length > 0 && (
          <VideoTable rows={pageRows.map((v) => ({ key: v.id, videoId: v.id, ...v }))} selectedKeys={selectedIds} onToggle={toggle} />
        )}
      </div>

      {selectedIds.size > 0 && <div className="h-24" />}
      <SelectionBar count={selectedIds.size} notice={notice}>
        {/* One job at a time (SPEC.md 8-1). */}
        <Button onClick={() => setDialog('remove')} disabled={running} title={running ? JOB_RUNNING_HINT : undefined}>
          Remove Like
        </Button>
        <Button onClick={() => setDialog('move')} disabled={running} title={running ? JOB_RUNNING_HINT : undefined}>
          Move to Playlist
        </Button>
        <span className="h-5 w-px bg-border" />
        <Button variant="ghost" onClick={clearSelection}>
          Clear selection
        </Button>
      </SelectionBar>

      {dialog === 'remove' && (
        <RemoveLikeDialog
          items={selectedEntries}
          onDeselect={deselect}
          onClose={() => setDialog(null)}
          onStarted={onJobStarted}
        />
      )}
      {dialog === 'move' && (
        <MoveToPlaylistDialog
          items={selectedEntries}
          onDeselect={deselect}
          onClose={() => setDialog(null)}
          onStarted={onJobStarted}
        />
      )}
    </>
  )
}
