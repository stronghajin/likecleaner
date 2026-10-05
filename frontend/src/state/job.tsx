import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, JOB_POLL_MS } from '../services'
import type { ApiErrorInfo, Job } from '../services'
import { useLikedVideos } from './likedVideos'
import { usePlaylists } from './playlists'
import { useQuota } from './quota'

// The user's latest job (SPEC.md 8, DECISIONS.md 11–12): loaded on sign-in so results survive a
// reload, polled while it runs, and shown in the progress panel.

const QUOTA_REFRESH_MS = 5000

interface JobState {
  job: Job | null
  /** True while a job runs: new actions and Resync are disabled (SPEC.md 8-1, DECISIONS.md 13). */
  running: boolean
  panelOpen: boolean
  setPanelOpen: (open: boolean) => void
  /** Call with the job a dialog just created. */
  trackJob: (job: Job) => void
  /** The error that stopped a job while the user was watching; shown as a popup (SPEC.md 8-3). */
  fatalError: ApiErrorInfo | null
  dismissFatalError: () => void
}

const JobContext = createContext<JobState | null>(null)

/** Videos whose like was removed by this job, so they leave the liked list. */
function unlikedIds(job: Job): string[] {
  if (job.type !== 'remove_like' && job.type !== 'move_and_unlike') return []
  return job.items.filter((i) => i.status === 'success').map((i) => i.videoId)
}

/** Playlist entries this job removed, so they leave the playlist list. */
function removedEntryIds(job: Job): string[] {
  if (job.type !== 'playlist_remove') return []
  return job.items.filter((i) => i.status === 'success' && i.playlistItemId).map((i) => i.playlistItemId!)
}

export function JobProvider({ children }: { children: ReactNode }) {
  const { removeVideos } = useLikedVideos()
  const { removeItems, refreshFromServer } = usePlaylists()
  const { refreshQuota } = useQuota()
  // Latest list updaters, read through a ref so `apply` stays stable and effects do not re-run.
  const updaters = useRef({ removeVideos, removeItems, refreshFromServer })
  useEffect(() => {
    updaters.current = { removeVideos, removeItems, refreshFromServer }
  })
  const [job, setJob] = useState<Job | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)
  const [fatalError, setFatalError] = useState<ApiErrorInfo | null>(null)
  const lastQuotaRefresh = useRef(0)
  /** Mirrors `job`, to compare each poll with the one before. */
  const jobRef = useRef<Job | null>(null)
  const running = job?.status === 'running'

  const apply = useCallback(
    (next: Job | null) => {
      const previous = jobRef.current
      jobRef.current = next
      setJob(next)
      if (!next) return
      const { removeVideos, removeItems, refreshFromServer } = updaters.current
      removeVideos(unlikedIds(next))
      if (next.targetPlaylistId) removeItems(next.targetPlaylistId, removedEntryIds(next))
      const justEnded = previous?.id === next.id && previous.status === 'running' && next.status !== 'running'
      if (justEnded) {
        refreshQuota()
        // Videos were added: take the playlist as the server now has it, without asking YouTube,
        // which shows changes only after a few seconds (DECISIONS.md 55).
        if (next.targetPlaylistId && (next.type === 'move' || next.type === 'move_and_unlike')) {
          refreshFromServer(next.targetPlaylistId)
        }
        if (next.fatalError) setFatalError(next.fatalError)
      } else if (next.status === 'running' && Date.now() - lastQuotaRefresh.current > QUOTA_REFRESH_MS) {
        lastQuotaRefresh.current = Date.now()
        refreshQuota()
      }
    },
    [refreshQuota],
  )

  // On sign-in: show the latest job, and open the panel if it is still running.
  useEffect(() => {
    api.getLatestJob().then(
      (latest) => {
        apply(latest)
        if (latest?.status === 'running') setPanelOpen(true)
      },
      () => {},
    )
  }, [apply])

  // Poll while running.
  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => {
      api.getLatestJob().then(apply, () => {})
    }, JOB_POLL_MS)
    return () => clearInterval(timer)
  }, [running, apply])

  const trackJob = useCallback(
    (started: Job) => {
      apply(started)
      setPanelOpen(true)
      refreshQuota()
    },
    [apply, refreshQuota],
  )

  return (
    <JobContext
      value={{
        job,
        running,
        panelOpen,
        setPanelOpen,
        trackJob,
        fatalError,
        dismissFatalError: () => setFatalError(null),
      }}
    >
      {children}
    </JobContext>
  )
}

export function useJob(): JobState {
  const state = useContext(JobContext)
  if (!state) throw new Error('useJob must be used inside JobProvider')
  return state
}
