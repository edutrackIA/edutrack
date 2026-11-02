import type { ReactNode } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'

export const selectClass = 'rounded-md border border-rule bg-surface px-3 py-2 text-ink'

/** Bottom bar of every sheet: pending changes, save button and the result. */
export function SaveBar({
  changes,
  pending,
  saved,
  error,
  label,
  onSave,
  extra,
}: {
  changes: number
  pending: boolean
  saved: boolean
  error: unknown
  label: string
  onSave: () => void
  extra?: ReactNode
}) {
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-4 border-t border-rule pt-4">
      <Button pending={pending} disabled={changes === 0} onClick={onSave}>
        {label}
      </Button>
      {extra}
      <p role="status" aria-live="polite" className="text-sm">
        {changes > 0 ? (
          <span className="text-risk-medium">
            {changes} {changes === 1 ? 'cambio sin guardar' : 'cambios sin guardar'}
          </span>
        ) : (
          saved && <span className="text-risk-low">Guardado.</span>
        )}
      </p>
      {Boolean(error) && <ErrorMessage>{messageFor(error)}</ErrorMessage>}
    </div>
  )
}
