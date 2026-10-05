import { useEffect, useState } from 'react'
import RemoveFromPlaylistDialog from '../components/actions/RemoveFromPlaylistDialog'
import Button from '../components/Button'
import Pagination from '../components/Pagination'
import ResyncButton from '../components/ResyncButton'
import SelectionBar from '../components/SelectionBar'
import VideoTable from '../components/VideoTable'
import YouTubeLink from '../components/YouTubeLink'
import { MAX_SELECTION, playlistLoadUnits } from '../services'
import type { Job, PlaylistItem } from '../services'
import { useJob } from '../state/job'
import { usePlaylists } from '../state/playlists'
import { formatNumber } from '../utils/format'
import { playlistUrl } from '../utils/youtubeLinks'

// Playlists (SPEC.md 7): pick a playlist, then clean it up. No search, filters or sorting (DECISIONS.md 5).

const LIMIT_NOTICE = `You can select up to ${MAX_SELECTION} videos at a time.`
const NOTICE_MS = 5000
const JOB_RUNNING_HINT = 'Available when the current job finishes'

/** Every copy of a video after its first appearance (SPEC.md 7-2: keep the earliest one). */
function duplicateEntries(items: PlaylistItem[]): PlaylistItem[] {
  const seen = new Set<string>()
  return items.filter((item) => {
    if (item.availability !== 'available') return false
    if (seen.has(item.videoId)) return true
    seen.add(item.videoId)
    return false
  })
}

const unavailableEntries = (items: PlaylistItem[]) => items.filter((i) => i.availability !== 'available')

export default function PlaylistsPage() {
  const {
    playlists,
    playlistsError,
    ensurePlaylists,
    activeId,
    openPlaylist,
    items,
    itemsLoading,
    itemsError,
    resync,
    pageSize,
    page,
    setPage,
    setPageSize,
    selection,
  } = usePlaylists()
  const { selectedIds, select, replace, deselect, clear } = selection
  const { running, trackJob } = useJob()
  const [limitNotice, setLimitNotice] = useState('')
  const [info, setInfo] = useState('')
  const [confirming, setConfirming] = useState(false)

  useEffect(ensurePlaylists, [ensurePlaylists])

  // Messages belong to the playlist they were about.
  const showPlaylist = (id: string) => {
    setInfo('')
    setLimitNotice('')
    openPlaylist(id)
  }

  useEffect(() => {
    if (!limitNotice && !info) return
    const timer = setTimeout(() => {
      setLimitNotice('')
      setInfo('')
    }, NOTICE_MS)
    return () => clearTimeout(timer)
  }, [limitNotice, info])

  const active = playlists?.find((p) => p.id === activeId) ?? null
  const all = items ?? []
  const watchable = all.filter((i) => i.availability === 'available')
  const pageCount = Math.max(1, Math.ceil(all.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const start = (currentPage - 1) * pageSize
  const pageRows = all.slice(start, start + pageSize)
  const pageIds = pageRows.map((i) => i.playlistItemId)

  const trySelect = (ids: string[]) => {
    if (!select(ids)) setLimitNotice(LIMIT_NOTICE)
  }
  const toggle = (id: string) => (selectedIds.has(id) ? deselect([id]) : trySelect([id]))

  /** Remove Duplicates / Remove Unavailable Videos: select the targets for review, never delete directly. */
  const autoSelect = (found: PlaylistItem[], what: string) => {
    setLimitNotice('')
    if (found.length === 0) {
      clear()
      setInfo(`No ${what} found.`)
      return
    }
    const allFit = replace(found.map((i) => i.playlistItemId))
    if (allFit) {
      setInfo(`Selected ${formatNumber(found.length)} ${what}. Review them, then click Remove Selected.`)
    } else {
      // DECISIONS.md 7: first 100 now, the rest in a later run.
      setInfo(
        `Selected the first ${MAX_SELECTION} of ${formatNumber(found.length)} ${what}. Run this again after removing them for the rest.`,
      )
    }
  }

  const onJobStarted = (job: Job) => {
    setConfirming(false)
    clear()
    trackJob(job)
  }

  return (
    <>
      <h1 className="text-xl font-semibold">Playlists</h1>

      <div className="mt-5 grid grid-cols-[260px_minmax(0,1fr)] items-start gap-6">
        {/* Playlist list (SPEC.md 7-1) */}
        <nav aria-label="Your playlists" className="sticky top-22 border bg-panel">
          {!playlists && !playlistsError && <p className="p-4 text-muted">Loading your playlists…</p>}
          {playlistsError && (
            <div className="p-4">
              <p className="text-danger">{playlistsError}</p>
              <Button className="mt-3" onClick={ensurePlaylists}>
                Try again
              </Button>
            </div>
          )}
          {playlists?.length === 0 && <p className="p-4 text-muted">You have no playlists.</p>}
          {playlists && playlists.length > 0 && (
            <ul>
              {playlists.map((p) => {
                const isActive = p.id === activeId
                return (
                  <li
                    key={p.id}
                    className={`flex items-center border-b last:border-b-0 ${isActive ? 'bg-accent text-bg' : ''}`}
                  >
                    <button
                      type="button"
                      onClick={() => showPlaylist(p.id)}
                      aria-current={isActive ? 'true' : undefined}
                      className={`flex min-w-0 flex-1 items-center justify-between gap-3 py-3 pr-2 pl-4 text-left ${
                        isActive ? '' : 'hover:bg-text/5'
                      }`}
                    >
                      <span className="truncate font-medium">{p.title}</span>
                      <span className={`shrink-0 text-xs tabular-nums ${isActive ? '' : 'text-muted'}`}>
                        {formatNumber(p.itemCount)}
                      </span>
                    </button>
                    {/* Next to the button, not inside it: a link cannot sit in a button (DECISIONS.md 60). */}
                    <span className={`shrink-0 pr-2 ${isActive ? '[&_a]:text-bg/70 [&_a:hover]:text-bg' : ''}`}>
                      <YouTubeLink href={playlistUrl(p.id)} label={`Open ${p.title} on YouTube`} />
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </nav>

        <section className="min-w-0">
          {!active && <div className="border bg-panel p-6 text-muted">Choose a playlist to see its videos.</div>}

          {active && (
            <>
              <div className="flex items-baseline justify-between gap-4">
                <h2 className="truncate text-lg font-semibold">{active.title}</h2>
                <p className="shrink-0 text-muted">
                  <span className="font-bold text-accent">Videos:</span> {formatNumber(active.itemCount)}
                </p>
              </div>

              {/* Selection and cleanup tools (SPEC.md 7-2) */}
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Button
                  className="h-9 py-0"
                  onClick={() => trySelect(pageIds)}
                  disabled={!items || pageIds.every((id) => selectedIds.has(id))}
                >
                  Select all
                </Button>
                <Button
                  className="h-9 py-0"
                  onClick={() => deselect(pageIds)}
                  disabled={!items || pageIds.every((id) => !selectedIds.has(id))}
                >
                  Deselect all
                </Button>
                <span className="mx-1 h-5 w-px bg-border" />
                <Button
                  className="h-9 py-0"
                  onClick={() => autoSelect(duplicateEntries(all), 'duplicate videos')}
                  disabled={!items}
                >
                  Remove Duplicates
                </Button>
                <Button
                  className="h-9 py-0"
                  onClick={() => autoSelect(unavailableEntries(all), 'deleted or private videos')}
                  disabled={!items}
                >
                  Remove Unavailable Videos
                </Button>
              </div>
              {info && (
                <p role="status" className="mt-2 text-muted">
                  {info}
                </p>
              )}

              {/* Count, paging and Resync above the list (DECISIONS.md 23) */}
              <div className="mt-4 flex items-center justify-end gap-4">
                {items && (
                  <span className="text-muted tabular-nums">
                    {all.length === 0
                      ? '0 videos'
                      : `${formatNumber(start + 1)}–${formatNumber(start + pageRows.length)} of ${formatNumber(all.length)}`}
                  </span>
                )}
                <Pagination
                  page={currentPage}
                  pageCount={pageCount}
                  pageSize={pageSize}
                  onPageChange={setPage}
                  onPageSizeChange={setPageSize}
                />
                <ResyncButton
                  units={playlistLoadUnits(all.length, new Set(watchable.map((i) => i.videoId)).size)}
                  onClick={resync}
                  loading={itemsLoading && items !== null}
                  disabled={itemsLoading}
                />
              </div>

              <div className="mt-3 border bg-panel">
                {!items && itemsLoading && <p className="p-6 text-muted">Loading videos…</p>}
                {itemsError && <p className="p-6 text-danger">{itemsError}</p>}
                {items && all.length === 0 && <p className="p-6 text-muted">This playlist is empty.</p>}
                {items && all.length > 0 && (
                  <VideoTable
                    rows={pageRows.map((i) => ({
                      key: i.playlistItemId,
                      videoId: i.videoId,
                      title: i.title,
                      channelTitle: i.channelTitle,
                      categoryName: i.categoryName,
                      durationSeconds: i.durationSeconds,
                      publishedAt: i.publishedAt,
                      thumbnailUrl: i.thumbnailUrl,
                      unavailable: i.availability !== 'available',
                    }))}
                    selectedKeys={selectedIds}
                    onToggle={toggle}
                  />
                )}
              </div>
            </>
          )}
        </section>
      </div>

      {selectedIds.size > 0 && <div className="h-24" />}
      <SelectionBar count={selectedIds.size} notice={limitNotice}>
        <Button
          variant="secondary"
          onClick={() => setConfirming(true)}
          disabled={running}
          title={running ? JOB_RUNNING_HINT : undefined}
        >
          Remove Selected
        </Button>
        <span className="h-5 w-px bg-border" />
        <Button variant="ghost" onClick={clear}>
          Clear selection
        </Button>
      </SelectionBar>

      {confirming && active && (
        <RemoveFromPlaylistDialog
          playlist={active}
          items={all
            .filter((i) => selectedIds.has(i.playlistItemId))
            .map((i) => ({ id: i.playlistItemId, title: i.title }))}
          onDeselect={deselect}
          onClose={() => setConfirming(false)}
          onStarted={onJobStarted}
        />
      )}
    </>
  )
}
