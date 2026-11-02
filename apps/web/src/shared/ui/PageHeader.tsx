import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
  className?: string
}

export function PageHeader({ title, description, actions, className = 'mb-8' }: PageHeaderProps) {
  return (
    <header
      className={`flex flex-wrap items-end justify-between gap-4 border-b-2 border-ink pb-4 ${className}`}
    >
      <div>
        <h1 className="font-figure text-3xl font-semibold text-ink">{title}</h1>
        {description && <p className="mt-1 max-w-prose text-ink-soft">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
    </header>
  )
}
