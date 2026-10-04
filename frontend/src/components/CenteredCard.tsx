import type { ReactNode } from 'react'
import Footer from './Footer'

// Full-screen frame for the screens shown before the main app (sign-in, access denied).
export default function CenteredCard({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex flex-1 items-center justify-center p-8">
        <div className="w-[560px] border bg-panel p-10">{children}</div>
      </main>
      <Footer />
    </div>
  )
}
