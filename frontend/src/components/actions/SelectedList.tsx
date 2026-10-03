import { formatNumber } from '../../utils/format'

export interface SelectedEntry {
  /** Video ID, or playlistItemId on the Playlists screen. */
  id: string
  title: string
}

interface Props {
  items: SelectedEntry[]
  /** Takes one item out of the selection (also unchecks it in the main list). */
  onRemove: (id: string) => void
  disabled?: boolean
}

// Selected videos inside a confirm dialog, each removable with ✕ (DECISIONS.md 29).
export default function SelectedList({ items, onRemove, disabled }: Props) {
  return (
    <div className="mt-4">
      <p className="text-xs font-bold text-accent">Selected videos ({formatNumber(items.length)})</p>
      {items.length === 0 ? (
        <p className="mt-2 border px-3 py-3 text-muted">No videos selected.</p>
      ) : (
        <ul className="mt-2 max-h-48 overflow-y-auto border">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-center gap-2 border-b py-1.5 pr-1.5 pl-3 last:border-b-0 hover:bg-text/5"
            >
              <span className="min-w-0 flex-1 truncate" title={item.title}>
                {item.title}
              </span>
              <button
                type="button"
                onClick={() => onRemove(item.id)}
                disabled={disabled}
                aria-label={`Remove "${item.title}" from selection`}
                title="Remove from selection"
                className="shrink-0 rounded-sm px-2 py-0.5 text-muted hover:bg-text/10 hover:text-text disabled:cursor-not-allowed disabled:opacity-40"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
