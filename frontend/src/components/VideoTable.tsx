import { formatDate, formatDuration } from '../utils/format'
import { videoUrl } from '../utils/youtubeLinks'
import YouTubeLink from './YouTubeLink'

/** One list row. Shared by liked videos and playlist items (SPEC.md 6-1, 7-1). */
export interface VideoRow {
  key: string
  /** For the YouTube link (DECISIONS.md 60). */
  videoId: string
  title: string
  channelTitle: string | null
  categoryName: string | null
  durationSeconds: number | null
  publishedAt: string | null
  thumbnailUrl: string | null
  /** Deleted or private video: title shown dimmed. */
  unavailable?: boolean
}

const COLUMNS = ['', '', 'Title', 'Channel', 'Category', 'Duration', 'Uploaded', 'Link']
const RIGHT_ALIGNED_FROM = 5

interface VideoTableProps {
  rows: VideoRow[]
  selectedKeys: ReadonlySet<string>
  onToggle: (key: string) => void
}

// Clicking anywhere on a row toggles its checkbox.
export default function VideoTable({ rows, selectedKeys, onToggle }: VideoTableProps) {
  return (
    <table className="w-full table-fixed border-collapse">
      <colgroup>
        <col className="w-11" />
        <col className="w-[92px]" />
        <col />
        <col className="w-[18%]" />
        <col className="w-[15%]" />
        <col className="w-24" />
        <col className="w-32" />
        <col className="w-16" />
      </colgroup>
      <thead>
        <tr className="sticky top-16 z-[1] bg-panel text-left text-xs">
          {COLUMNS.map((label, i) => (
            <th
              key={i}
              className={`border-b px-3 py-2.5 font-bold text-accent ${i >= RIGHT_ALIGNED_FROM ? 'text-right' : ''}`}
            >
              {label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const selected = selectedKeys.has(row.key)
          return (
            <tr
              key={row.key}
              onClick={() => onToggle(row.key)}
              aria-selected={selected}
              className={`cursor-pointer border-b transition-colors duration-150 last:border-b-0 ${
                selected ? 'bg-text/10 hover:bg-text/15' : 'hover:bg-text/5'
              }`}
            >
              <td className="py-2 pl-4">
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => onToggle(row.key)}
                  onClick={(e) => e.stopPropagation()}
                  aria-label={`Select ${row.title}`}
                  className="block size-4 cursor-pointer accent-accent"
                />
              </td>
              <td className="py-2 pr-3 pl-1">
                {row.thumbnailUrl ? (
                  <img
                    src={row.thumbnailUrl}
                    alt=""
                    width={80}
                    height={60}
                    loading="lazy"
                    className="block h-[60px] w-20 object-cover"
                  />
                ) : (
                  <div className="h-[60px] w-20 bg-border" />
                )}
              </td>
              <td className="px-3 py-2">
                <p className={`truncate font-medium ${row.unavailable ? 'text-muted italic' : ''}`} title={row.title}>
                  {row.title}
                </p>
              </td>
              <td className="truncate px-3 py-2 text-muted" title={row.channelTitle ?? undefined}>
                {row.channelTitle ?? '—'}
              </td>
              <td className="truncate px-3 py-2 text-muted">{row.categoryName ?? '—'}</td>
              <td className="px-3 py-2 text-right text-muted tabular-nums">
                {row.durationSeconds === null ? '—' : formatDuration(row.durationSeconds)}
              </td>
              <td className="px-3 py-2 text-right text-muted tabular-nums">
                {row.publishedAt ? formatDate(row.publishedAt) : '—'}
              </td>
              <td className="px-3 py-2 text-right">
                <YouTubeLink
                  href={row.unavailable ? null : videoUrl(row.videoId)}
                  label={`Open ${row.title} on YouTube`}
                />
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
