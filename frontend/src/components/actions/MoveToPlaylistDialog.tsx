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
  videoIds: string[]
  onClose: () => void
  onStarted: (job: Job) => void
}

// Move to Playlist (SPEC.md 6-6): 1. pick one playlist, 2. choose Move Only or Move and Remove Likes.
export default function MoveToPlaylistDialog({ videoIds, onClose, onStarted }: Props) {
  const [target, setTarget] = useState<Playlist | null>(null)
  return target ? (
    <ConfirmMove videoIds={videoIds} playlist={target} onClose={onClose} onStarted={onStarted} />
  ) : (
    <PickPlaylist onClose={onClose} onPick={setTarget} />
  )
}

function PickPlaylist({ onClose, onPick }: { onClose: () => void; onPick: (p: Playlist) => void }) {
  const { refreshQuota } = useQuota()
  const [playlists, setPlaylists] = useState<Playlist[] | null>(null)
  const [chosen, setChosen] = useState<Playlist | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .getPlaylists()
      .then(setPlaylists, (e) => setError(errorText(e)))
      .finally(refreshQuota)
  }, [refreshQuota])

  return (
    <Modal
      title="Move to Playlist"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={() => chosen && onPick(chosen)} disabled={!chosen}>
            Continue
          </Button>
        </>
      }
    >
      <p className="text-muted">Choose one playlist.</p>
      {!playlists && !error && <p className="mt-4 text-muted">Loading your playlists…</p>}
      {error && <p className="mt-4 text-danger">{error}</p>}
      {playlists && playlists.length === 0 && <p className="mt-4 text-muted">You have no playlists.</p>}
      {playlists && playlists.length > 0 && (
        <ul role="listbox" aria-label="Playlists" className="mt-4 max-h-80 overflow-y-auto border">
          {playlists.map((p) => {
            const selected = chosen?.id === p.id
            return (
              <li key={p.id} role="option" aria-selected={selected} className="border-b last:border-b-0">
                <button
                  type="button"
                  onClick={() => setChosen(p)}
                  onDoubleClick={() => onPick(p)}
                  className={`flex w-full items-center justify-between px-4 py-2.5 text-left ${
                    selected ? 'bg-accent text-bg' : 'hover:bg-text/5'
                  }`}
                >
                  <span className="truncate font-medium">{p.title}</span>
                  <span className={`shrink-0 tabular-nums ${selected ? '' : 'text-muted'}`}>
                    {formatNumber(p.itemCount)} videos
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </Modal>
  )
}

interface ConfirmProps extends Props {
  playlist: Playlist
}

function ConfirmMove({ videoIds, playlist, onClose, onStarted }: ConfirmProps) {
  const { refreshQuota } = useQuota()
  const moveAndUnlike = useQuotaCheck('move_and_unlike', videoIds.length, playlist.itemCount)
  const moveOnly = useQuotaCheck('move', videoIds.length, playlist.itemCount)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(refreshQuota, [refreshQuota])

  const start = async (type: 'move' | 'move_and_unlike') => {
    setBusy(true)
    setError('')
    try {
      onStarted(await api.createJob({ type, videoIds, targetPlaylistId: playlist.id }))
    } catch (e) {
      setError(errorText(e))
      setBusy(false)
    }
  }

  // One row per choice, each with its own estimate; only a choice that does not fit is blocked (DECISIONS.md 8).
  const options = [
    {
      type: 'move_and_unlike' as const,
      label: 'Move and Remove Likes',
      check: moveAndUnlike,
      variant: 'danger' as const,
    },
    { type: 'move' as const, label: 'Move Only', check: moveOnly, variant: 'primary' as const },
  ]

  return (
    <Modal
      title="Move to Playlist"
      onClose={onClose}
      width={600}
      footer={<Button onClick={onClose}>Cancel</Button>}
    >
      <p>
        Move {formatNumber(videoIds.length)} videos to &quot;{playlist.title}&quot;. Do you also want to remove their
        likes?
      </p>
      <div className="mt-5 flex flex-col gap-3">
        {options.map(({ type, label, check, variant }) => (
          <div key={type} className="flex items-center justify-between gap-4 border p-4">
            <div>
              <p className="font-bold text-accent">{label}</p>
              <p className="mt-1 text-muted">{estimateText(check.units)}</p>
              {!check.loading && !check.enough && <p className="mt-1 text-danger">{notEnoughText(check.maxItems)}</p>}
            </div>
            <Button
              variant={variant}
              className="shrink-0"
              onClick={() => start(type)}
              disabled={!check.enough || busy}
            >
              {label}
            </Button>
          </div>
        ))}
      </div>
      {error && <p className="mt-4 text-danger">{error}</p>}
    </Modal>
  )
}
