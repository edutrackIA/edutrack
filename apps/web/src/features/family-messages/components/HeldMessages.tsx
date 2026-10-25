import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { useHeldMessages, useReviewMessage, type FamilyMessage } from '../api'

function HeldMessage({ message }: { message: FamilyMessage }) {
  const review = useReviewMessage()

  return (
    <li className="rounded-lg border border-rule bg-surface p-4">
      <p className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-bold text-ink">{message.student.full_name}</span>
        <span className="text-sm text-ink-soft">
          {message.kind_label}. {message.hold_reason}
        </span>
      </p>
      <p className="mt-2 text-ink">{message.intro}</p>
      <dl className="mt-2 text-sm">
        {message.rows.map(([label, value]) => (
          <div key={label} className="flex gap-2">
            <dt className="text-ink-soft">{label}:</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {review.isError && (
        <div className="mt-3">
          <ErrorMessage>{messageFor(review.error)}</ErrorMessage>
        </div>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="secondary"
          pending={review.isPending && review.variables?.action === 'release'}
          disabled={review.isPending}
          onClick={() => review.mutate({ id: message.id, action: 'release' })}
        >
          Enviar a la familia
          <span className="sr-only"> el mensaje de {message.student.full_name}</span>
        </Button>
        <Button
          variant="ghost"
          disabled={review.isPending}
          onClick={() => review.mutate({ id: message.id, action: 'discard' })}
        >
          No enviar
          <span className="sr-only"> el mensaje de {message.student.full_name}</span>
        </Button>
      </div>
    </li>
  )
}

/**
 * Automatic data messages (attendance, grades) held because the student has a sensitive
 * situation. The tutor decides whether the family should receive them.
 */
export function HeldMessages() {
  const held = useHeldMessages()
  if (!held.data || held.data.length === 0) return null

  return (
    <section aria-labelledby="held-title" className="shrink-0">
      <h2 id="held-title" className="font-figure text-lg font-semibold text-ink">
        Mensajes automáticos retenidos ({held.data.length})
      </h2>
      <p className="mt-1 text-sm text-ink-soft">
        No se enviaron porque el estudiante tiene una situación activa. Revisa si conviene que la
        familia los reciba.
      </p>
      <ul className="mt-3 grid gap-3 lg:grid-cols-2">
        {held.data.map((message) => (
          <HeldMessage key={message.id} message={message} />
        ))}
      </ul>
    </section>
  )
}
