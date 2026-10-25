import { useId, useState } from 'react'
import { Link } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import { useRecordLinkState } from '../../students/navigation'
import {
  useApproveRecommendation,
  useDiscardRecommendation,
  useResendRecommendation,
  useSaveRecommendation,
  type ReviewItem,
} from '../api'

const MAX_ITEMS = 6

function clean(items: string[]): string[] {
  return items.map((item) => item.trim()).filter(Boolean)
}

function ItemField({
  index,
  value,
  onChange,
  onRemove,
  canRemove,
}: {
  index: number
  value: string
  onChange: (value: string) => void
  onRemove: () => void
  canRemove: boolean
}) {
  const id = useId()
  return (
    <li className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-3">
        <label htmlFor={id} className="text-sm font-bold text-ink">
          Recomendación {index + 1}
        </label>
        {canRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="text-sm text-ink-soft hover:text-risk-high"
          >
            Quitar<span className="sr-only"> la recomendación {index + 1}</span>
          </button>
        )}
      </div>
      <textarea
        id={id}
        rows={3}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="resize-y rounded-md border border-rule bg-surface px-3 py-2 text-ink"
      />
    </li>
  )
}

export function RecommendationEditor({
  recommendation,
  onDone,
}: {
  recommendation: ReviewItem
  onDone: (message: string) => void
}) {
  const [items, setItems] = useState(recommendation.parent_items)
  const [confirmingDiscard, setConfirmingDiscard] = useState(false)
  const save = useSaveRecommendation()
  const approve = useApproveRecommendation()
  const discard = useDiscardRecommendation()
  const resend = useResendRecommendation()
  const linkState = useRecordLinkState()

  const pending = recommendation.status === 'PENDING_REVIEW'
  const cleaned = clean(items)
  const dirty = JSON.stringify(cleaned) !== JSON.stringify(recommendation.parent_items)
  const busy = save.isPending || approve.isPending || discard.isPending || resend.isPending
  const error = save.error ?? approve.error ?? discard.error ?? resend.error
  const { student } = recommendation

  function updateItem(index: number, value: string) {
    setItems(items.map((item, i) => (i === index ? value : item)))
  }

  function handleApprove() {
    approve.mutate(
      { id: recommendation.id, items: dirty ? cleaned : undefined },
      {
        onSuccess: (item) =>
          onDone(
            item.sent_at
              ? `Recomendación de ${student.full_name} aprobada y enviada a la familia.`
              : `Recomendación de ${student.full_name} aprobada. El correo no se pudo enviar; puedes reenviarlo desde Aprobadas.`,
          ),
      },
    )
  }

  return (
    <article aria-labelledby="editor-title" className="flex flex-col gap-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="editor-title" className="font-figure text-2xl font-semibold text-ink">
            {student.full_name}
          </h2>
          <p className="mt-1 flex flex-wrap items-center gap-3 text-ink-soft">
            {student.classroom}
            {student.risk_level && <RiskBadge level={student.risk_level} />}
          </p>
        </div>
        <Link
          to={`/estudiantes/${student.id}`}
          state={linkState}
          className="text-sm font-bold text-accent hover:underline"
        >
          Ver ficha completa
        </Link>
      </header>

      <section aria-labelledby="family-title">
        <h3 id="family-title" className="font-bold text-ink">
          Lo que recibirá la familia
        </h3>
        <p className="mt-1 text-sm text-ink-soft">
          El correo indica que estas sugerencias se generaron con Machine Learning y que tú las
          revisaste.
        </p>
        {pending ? (
          <>
            <ol className="mt-4 flex flex-col gap-4">
              {items.map((item, index) => (
                <ItemField
                  key={index}
                  index={index}
                  value={item}
                  onChange={(value) => updateItem(index, value)}
                  onRemove={() => setItems(items.filter((_, i) => i !== index))}
                  canRemove={items.length > 1}
                />
              ))}
            </ol>
            {items.length < MAX_ITEMS && (
              <Button variant="ghost" className="mt-2" onClick={() => setItems([...items, ''])}>
                Agregar recomendación
              </Button>
            )}
          </>
        ) : (
          <ol className="mt-3 list-decimal space-y-2 pl-5">
            {recommendation.parent_items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        )}
      </section>

      <section aria-labelledby="teacher-title">
        <h3 id="teacher-title" className="font-bold text-ink">
          Acciones sugeridas para ti
        </h3>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-ink">
          {recommendation.teacher_items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      {error && <ErrorMessage>{messageFor(error)}</ErrorMessage>}

      {pending && (
        <footer className="flex flex-wrap items-center gap-3 border-t border-rule pt-5">
          <Button pending={approve.isPending} disabled={busy || cleaned.length === 0} onClick={handleApprove}>
            Aprobar y enviar a la familia
          </Button>
          {dirty && (
            <Button
              variant="secondary"
              pending={save.isPending}
              disabled={busy || cleaned.length === 0}
              onClick={() =>
                save.mutate(
                  { id: recommendation.id, items: cleaned },
                  { onSuccess: () => onDone('Cambios guardados.') },
                )
              }
            >
              Guardar cambios
            </Button>
          )}
          {confirmingDiscard ? (
            <span className="flex flex-wrap items-center gap-2">
              <span className="text-sm text-ink">¿Descartar? La familia no recibirá nada.</span>
              <Button
                variant="secondary"
                pending={discard.isPending}
                disabled={busy}
                onClick={() =>
                  discard.mutate(recommendation.id, {
                    onSuccess: () =>
                      onDone(`Recomendación de ${student.full_name} descartada.`),
                  })
                }
              >
                Sí, descartar
              </Button>
              <Button variant="ghost" onClick={() => setConfirmingDiscard(false)}>
                Cancelar
              </Button>
            </span>
          ) : (
            <Button variant="ghost" disabled={busy} onClick={() => setConfirmingDiscard(true)}>
              Descartar
            </Button>
          )}
        </footer>
      )}

      {recommendation.status === 'APPROVED' && (
        <footer className="flex flex-wrap items-center gap-3 border-t border-rule pt-5">
          {recommendation.sent_at ? (
            <p className="text-ink-soft">
              Enviada a la familia el {formatDate(recommendation.sent_at)}.
            </p>
          ) : (
            <>
              <p className="text-ink-soft">Aprobada, pero el correo aún no se envió.</p>
              <Button
                variant="secondary"
                pending={resend.isPending}
                onClick={() =>
                  resend.mutate(recommendation.id, {
                    onSuccess: () => onDone('Correo enviado a la familia.'),
                  })
                }
              >
                Reenviar correo
              </Button>
            </>
          )}
        </footer>
      )}
    </article>
  )
}
