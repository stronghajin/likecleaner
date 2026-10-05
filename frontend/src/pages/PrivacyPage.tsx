import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import Footer from '../components/Footer'
import Logo from '../components/Logo'
import { EXTERNAL_LINKS } from '../config'
import { api } from '../services'

// Privacy Policy (SPEC.md sections 9 and 10), matching how the real backend works (DECISIONS.md 56, 58, 63, 64).
const EFFECTIVE_DATE = 'October 5, 2026'

const RETENTION: [string, string][] = [
  [
    'Account details: name, email address, profile image and whether your access is active',
    'Until you ask us to delete them',
  ],
  ['Google sign-in token (refresh token, stored encrypted)', 'Until your account is deleted'],
  [
    'Job history: video IDs, video titles, the playlist name and the result or error of each item',
    '30 days',
  ],
  ['Quota usage records: which YouTube API call was made, when, and its cost', '30 days'],
  [
    'Your liked videos, playlist items and video details',
    'Never saved to our database. Kept only in the server\'s memory while you use the app, deleted when you sign out, and for 7 days at most',
  ],
]

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="text-base font-semibold text-accent">{title}</h2>
      <div className="mt-2 space-y-2 leading-relaxed text-text/90">{children}</div>
    </section>
  )
}

export default function PrivacyPage() {
  const linkClass = 'underline hover:text-accent'
  // ADMIN_EMAIL from the backend settings (DECISIONS.md 64).
  const [adminEmail, setAdminEmail] = useState<string | null>(null)

  useEffect(() => {
    api.getAppInfo().then((info) => setAdminEmail(info.adminEmail), () => {})
  }, [])

  const adminLink = adminEmail ? (
    <a href={`mailto:${adminEmail}`} className={linkClass}>
      {adminEmail}
    </a>
  ) : (
    'the admin'
  )

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex h-16 items-center justify-between border-b px-8">
        <Logo />
        {/* "/" sends signed-in users back to their own screen. */}
        <Link to="/" className="rounded-sm px-3 py-1.5 font-medium text-muted hover:bg-text/5 hover:text-text">
          Back
        </Link>
      </header>

      <main className="flex-1 px-8 py-10">
        <article className="max-w-3xl">
          <h1 className="text-2xl font-semibold">Privacy Policy</h1>
          <p className="mt-2 text-muted">Effective date: {EFFECTIVE_DATE}</p>

          <Section title="Overview">
            <p>
              LikeCleaner is a small web tool that helps you clean up your YouTube liked videos and playlists. Only
              people whose Google account email the admin has registered can use it. This policy explains what we
              collect, why, how long we keep it, and how to have it deleted.
            </p>
          </Section>

          <Section title="Information we collect">
            <ul className="list-disc space-y-1 pl-5">
              <li>Your name, email address and profile image from your Google account.</li>
              <li>
                Google OAuth tokens that let LikeCleaner read and change your YouTube likes and playlists when you ask
                it to. The long-lived token is stored encrypted.
              </li>
              <li>
                A record of the jobs you run: the IDs and titles of the videos in each job, the playlist involved, and
                whether each step succeeded or failed.
              </li>
              <li>A record of each YouTube API call made for you and its quota cost, to keep within YouTube&apos;s daily limit.</li>
            </ul>
          </Section>

          <Section title="How we use your information">
            <p>
              We use your information only to show your YouTube data on screen and to perform the cleanup actions you
              request, such as removing likes, adding videos to a playlist, or removing videos from a playlist. Your
              liked videos and playlists are read from YouTube when you open them or press Resync, and are not saved to
              our database.
            </p>
            <p>
              We do not use your data for analytics or advertising, and we do not sell or share it with third parties.
              We do not collect usage statistics.
            </p>
            <p>
              LikeCleaner&apos;s use of information received from Google APIs follows the{' '}
              <a href={EXTERNAL_LINKS.googleUserDataPolicy} target="_blank" rel="noreferrer" className={linkClass}>
                Google API Services User Data Policy
              </a>
              , including the Limited Use requirements.
            </p>
          </Section>

          <Section title="How long we keep it">
            <table className="mt-2 w-full border text-left">
              <thead className="bg-panel">
                <tr>
                  <th className="border-b px-4 py-2 font-bold text-accent">Data</th>
                  <th className="border-b px-4 py-2 font-bold text-accent">Kept for</th>
                </tr>
              </thead>
              <tbody>
                {RETENTION.map(([data, period]) => (
                  <tr key={data} className="border-b last:border-b-0">
                    <td className="px-4 py-2">{data}</td>
                    <td className="px-4 py-2 text-muted">{period}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p>Data with a 30-day limit is deleted automatically every day. We never keep YouTube API data for more than 30 days.</p>
          </Section>

          <Section title="Deleting your data">
            <p>
              To delete your account and all related data, email {adminLink} from the Google account you use with
              LikeCleaner. The admin will delete your account, your stored token and your job history from our
              database.
            </p>
            <p>
              Signing out ends your session but does not remove LikeCleaner&apos;s access to your Google account. You
              can remove that access at any time from your{' '}
              <a href={EXTERNAL_LINKS.googlePermissions} target="_blank" rel="noreferrer" className={linkClass}>
                Google Account permissions page
              </a>
              .
            </p>
          </Section>

          <Section title="Third-party services">
            <p>
              LikeCleaner uses YouTube API Services. By using LikeCleaner you agree to the{' '}
              <a href={EXTERNAL_LINKS.youtubeTerms} target="_blank" rel="noreferrer" className={linkClass}>
                YouTube Terms of Service
              </a>
              . Google&apos;s handling of your data is described in the{' '}
              <a href={EXTERNAL_LINKS.googlePrivacy} target="_blank" rel="noreferrer" className={linkClass}>
                Google Privacy Policy
              </a>
              .
            </p>
          </Section>

          <Section title="Contact">
            <p>
              Questions about this policy? Email {adminLink}.
            </p>
          </Section>
        </article>
      </main>
      <Footer />
    </div>
  )
}
