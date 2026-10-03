import { useEffect, useState } from 'react'
import { api } from '../../services'
import type { Job, Playlist } from '../../services'
import { useQuota } from '../../state/quota'
import { formatNumber } from '../../utils/format'
import Button from '../Button'
import Modal from '../Modal'
import { errorText } from './ErrorText'
import { estimateText, notEnoughText, useQuotaCheck } from './QuotaEstimate'

interface Props {
  playlist: Playlist
  playlistItemIds: string[]
  onClose: () => void
  onStarted: (job: Job) => void
}

// Remove from playlist confirm dialog (SPEC.md 7-2).
export default function RemoveFromPlaylistDialog({ playlist, playlistItemIds, onClose, onStarted }: Props) {
  const { refreshQuota } = useQuota()
  const check = useQuotaCheck('playlist_remove', playlistItemIds.length)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(refreshQuota, [refreshQuota])

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      onStarted(await api.createJob({ type: 'playlist_remove', playlistId: playlist.id, playlistItemIds }))
    } catch (e) {
      setError(errorText(e))
      setBusy(false)
    }
  }

  return (
    <Modal
      title={`Remove ${formatNumber(playlistItemIds.length)} videos from "${playlist.title}"?`}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="danger" onClick={confirm} disabled={!check.enough || busy}>
            {busy ? 'Starting…' : 'Remove'}
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
