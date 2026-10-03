import { useEffect, useState } from 'react'
import { useQuota } from '../state/quota'
import { formatNumber, formatTimeUntil } from '../utils/format'

// "Quota left today: 7,450 / 10,000 units" + bar + "Resets in 5h 12m" (SPEC.md 4-3).
export default function QuotaMeter() {
  const { quota } = useQuota()
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(timer)
  }, [])

  if (!quota) return <div className="h-9 w-[440px]" />

  const left = Math.max(0, quota.limit - quota.used)
  const percentLeft = (left / quota.limit) * 100

  return (
    <div className="w-[440px] whitespace-nowrap">
      <div className="flex items-baseline justify-between gap-4 text-xs">
        <span>
          <span className="font-bold text-accent">Quota left today:</span>{' '}
          <span className="tabular-nums">
            {formatNumber(left)} / {formatNumber(quota.limit)} units
          </span>
        </span>
        <span className="text-muted tabular-nums">Resets in {formatTimeUntil(quota.resetsAt, now)}</span>
      </div>
      <div
        className="mt-1.5 h-1.5 bg-border"
        role="progressbar"
        aria-label="Quota left today"
        aria-valuemin={0}
        aria-valuemax={quota.limit}
        aria-valuenow={left}
      >
        <div className="h-full bg-accent transition-[width] duration-500" style={{ width: `${percentLeft}%` }} />
      </div>
    </div>
  )
}
