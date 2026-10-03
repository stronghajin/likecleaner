import type { ReactNode } from 'react'
import { formatNumber } from '../utils/format'

interface SelectionBarProps {
  count: number
  /** Red notice, e.g. the selection limit message. */
  notice?: string
  /** Action buttons. */
  children: ReactNode
}

// Floating bar at the bottom of the content area, shown while something is selected (SPEC.md 6-4).
export default function SelectionBar({ count, notice, children }: SelectionBarProps) {
  if (count === 0) return null
  return (
    <div className="fixed bottom-6 left-[calc(50%+120px)] z-30 -translate-x-1/2 animate-[bar-in_180ms_ease-out]">
      {notice && (
        <p role="alert" className="mb-2 border border-danger bg-panel px-4 py-2 text-center text-danger shadow-2xl shadow-bg">
          {notice}
        </p>
      )}
      <div className="flex items-center gap-3 border bg-panel py-2.5 pr-2.5 pl-5 shadow-2xl shadow-bg">
        <span className="font-bold whitespace-nowrap text-accent tabular-nums">{formatNumber(count)} selected</span>
        <span className="h-5 w-px bg-border" />
        {children}
      </div>
    </div>
  )
}
