export const formatNumber = (n: number) => n.toLocaleString('en-US')

/** 1:02:03 or 4:05 */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = String(seconds % 60).padStart(2, '0')
  return h ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`
}

/** "5h 12m" until the given time (never negative). */
export function formatTimeUntil(iso: string, now = Date.now()): string {
  const minutes = Math.max(0, Math.ceil((Date.parse(iso) - now) / 60_000))
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`
}

/** "Mar 4, 2021" */
export const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
