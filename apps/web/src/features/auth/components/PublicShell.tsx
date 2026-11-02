import type { ReactNode } from 'react'
import { ThemeToggle } from '../../../shared/ui/ThemeToggle'

/** Centered layout for the pages people open without a session. */
export function PublicShell({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <main className="relative flex min-h-screen items-center justify-center px-6 py-12">
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <div className={`w-full ${wide ? 'max-w-2xl' : 'max-w-md'}`}>
        <p className="mb-10 font-figure text-2xl font-semibold text-ink">EduTrack</p>
        {children}
      </div>
    </main>
  )
}
