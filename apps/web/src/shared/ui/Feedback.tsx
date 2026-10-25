import type { ReactNode } from 'react'
import { Spinner } from './Spinner'

export function LoadingState({ label = 'Cargando…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 py-10 text-ink-soft">
      <Spinner />
      <span>{label}</span>
    </div>
  )
}

export function FullPageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <LoadingState label="Abriendo EduTrack…" />
    </div>
  )
}

export function ErrorMessage({ children }: { children: ReactNode }) {
  return (
    <div
      role="alert"
      className="rounded-md border border-risk-high/30 bg-risk-high-bg px-4 py-3 text-risk-high"
    >
      {children}
    </div>
  )
}

interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="bg-ruled rounded-lg border border-rule px-6 py-12 text-center">
      <p className="font-figure text-xl font-semibold text-ink">{title}</p>
      {description && <p className="mx-auto mt-2 max-w-prose text-ink-soft">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
