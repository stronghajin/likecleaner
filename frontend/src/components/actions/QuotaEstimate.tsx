import { estimateUnits, maxAffordableItems } from '../../services'
import type { JobType } from '../../services'
import { useQuota } from '../../state/quota'
import { formatNumber } from '../../utils/format'

/** Estimate and whether it fits in today's remaining quota (SPEC.md 4-3, 4-4). */
export function useQuotaCheck(type: JobType, count: number, targetItemCount = 0) {
  const { quota } = useQuota()
  const units = estimateUnits(type, count, targetItemCount)
  const unitsLeft = quota ? quota.limit - quota.used : 0
  return {
    units,
    /** False while the quota is still loading, too. */
    enough: quota !== null && units <= unitsLeft,
    maxItems: maxAffordableItems(type, unitsLeft, targetItemCount),
    loading: quota === null,
  }
}

export const estimateText = (units: number) => `This action will use about ${formatNumber(units)} units.`

export const notEnoughText = (maxItems: number) =>
  `Not enough quota. You can process up to ${formatNumber(maxItems)} items today.`
