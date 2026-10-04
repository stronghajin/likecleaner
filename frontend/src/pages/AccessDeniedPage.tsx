import { useState } from 'react'
import { useNavigate } from 'react-router'
import Button from '../components/Button'
import CenteredCard from '../components/CenteredCard'
import Logo from '../components/Logo'
import { HOME_FOR_STATUS, useSession } from '../state/session'

// For emails the admin has not registered, or has disabled (DECISIONS.md 56, exact wording).
export default function AccessDeniedPage() {
  const { user, signIn, signOut } = useSession()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // Google always shows its account chooser, so signing in again lets the user pick another account.
  const handleDifferentAccount = async () => {
    setBusy(true)
    setError('')
    try {
      await signOut()
      const next = await signIn()
      navigate(HOME_FOR_STATUS[next.status])
    } catch (e) {
      setError((e as Error).message)
      navigate('/')
    } finally {
      setBusy(false)
    }
  }

  return (
    <CenteredCard>
      <Logo />
      <h1 className="mt-8 text-lg font-semibold text-danger">Access Denied</h1>
      <p className="mt-2">
        This Google account ({user?.email}) doesn&apos;t have access to LikeCleaner. Please contact the admin.
      </p>
      <Button variant="primary" className="mt-6" onClick={handleDifferentAccount} disabled={busy}>
        {busy ? 'Signing in…' : 'Sign in with a different account'}
      </Button>
      {error && <p className="mt-3 text-danger">{error}</p>}
    </CenteredCard>
  )
}
