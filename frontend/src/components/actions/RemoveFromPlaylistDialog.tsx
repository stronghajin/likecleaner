import { useEffect, useState } from 'react'
import { api } from '../../services'
import type { Job, Playlist } from '../../services'
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
  playlist: Playlist
  /** Selected playlist entries (id = playlistItemId), in playlist order. */
  items: SelectedEntry[]
  onDeselect: (ids: string[]) => void
  onClose: () => void
  onStarted: (job: Job) => void
}

// Remove from playlist confirm dialog (SPEC.md 7-2), with the selection editable in place (DECISIONS.md 29).
export default function RemoveFromPlaylistDialog({ playlist, items, onDeselect, onClose, onStarted }: Props) {
  const { refreshQuota } = useQuota()
  const check = useQuotaCheck('playlist_remove', items.length)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(refreshQuota, [refreshQuota])

  const keepFirst = (count: number) => onDeselect(items.slice(count).map((i) => i.id))

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      onStarted(
        await api.createJob({
          type: 'playlist_remove',
          playlistId: playlist.id,
          playlistItemIds: items.map((i) => i.id),
        }),
      )
    } catch (e) {
      setError(errorText(e))
      setBusy(false)
    }
  }

  return (
    <Modal
      title={`Remove ${formatNumber(items.length)} videos from "${playlist.title}"?`}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="danger" onClick={confirm} disabled={items.length === 0 || !check.enough || busy}>
            {busy ? 'Starting…' : 'Remove'}
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
