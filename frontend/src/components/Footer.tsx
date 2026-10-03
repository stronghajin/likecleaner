import { Link } from 'react-router'
import { EXTERNAL_LINKS } from '../config'

// Policy links required on the sign-in screen and in the footer (SPEC.md section 10).
export default function Footer() {
  const linkClass = 'hover:text-text hover:underline'
  return (
    <footer className="flex gap-6 border-t px-8 py-4 text-xs text-muted">
      <Link to="/privacy" className={linkClass}>
        Privacy Policy
      </Link>
      <a href={EXTERNAL_LINKS.youtubeTerms} target="_blank" rel="noreferrer" className={linkClass}>
        YouTube Terms of Service
      </a>
      <a href={EXTERNAL_LINKS.googlePrivacy} target="_blank" rel="noreferrer" className={linkClass}>
        Google Privacy Policy
      </a>
    </footer>
  )
}
