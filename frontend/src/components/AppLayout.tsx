import { NavLink, Outlet, useNavigate } from 'react-router'
import { useSession } from '../state/session'
import Button from './Button'
import Footer from './Footer'
import { Icon } from './icons'
import JobIndicator from './job/JobIndicator'
import JobPanel from './job/JobPanel'
import type { IconName } from './icons'
import Logo from './Logo'
import QuotaMeter from './QuotaMeter'

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: '/liked', label: 'Liked Videos', icon: 'like' },
  { to: '/playlists', label: 'Playlists', icon: 'playlist' },
]

// Signed-in frame (DECISIONS.md 17): left sidebar with menu, top bar with quota and profile.
export default function AppLayout() {
  const { user, signOut } = useSession()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r bg-panel">
        <div className="flex h-16 items-center border-b px-6">
          <Logo />
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-sm px-3 py-2 font-medium transition-colors duration-150 ${
                  isActive ? 'bg-accent text-bg' : 'text-muted hover:bg-text/5 hover:text-text'
                }`
              }
            >
              <Icon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between gap-6 border-b bg-bg px-8">
          <QuotaMeter />
          <div className="flex items-center gap-6">
            <JobIndicator />
            {user && (
              <div className="flex items-center gap-3">
                <img src={user.pictureUrl} alt="" width={28} height={28} className="rounded-full" />
                <span className="font-medium">{user.name}</span>
                <Button variant="ghost" className="px-3 py-1.5" onClick={handleSignOut}>
                  Sign out
                </Button>
              </div>
            )}
          </div>
        </header>
        <main className="flex-1 px-8 py-6">
          <Outlet />
        </main>
        <Footer />
      </div>
      <JobPanel />
    </div>
  )
}
