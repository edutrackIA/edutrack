import type { ReactNode } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { ErrorMessage } from '../../../shared/ui/Feedback'

export const inputClass = 'rounded-md border border-rule bg-surface px-3 py-2 text-ink'

/** Labelled control laid out for the inline forms of the setup screens. */
export function Field({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor: string
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-sm font-bold text-ink">
        {label}
      </label>
      {children}
    </div>
  )
}

export function SetupSection({
  title,
  description,
  form,
  children,
}: {
  title: string
  description: string
  form: ReactNode
  children: ReactNode
}) {
  return (
    <section aria-labelledby={`${title}-title`} className="flex flex-col gap-5">
      <div>
        <h2 id={`${title}-title`} className="font-figure text-xl font-semibold text-ink">
          {title}
        </h2>
        <p className="mt-1 text-ink-soft">{description}</p>
      </div>
      <div className="rounded-xl border border-rule bg-surface p-4">{form}</div>
      {children}
    </section>
  )
}

export function MutationError({ error }: { error: unknown }) {
  return error ? <ErrorMessage>{messageFor(error)}</ErrorMessage> : null
}
