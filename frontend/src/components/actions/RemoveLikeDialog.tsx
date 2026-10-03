import { useEffect, useState } from 'react'
import { api } from '../../services'
import type { Job } from '../../services'
import { useQuota } from '../../state/quota'
import { formatNumber } from '../../utils/format'
import Button from '../Button'
import Modal from '../Modal'
import { errorText } from './ErrorText'
import { estimateText, notEnoughText, useQuotaCheck } from './QuotaEstimate'

interface Props {
  videoIds: string[]
  onClose: () => void
  onStarted: (job: Job) => void
}

// Remove Like confirm dialog (SPEC.md 6-5).
export default function RemoveLikeDialog({ videoIds, onClose, onStarted }: Props) {
  const { refreshQuota } = useQuota()
  const check = useQuotaCheck('remove_like', videoIds.length)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // The quota is shared with other users, so check it fresh before deciding.
  useEffect(refreshQuota, [refreshQuota])

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      onStarted(await api.createJob({ type: 'remove_like', videoIds }))
    } catch (e) {
      setError(errorText(e))
      setBusy(false)
    }
  }

  return (
    <Modal
      title={`Remove likes from ${formatNumber(videoIds.length)} videos?`}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="danger" onClick={confirm} disabled={!check.enough || busy}>
            {busy ? 'Starting…' : 'Remove Likes'}
          </Button>
        </>
      }
    >
      <p>{estimateText(check.units)}</p>
      {!check.loading && !check.enough && <p className="mt-3 text-danger">{notEnoughText(check.maxItems)}</p>}
      {error && <p className="mt-3 text-danger">{error}</p>}
    </Modal>
  )
}
