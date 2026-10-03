import { useNavigate } from 'react-router'
import Button from '../components/Button'
import CenteredCard from '../components/CenteredCard'
import Logo from '../components/Logo'
import { useSession } from '../state/session'

// Exact wording from SPEC.md section 5.
const MESSAGES = {
  pending: {
    title: 'Pending Approval',
    body: 'Your access request has been sent. You can use LikeCleaner once the admin approves it.',
  },
  rejected: {
    title: 'Access Denied',
    body: 'Your access request was not approved.',
  },
}

export default function StatusPage({ status }: { status: keyof typeof MESSAGES }) {
  const { user, signOut } = useSession()
  const navigate = useNavigate()
  const message = MESSAGES[status]

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  return (
    <CenteredCard>
      <Logo />
      <h1 className={`mt-8 text-lg font-semibold ${status === 'rejected' ? 'text-danger' : ''}`}>{message.title}</h1>
      <p className="mt-2">{message.body}</p>
      {user && <p className="mt-6 text-xs text-muted">Signed in as {user.email}</p>}
      <Button className="mt-4" onClick={handleSignOut}>
        Sign out
      </Button>
    </CenteredCard>
  )
}
