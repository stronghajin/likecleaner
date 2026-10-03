import Select from './Select'

export const PAGE_SIZES = [20, 50, 100] as const
export type PageSize = (typeof PAGE_SIZES)[number]

/** Page numbers to show, with gaps: 1 … 4 5 6 … 16 */
function pageList(page: number, pageCount: number): (number | 'gap')[] {
  const pages = new Set([1, pageCount, page - 1, page, page + 1].filter((p) => p >= 1 && p <= pageCount))
  const sorted = [...pages].sort((a, b) => a - b)
  return sorted.flatMap((p, i) => (i > 0 && p - sorted[i - 1] > 1 ? ['gap' as const, p] : [p]))
}

interface PaginationProps {
  page: number
  pageCount: number
  pageSize: PageSize
  onPageChange: (page: number) => void
  onPageSizeChange: (size: PageSize) => void
}

// Page size 20 / 50 / 100 and page buttons (SPEC.md 6-3).
export default function Pagination({ page, pageCount, pageSize, onPageChange, onPageSizeChange }: PaginationProps) {
  const navClass =
    'h-9 min-w-9 rounded-sm px-2.5 text-sm tabular-nums disabled:cursor-not-allowed disabled:opacity-40'
  return (
    <div className="flex items-center gap-4">
      <label className="flex items-center gap-2 text-muted">
        Rows per page
        <Select value={pageSize} onChange={(e) => onPageSizeChange(Number(e.target.value) as PageSize)}>
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </Select>
      </label>
      <nav className="flex items-center gap-1" aria-label="Pagination">
        <button
          type="button"
          className={`${navClass} text-muted hover:bg-text/5 hover:text-text`}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </button>
        {pageList(page, pageCount).map((p, i) =>
          p === 'gap' ? (
            <span key={`gap${i}`} className="px-1 text-muted">
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              aria-current={p === page ? 'page' : undefined}
              className={`${navClass} ${p === page ? 'bg-accent font-semibold text-bg' : 'text-muted hover:bg-text/5 hover:text-text'}`}
              onClick={() => onPageChange(p)}
            >
              {p}
            </button>
          ),
        )}
        <button
          type="button"
          className={`${navClass} text-muted hover:bg-text/5 hover:text-text`}
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </button>
      </nav>
    </div>
  )
}
