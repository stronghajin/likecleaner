import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import Button from '../components/Button'
import CenteredCard from '../components/CenteredCard'
import Logo from '../components/Logo'
import { EXTERNAL_LINKS } from '../config'
import { HOME_FOR_STATUS, useSession } from '../state/session'

// Sent back by the server when the YouTube permission was refused on Google's page (DECISIONS.md 57).
const SIGNIN_ERRORS: Record<string, string> = {
  youtube_permission: 'LikeCleaner needs access to your YouTube account. Please sign in again and allow access.',
}

export default function LandingPage() {
  const { signIn } = useSession()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(() => SIGNIN_ERRORS[searchParams.get('signin_error') ?? ''] ?? '')

  const handleSignIn = async () => {
    setBusy(true)
    setError('')
    try {
      const user = await signIn()
      navigate(HOME_FOR_STATUS[user.status])
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  const linkClass = 'underline hover:text-text'

  return (
    <CenteredCard>
      <Logo size="lg" />
      <p className="mt-3 text-muted">Clean up your YouTube liked videos and playlists in one place.</p>
      <Button variant="primary" className="mt-8 w-full py-3" onClick={handleSignIn} disabled={busy}>
        {busy ? 'Signing in…' : 'Sign in with Google'}
      </Button>
      {error && <p className="mt-3 text-danger">{error}</p>}
      <p className="mt-6 text-xs leading-relaxed text-muted">
        By signing in, you agree to the{' '}
        <a href={EXTERNAL_LINKS.youtubeTerms} target="_blank" rel="noreferrer" className={linkClass}>
          YouTube Terms of Service
        </a>
        . See our{' '}
        <Link to="/privacy" className={linkClass}>
          Privacy Policy
        </Link>{' '}
        and the{' '}
        <a href={EXTERNAL_LINKS.googlePrivacy} target="_blank" rel="noreferrer" className={linkClass}>
          Google Privacy Policy
        </a>
        .
      </p>
    </CenteredCard>
  )
}
