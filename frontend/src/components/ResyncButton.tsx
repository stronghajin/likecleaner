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
  /** A job is running: Resync waits for it (DECISIONS.md 13). */
  jobRunning: boolean
}

const JOB_RUNNING_HINT = 'Available when the current job finishes'

// Resync with its cost as a tooltip, turned off with a red warning when today's quota cannot cover it.
export default function ResyncButton({ units, onClick, loading, disabled, jobRunning }: Props) {
  const { quota } = useQuota()
  const notEnough = quota !== null && units > quota.limit - quota.used
  return (
    <>
      {notEnough && <span className="text-danger">Not enough quota to resync (needs about {formatNumber(units)} units).</span>}
      <Button
        onClick={onClick}
        disabled={loading || disabled || jobRunning || notEnough}
        title={jobRunning ? JOB_RUNNING_HINT : `Uses about ${formatNumber(units)} units`}
      >
        {loading ? 'Resyncing…' : 'Resync'}
      </Button>
    </>
  )
}
