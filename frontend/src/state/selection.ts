import { useCallback, useState } from 'react'
import { MAX_SELECTION } from '../services'

/** A checkbox selection capped at 100 items (SPEC.md 6-4, 7-2). */
export function useSelection() {
  const [selectedIds, setSelectedIds] = useState<ReadonlySet<string>>(new Set())

  /** Adds IDs in order until the limit. Returns false if some could not be added. */
  const select = useCallback(
    (ids: string[]) => {
      const next = new Set(selectedIds)
      for (const id of ids) {
        if (next.has(id)) continue
        if (next.size >= MAX_SELECTION) {
          setSelectedIds(next)
          return false
        }
        next.add(id)
      }
      setSelectedIds(next)
      return true
    },
    [selectedIds],
  )

  /** Replaces the whole selection with the first 100 IDs. Returns false if some were left out. */
  const replace = useCallback((ids: string[]) => {
    setSelectedIds(new Set(ids.slice(0, MAX_SELECTION)))
    return ids.length <= MAX_SELECTION
  }, [])

  const deselect = useCallback((ids: string[]) => {
    const gone = new Set(ids)
    setSelectedIds((current) =>
      [...current].some((id) => gone.has(id)) ? new Set([...current].filter((id) => !gone.has(id))) : current,
    )
  }, [])

  /** Keeps only IDs that still exist (after a reload). */
  const keepOnly = useCallback((existing: ReadonlySet<string>) => {
    setSelectedIds((current) => new Set([...current].filter((id) => existing.has(id))))
  }, [])

  const clear = useCallback(() => setSelectedIds(new Set()), [])

  return { selectedIds, select, replace, deselect, keepOnly, clear }
}
