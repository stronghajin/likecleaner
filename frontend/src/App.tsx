import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes } from 'react-router'
import AppLayout from './components/AppLayout'
import CursorGlow from './components/CursorGlow'
import CursorTrail from './components/CursorTrail'
import LandingPage from './pages/LandingPage'
import LikedVideosPage from './pages/LikedVideosPage'
import PlaylistsPage from './pages/PlaylistsPage'
import PrivacyPage from './pages/PrivacyPage'
import StatusPage from './pages/StatusPage'
import type { UserStatus } from './services'
import { JobProvider } from './state/job'
import { LikedVideosProvider } from './state/likedVideos'
import { PlaylistsProvider } from './state/playlists'
import { QuotaProvider } from './state/quota'
import { HOME_FOR_STATUS, SessionProvider, useSession } from './state/session'

// Phase 1 dev panel: only `npm run dev` loads it, so production builds leave it out entirely.
const DevPanel = import.meta.env.DEV ? lazy(() => import('./components/DevPanel')) : null

/** Signed-out users only; signed-in users go to the screen for their approval status. */
function SignedOutOnly() {
  const { user } = useSession()
  if (user === undefined) return null
  return user ? <Navigate to={HOME_FOR_STATUS[user.status]} replace /> : <Outlet />
}

/** Only users with this approval status; everyone else goes where they belong. */
function RequireStatus({ status }: { status: UserStatus }) {
  const { user } = useSession()
  if (user === undefined) return null
  if (!user) return <Navigate to="/" replace />
  if (user.status !== status) return <Navigate to={HOME_FOR_STATUS[user.status]} replace />
  return <Outlet />
}

export default function App() {
  return (
    <SessionProvider>
      <QuotaProvider>
        <CursorGlow />
        <CursorTrail />
        <Routes>
          <Route element={<SignedOutOnly />}>
            <Route index element={<LandingPage />} />
          </Route>
          <Route element={<RequireStatus status="pending" />}>
            <Route path="pending" element={<StatusPage status="pending" />} />
          </Route>
          <Route element={<RequireStatus status="rejected" />}>
            <Route path="denied" element={<StatusPage status="rejected" />} />
          </Route>
          <Route element={<RequireStatus status="approved" />}>
            <Route
              element={
                <LikedVideosProvider>
                  <PlaylistsProvider>
                    <JobProvider>
                      <AppLayout />
                    </JobProvider>
                  </PlaylistsProvider>
                </LikedVideosProvider>
              }
            >
              <Route path="liked" element={<LikedVideosPage />} />
              <Route path="playlists" element={<PlaylistsPage />} />
            </Route>
          </Route>
          <Route path="privacy" element={<PrivacyPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        {DevPanel && (
          <Suspense>
            <DevPanel />
          </Suspense>
        )}
      </QuotaProvider>
    </SessionProvider>
  )
}
