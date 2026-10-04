import type { ReactNode } from 'react'
import { Link } from 'react-router'
import Footer from '../components/Footer'
import Logo from '../components/Logo'
import { ADMIN_EMAIL, EXTERNAL_LINKS } from '../config'

// Privacy Policy (SPEC.md sections 9 and 10).
const EFFECTIVE_DATE = 'October 2, 2026'

const RETENTION: [string, string][] = [
  ['Account details: name, email address, profile image, account status', 'Until you ask us to delete them'],
  ['Google sign-in tokens (stored encrypted)', 'Until your account is deleted'],
  ['Job history: video IDs, video titles and the result of each item', '30 days'],
  ['Quota usage records', '30 days'],
  ['Your liked videos and video details', 'Not stored. Kept in memory only while you are signed in'],
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
              LikeCleaner is a small web tool that helps you clean up your YouTube liked videos and playlists. It is
              available only to people the admin has registered. This policy explains what we collect, why, and how long
              we keep it.
            </p>
          </Section>

          <Section title="Information we collect">
            <ul className="list-disc space-y-1 pl-5">
              <li>Your name, email address and profile image from your Google account.</li>
              <li>Google OAuth tokens that let LikeCleaner act on your YouTube account when you ask it to.</li>
              <li>A record of the jobs you run (for example, which videos were removed and whether each step succeeded).</li>
            </ul>
          </Section>

          <Section title="How we use your information">
            <p>
              We use your information only to show your YouTube data on screen and to perform the cleanup actions you
              request, such as removing likes, adding videos to a playlist, or removing videos from a playlist.
            </p>
            <p>
              We do not use your data for analytics or advertising, and we do not sell or share it with third parties.
              We do not collect usage statistics.
            </p>
            <p>
              LikeCleaner&apos;s use of information received from Google APIs follows the Google API Services User Data
              Policy, including the Limited Use requirements.
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
              To delete your account and all related data, email{' '}
              <a href={`mailto:${ADMIN_EMAIL}`} className={linkClass}>
                {ADMIN_EMAIL}
              </a>
              . The admin will delete it from our database.
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
              Questions about this policy? Email{' '}
              <a href={`mailto:${ADMIN_EMAIL}`} className={linkClass}>
                {ADMIN_EMAIL}
              </a>
              .
            </p>
          </Section>
        </article>
      </main>
      <Footer />
    </div>
  )
}
