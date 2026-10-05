import { useEffect, useRef, useState } from 'react'
import { useJob } from '../state/job'
import { useQuota } from '../state/quota'
import { formatNumber } from '../utils/format'
import Button from './Button'

interface Props {
  /** About how many units this reload uses (DECISIONS.md 62). */
  units: number
  onClick: () => void
  /** Shows "Resyncing…". */
  loading: boolean
  /** Off for another reason, e.g. the first load is still running. */
  disabled?: boolean
}

const JOB_RUNNING_HINT = 'Available when the current job finishes'
/** YouTube shows a job's changes only after a few seconds (DECISIONS.md 55). */
const SETTLE_MS = 10_000

// Resync with its cost as a tooltip, turned off with a red warning when today's quota cannot cover it.
// Within 10 s of a job ending it waits before loading, so YouTube's answer already has the job's changes.
export default function ResyncButton({ units, onClick, loading, disabled }: Props) {
  const { quota } = useQuota()
  const { job, running } = useJob()
  const [waiting, setWaiting] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const notEnough = quota !== null && units > quota.limit - quota.used

  useEffect(() => () => clearTimeout(timer.current), [])

  const click = () => {
    const endedAt = job && !running && job.finishedAt ? Date.parse(job.finishedAt) : 0
    const wait = endedAt + SETTLE_MS - Date.now()
    if (wait <= 0) return onClick()
    setWaiting(true)
    timer.current = setTimeout(() => {
      setWaiting(false)
      onClick()
    }, wait)
  }

  return (
    <>
      {notEnough && (
        <span className="text-danger">Not enough quota to resync (needs about {formatNumber(units)} units).</span>
      )}
      <Button
        onClick={click}
        disabled={loading || waiting || disabled || running || notEnough}
        title={running ? JOB_RUNNING_HINT : `Uses about ${formatNumber(units)} units`}
      >
        {waiting ? 'Syncing with YouTube...' : loading ? 'Resyncing…' : 'Resync'}
      </Button>
    </>
  )
}
