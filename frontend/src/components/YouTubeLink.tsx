import { Icon } from './icons'

interface YouTubeLinkProps {
  /** null = the video cannot be watched: a grey icon with a "Not available" tooltip. */
  href: string | null
  /** What opens, for screen readers, e.g. "Open Song title on YouTube". */
  label: string
}

// External link icon that opens YouTube in a new tab (DECISIONS.md 60).
// Clicks stop here so the row's checkbox or the playlist choice does not change.
export default function YouTubeLink({ href, label }: YouTubeLinkProps) {
  const box = 'inline-flex size-7 items-center justify-center rounded-sm'
  if (!href) {
    return (
      <span title="Not available" aria-label="Not available" className={`${box} cursor-not-allowed text-muted/40`}>
        <Icon name="external" />
      </span>
    )
  }
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      title="Open on YouTube"
      aria-label={label}
      className={`${box} text-muted hover:bg-text/10 hover:text-text`}
    >
      <Icon name="external" />
    </a>
  )
}
