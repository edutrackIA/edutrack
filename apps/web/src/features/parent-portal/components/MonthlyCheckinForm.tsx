import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import {
  useSubmitCheckin,
  type FamilyCheckin,
  type FamilyMood,
  type HomeChange,
} from '../api'

const MOODS: { value: FamilyMood; label: string }[] = [
  { value: 'GOOD', label: 'Lo vemos bien' },
  { value: 'OK', label: 'Regular' },
  { value: 'WORRIED', label: 'Nos preocupa' },
]

const CHANGES: { value: HomeChange; label: string }[] = [
  { value: 'MOVING', label: 'Mudanza' },
  { value: 'HEALTH', label: 'Salud de algún familiar o del estudiante' },
  { value: 'PARENTS_WORK', label: 'Cambios en el trabajo de los padres' },
  { value: 'CARING_FAMILY', label: 'Cuidado de hermanos o familiares' },
  { value: 'ECONOMIC', label: 'Dificultades económicas' },
  { value: 'OTHER', label: 'Otro cambio' },
]

// prettier-ignore
const MONTHS = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

export function MonthlyCheckinForm({
  studentId,
  name,
  month,
  current,
}: {
  studentId: number
  name: string
  month: string
  current: FamilyCheckin | null
}) {
  const submit = useSubmitCheckin(studentId)
  const [mood, setMood] = useState<FamilyMood | null>(current?.mood ?? null)
  const [changes, setChanges] = useState<HomeChange[]>(current?.home_changes ?? [])
  const [peerConcern, setPeerConcern] = useState(current?.peer_concern ?? false)
  const [comment, setComment] = useState(current?.comment ?? '')
  const [saved, setSaved] = useState(false)
  const commentId = useId()
  const monthName = MONTHS[Number(month.slice(5, 7)) - 1]

  function toggle(change: HomeChange) {
    setChanges((list) =>
      list.includes(change) ? list.filter((item) => item !== change) : [...list, change],
    )
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!mood) return
    submit.mutate(
      { mood, home_changes: changes, peer_concern: peerConcern, comment: comment.trim() || null },
      { onSuccess: () => setSaved(true) },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {current && !saved && (
        <p className="text-sm text-ink-soft">
          Ya respondió el seguimiento de {monthName}. Puede actualizarlo si algo cambió.
        </p>
      )}

      <fieldset>
        <legend className="font-bold text-ink">¿Cómo ve a {name} este mes?</legend>
        <div className="mt-2 grid gap-2 sm:grid-cols-3">
          {MOODS.map((option) => (
            <label
              key={option.value}
              className={`flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2.5 ${
                mood === option.value ? 'border-accent bg-accent-tint' : 'border-rule bg-surface'
              }`}
            >
              <input
                type="radio"
                name="mood"
                value={option.value}
                checked={mood === option.value}
                onChange={() => setMood(option.value)}
                className="accent-accent"
              />
              {option.label}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="font-bold text-ink">¿Hubo algún cambio en casa?</legend>
        <p className="text-sm text-ink-soft">Marque solo si aplica. Es información para el tutor.</p>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {CHANGES.map((option) => (
            <label key={option.value} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={changes.includes(option.value)}
                onChange={() => toggle(option.value)}
                className="accent-accent"
              />
              {option.label}
            </label>
          ))}
        </div>
      </fieldset>

      <label className="flex items-start gap-2 rounded-md border border-rule bg-surface p-3">
        <input
          type="checkbox"
          checked={peerConcern}
          onChange={(event) => setPeerConcern(event.target.checked)}
          className="mt-1 accent-accent"
        />
        <span>
          <span className="font-bold">Me preocupa cómo lo tratan sus compañeros</span>
          <span className="block text-sm text-ink-soft">
            El tutor recibirá un aviso prioritario y se comunicará con usted.
          </span>
        </span>
      </label>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={commentId} className="font-bold text-ink">
          Comentario para el tutor (opcional)
        </label>
        <textarea
          id={commentId}
          rows={3}
          maxLength={500}
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          className="resize-y rounded-md border border-rule bg-surface px-3 py-2 text-ink"
        />
      </div>

      {submit.isError && <ErrorMessage>{messageFor(submit.error)}</ErrorMessage>}
      <div role="status" aria-live="polite">
        {saved && (
          <p className="rounded-md bg-risk-low-bg px-3 py-2 text-risk-low">
            Gracias. El tutor recibió su respuesta de {monthName}.
          </p>
        )}
      </div>
      <div>
        <Button type="submit" pending={submit.isPending} disabled={!mood}>
          {current ? 'Actualizar respuesta' : 'Enviar respuesta'}
        </Button>
      </div>
    </form>
  )
}
