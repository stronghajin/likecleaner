import type { Job, JobItemStatus } from './types'

export type JobCounts = Record<JobItemStatus, number> & { total: number; done: number }

/** Counts for the progress panel ("Processing 37 / 100", success / failed / skipped). */
export function summarizeJob(job: Job): JobCounts {
  const counts: JobCounts = {
    total: job.items.length,
    done: 0,
    pending: 0,
    success: 0,
    failed: 0,
    skipped: 0,
    rollback_failed: 0,
    not_processed: 0,
  }
  for (const item of job.items) {
    counts[item.status] += 1
    // Items skipped because the job stopped early were never worked on.
    if (item.status !== 'pending' && item.status !== 'not_processed') counts.done += 1
  }
  return counts
}

/** Items that `Retry Failed` runs again (DECISIONS.md 10: not rollback_failed). */
export const isRetryable = (status: JobItemStatus) =>
  status === 'failed' || status === 'not_processed'
