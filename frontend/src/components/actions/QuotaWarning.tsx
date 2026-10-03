import { formatNumber } from '../../utils/format'
import Button from '../Button'
import { notEnoughText } from './QuotaEstimate'

interface Props {
  /** How many items fit in today's remaining quota. */
  maxItems: number
  /** Keeps the first `maxItems` and unselects the rest (DECISIONS.md 29). */
  onKeepFirst: (count: number) => void
  disabled?: boolean
}

// Red "Not enough quota" warning with a one-click way to shrink the selection (SPEC.md 4-4).
export default function QuotaWarning({ maxItems, onKeepFirst, disabled }: Props) {
  return (
    <div className="mt-2 flex items-center justify-between gap-3">
      <p className="text-danger">{notEnoughText(maxItems)}</p>
      {maxItems > 0 && (
        <Button className="shrink-0 px-3 py-1 text-xs" onClick={() => onKeepFirst(maxItems)} disabled={disabled}>
          Keep first {formatNumber(maxItems)} only
        </Button>
      )}
    </div>
  )
}
