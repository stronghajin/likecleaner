import { useEffect, useRef, useState } from 'react'
import { api, estimateUnits, isRetryable, maxAffordableItems, summarizeJob } from '../../services'
import { useJob } from '../../state/job'
import { useQuota } from '../../state/quota'
import { formatNumber } from '../../utils/format'
import { errorText } from '../actions/ErrorText'
import { notEnoughText } from '../actions/QuotaEstimate'
import Button from '../Button'
import Modal from '../Modal'
import { formatApiError, jobTitle } from './jobText'

/** "Rate limited. Retrying in N s..." while the job waits after a 429 (DECISIONS.md 28). */
function RetryCountdown({ retryAt }: { retryAt: string }) {
  // Mounted fresh for each wait (keyed by retryAt), so the clock never starts out of date.
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 250)
    return () => clearInterval(timer)
  }, [])
  const seconds = Math.max(1, Math.ceil((Date.parse(retryAt) - now) / 1000))
  return (
    <p role="status" className="mt-2 text-danger tabular-nums">
      Rate limited. Retrying in {seconds} s...
    </p>
  )
}

// Progress panel, bottom right (SPEC.md 8-2, DECISIONS.md 11): progress, counts, failed items, Retry Failed.
// Also shows the popup for an error that stopped the job (SPEC.md 8-3).
export default function JobPanel() {
  const { job, running, panelOpen, setPanelOpen, trackJob, fatalError, dismissFatalError } = useJob()
  const { quota } = useQuota()
  const [retrying, setRetrying] = useState(false)
  const [retryError, setRetryError] = useState('')
  const panelRef = useRef<HTMLElement>(null)
  const retryAt = running ? job?.rateLimit?.retryAt : undefined
  const closeOnOutsideClick = panelOpen && !!job && !running

  // Once the job has ended, a click outside the panel closes it (DECISIONS.md 27).
  useEffect(() => {
    if (!closeOnOutsideClick) return
    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as Element
      if (panelRef.current?.contains(target) || target.closest('[data-job-indicator], [role=dialog]')) return
      setPanelOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [closeOnOutsideClick, setPanelOpen])

  const errorPopup = fatalError && (
    <Modal
      title="Something went wrong"
      onClose={dismissFatalError}
      footer={
        <Button variant="primary" onClick={dismissFatalError}>
          OK
        </Button>
      }
    >
      <p className="text-danger">{formatApiError(fatalError)}</p>
      <p className="mt-3 text-muted">The job was stopped. The remaining videos were not processed.</p>
    </Modal>
  )

  if (!job || !panelOpen) return errorPopup

  const counts = summarizeJob(job)
  const failedTotal = counts.failed + counts.rollback_failed
  const percent = counts.total ? (counts.done / counts.total) * 100 : 0
  const problemItems = job.items.filter((i) => i.status === 'failed' || i.status === 'rollback_failed')
  const retryCount = job.items.filter((i) => isRetryable(i.status)).length

  // Same quota rule as any action (SPEC.md 8-2). The server checks again with the exact playlist size.
  const unitsLeft = quota ? quota.limit - quota.used : 0
  const retryUnits = estimateUnits(job.type, retryCount)
  const retryFits = retryUnits <= unitsLeft

  const retry = async () => {
    setRetrying(true)
    setRetryError('')
    try {
      trackJob(await api.retryFailedItems(job.id))
    } catch (e) {
      setRetryError(errorText(e))
    } finally {
      setRetrying(false)
    }
  }

  const stat = (label: string, value: number, color: string) => (
    <div className="flex-1 border px-3 py-2">
      <p className="text-xs font-bold text-accent">{label}</p>
      <p className={`mt-0.5 text-lg font-semibold tabular-nums ${color}`}>{formatNumber(value)}</p>
    </div>
  )

  const statusText = running
    ? 'Running in the background. You can close this tab.'
    : job.status === 'completed'
      ? 'Completed'
      : 'Stopped'
  const statusColor = running ? 'text-muted' : job.status === 'completed' ? 'text-success' : 'text-danger'

  return (
    <>
      <section
        ref={panelRef}
        aria-label="Job progress"
        className="fixed right-4 bottom-24 z-30 flex max-h-[70vh] w-[420px] flex-col border bg-panel shadow-2xl shadow-bg animate-[fade-in_150ms_ease-out]"
      >
        <header className="flex items-start justify-between gap-3 border-b px-5 py-4">
          <div className="min-w-0">
            <h2 className="truncate font-semibold" title={jobTitle(job)}>
              {jobTitle(job)}
            </h2>
            <p className={`mt-0.5 text-xs ${statusColor}`}>{statusText}</p>
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={() => setPanelOpen(false)}
            className="-mr-1 rounded-sm px-2 py-0.5 text-lg leading-none text-muted hover:bg-text/5 hover:text-text"
          >
            ×
          </button>
        </header>

        <div className="overflow-y-auto px-5 py-4">
          <p className="tabular-nums">
            {running ? 'Processing' : 'Processed'} {formatNumber(counts.done)} / {formatNumber(counts.total)}
          </p>
          <div className="mt-2 h-1.5 bg-border">
            <div className="h-full bg-accent transition-[width] duration-300" style={{ width: `${percent}%` }} />
          </div>
          {retryAt && <RetryCountdown key={retryAt} retryAt={retryAt} />}

          <div className="mt-4 flex gap-2">
            {stat('Success', counts.success, 'text-success')}
            {stat('Failed', failedTotal, failedTotal ? 'text-danger' : '')}
            {stat('Skipped', counts.skipped, 'text-muted')}
          </div>
          {counts.not_processed > 0 && (
            <p className="mt-2 text-danger">{formatNumber(counts.not_processed)} not processed</p>
          )}
          {job.fatalError && <p className="mt-3 text-danger">{formatApiError(job.fatalError)}</p>}

          {problemItems.length > 0 && (
            <>
              <h3 className="mt-5 text-xs font-bold text-accent">Failed items</h3>
              <ul className="mt-2 border">
                {problemItems.map((item, i) => (
                  <li key={`${item.videoId}-${i}`} className="border-b px-3 py-2 last:border-b-0">
                    <p className="truncate font-medium" title={item.videoTitle}>
                      {item.videoTitle}
                    </p>
                    {item.status === 'rollback_failed' && (
                      <p className="mt-0.5 text-xs font-bold text-danger">
                        Rollback failed. Check this video on YouTube yourself.
                      </p>
                    )}
                    {item.error && <p className="mt-0.5 text-xs text-danger">{formatApiError(item.error)}</p>}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        {!running && retryCount > 0 && (
          <footer className="border-t px-5 py-4">
            {quota && !retryFits && (
              <p className="mb-2 text-danger">{notEnoughText(maxAffordableItems(job.type, unitsLeft))}</p>
            )}
            {retryError && <p className="mb-2 text-danger">{retryError}</p>}
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted">About {formatNumber(retryUnits)} units</span>
              <Button variant="primary" onClick={retry} disabled={retrying || !retryFits}>
                {retrying ? 'Starting…' : `Retry Failed (${formatNumber(retryCount)})`}
              </Button>
            </div>
          </footer>
        )}
      </section>
      {errorPopup}
    </>
  )
}
