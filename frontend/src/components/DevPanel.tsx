import { useEffect, useRef, useState } from 'react'
import { api, devTools } from '../services'
import type { DevSettings, FailureMode, UserStatus } from '../services'
import { useQuota } from '../state/quota'
import { useSession } from '../state/session'
import { formatNumber } from '../utils/format'
import Button from './Button'

// Phase 1 only (DECISIONS.md 14, 22): a small "DEV" button in the bottom-right corner of every
// screen that opens switches for trying every screen and error without a backend.
// Loaded only by `npm run dev`; never part of a production build. Delete in Phase 2.

const STATUS_OPTIONS: { value: UserStatus; label: string }[] = [
  { value: 'approved', label: 'Approved' },
  { value: 'pending', label: 'Pending' },
  { value: 'rejected', label: 'Rejected' },
]

const FAILURE_OPTIONS: { value: FailureMode; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'some_failures', label: 'Some items fail' },
  { value: 'quota_exceeded', label: 'Quota runs out' },
]

function Segmented<T extends string>(props: {
  options: { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
}) {
  return (
    <div className="inline-flex border">
      {props.options.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => props.onChange(o.value)}
          className={`px-2.5 py-1.5 text-xs font-medium ${
            props.value === o.value ? 'bg-accent text-bg' : 'text-muted hover:bg-text/5 hover:text-text'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export default function DevPanel() {
  const { refresh } = useSession()
  const { refreshQuota } = useQuota()
  const [open, setOpen] = useState(false)
  const [settings, setSettings] = useState<DevSettings>(devTools.getDevSettings)
  const [quotaLeft, setQuotaLeft] = useState<number | null>(null)
  const [quotaInput, setQuotaInput] = useState('')
  const [message, setMessage] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  const loadQuota = () => api.getQuota().then((q) => setQuotaLeft(q.limit - q.used))
  useEffect(() => {
    if (open) loadQuota()
  }, [open])

  // Clicking anywhere outside the panel (and its DEV button) closes it.
  useEffect(() => {
    if (!open) return
    const onPointerDown = (e: PointerEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])

  const done = (text: string) => {
    setMessage(text)
    loadQuota()
    refreshQuota()
  }

  const changeStatus = (userStatus: UserStatus) => {
    setSettings(devTools.setDevSettings({ userStatus }))
    refresh() // signed-in users jump to the screen for the new status
  }

  const applyQuota = () => {
    const value = Number(quotaInput)
    if (quotaInput.trim() === '' || !Number.isFinite(value)) return
    devTools.setQuotaLeft(value)
    setQuotaInput('')
    done('Quota updated.')
  }

  const reset = () => {
    devTools.resetMockData()
    refresh() // reset also signs you out
    done('Mock data reset.')
  }

  const rowClass = 'flex items-center justify-between gap-4'
  const labelClass = 'text-xs font-bold text-accent'

  return (
    <div ref={containerRef} className="fixed right-4 bottom-4 z-40 flex flex-col items-end gap-2">
      {open && (
        <section className="w-[420px] border bg-panel p-5 shadow-2xl shadow-bg">
          <h2 className="text-xs font-bold tracking-wider text-muted uppercase">Developer tools (mock only)</h2>
          <div className="mt-4 flex flex-col gap-3">
            <div className={rowClass}>
              <span className={labelClass}>Approval status</span>
              <Segmented options={STATUS_OPTIONS} value={settings.userStatus} onChange={changeStatus} />
            </div>
            <div className={rowClass}>
              <span className={labelClass}>Job failures</span>
              <Segmented
                options={FAILURE_OPTIONS}
                value={settings.failureMode}
                onChange={(failureMode) => setSettings(devTools.setDevSettings({ failureMode }))}
              />
            </div>
            <div className={rowClass}>
              <span className={labelClass}>
                Quota left{' '}
                <span className="font-normal text-muted">({quotaLeft === null ? '…' : formatNumber(quotaLeft)})</span>
              </span>
              <div className="flex gap-2">
                <input
                  type="number"
                  min={0}
                  max={10000}
                  value={quotaInput}
                  onChange={(e) => setQuotaInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && applyQuota()}
                  placeholder="e.g. 1000"
                  className="w-28 rounded-sm border bg-bg px-2 py-1.5 text-xs outline-none focus:border-muted"
                />
                <Button className="px-3 py-1.5 text-xs" onClick={applyQuota}>
                  Set
                </Button>
              </div>
            </div>
            <div className={rowClass}>
              <span className={labelClass}>Mock data</span>
              <Button className="px-3 py-1.5 text-xs" onClick={reset}>
                Reset mock data
              </Button>
            </div>
          </div>
          {message && <p className="mt-3 text-xs text-success">{message}</p>}
        </section>
      )}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className={`rounded-sm border px-2.5 py-1 text-[11px] font-bold tracking-wider ${
          open ? 'bg-accent text-bg' : 'bg-panel text-muted hover:border-muted hover:text-text'
        }`}
      >
        DEV
      </button>
    </div>
  )
}
