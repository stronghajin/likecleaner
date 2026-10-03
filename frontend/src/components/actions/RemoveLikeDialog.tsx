import { useEffect, useState } from 'react'
import { api } from '../../services'
import type { Job } from '../../services'
import { useQuota } from '../../state/quota'
import { formatNumber } from '../../utils/format'
import Button from '../Button'
import Modal from '../Modal'
import { errorText } from './ErrorText'
import { estimateText, useQuotaCheck } from './QuotaEstimate'
import QuotaWarning from './QuotaWarning'
import SelectedList from './SelectedList'
import type { SelectedEntry } from './SelectedList'

interface Props {
  /** The current selection; it shrinks live as items are removed here. */
  items: SelectedEntry[]
  /** Unselects these videos in the main list. */
  onDeselect: (ids: string[]) => void
  onClose: () => void
  onStarted: (job: Job) => void
}

// Remove Like confirm dialog (SPEC.md 6-5), with the selection editable in place (DECISIONS.md 29).
export default function RemoveLikeDialog({ items, onDeselect, onClose, onStarted }: Props) {
  const { refreshQuota } = useQuota()
  const check = useQuotaCheck('remove_like', items.length)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // The quota is shared with other users, so check it fresh before deciding.
  useEffect(refreshQuota, [refreshQuota])

  const keepFirst = (count: number) => onDeselect(items.slice(count).map((i) => i.id))

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      onStarted(await api.createJob({ type: 'remove_like', videoIds: items.map((i) => i.id) }))
    } catch (e) {
      setError(errorText(e))
      setBusy(false)
    }
  }

  return (
    <Modal
      title={`Remove likes from ${formatNumber(items.length)} videos?`}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="danger" onClick={confirm} disabled={items.length === 0 || !check.enough || busy}>
            {busy ? 'Starting…' : 'Remove Likes'}
          </Button>
        </>
      }
    >
      <p>{estimateText(check.units)}</p>
      {!check.loading && !check.enough && (
        <QuotaWarning maxItems={check.maxItems} onKeepFirst={keepFirst} disabled={busy} />
      )}
      <SelectedList items={items} onRemove={(id) => onDeselect([id])} disabled={busy} />
      {error && <p className="mt-3 text-danger">{error}</p>}
    </Modal>
  )
}
