import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b-2 border-ink pb-4">
      <div>
        <h1 className="font-figure text-3xl font-semibold text-ink">{title}</h1>
        {description && <p className="mt-1 max-w-prose text-ink-soft">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </header>
  )
}
