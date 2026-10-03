import { summarizeJob } from '../../services'
import { useJob } from '../../state/job'
import { formatNumber } from '../../utils/format'

// Small job status in the top bar; click to show or hide the progress panel (DECISIONS.md 11).
export default function JobIndicator() {
  const { job, running, panelOpen, setPanelOpen } = useJob()
  if (!job) return null
  const { done, total } = summarizeJob(job)
  const label = running
    ? `Processing ${formatNumber(done)} / ${formatNumber(total)}`
    : job.status === 'completed'
      ? 'Last job: completed'
      : 'Last job: stopped'
  const dot = running ? 'bg-accent animate-pulse' : job.status === 'completed' ? 'bg-success' : 'bg-danger'

  return (
    <button
      type="button"
      data-job-indicator
      onClick={() => setPanelOpen(!panelOpen)}
      aria-expanded={panelOpen}
      className={`flex items-center gap-2 rounded-sm border px-3 py-1.5 text-xs tabular-nums ${
        panelOpen ? 'border-muted text-text' : 'text-muted hover:border-muted hover:text-text'
      }`}
    >
      <span className={`size-2 rounded-full ${dot}`} />
      {label}
    </button>
  )
}
