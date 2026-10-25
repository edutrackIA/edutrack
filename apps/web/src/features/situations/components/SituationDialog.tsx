import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { Modal } from '../../../shared/ui/Modal'
import {
  useCreateSituation,
  useSituationCatalog,
  useUpdateSituation,
  type Situation,
} from '../api'

const NOTE_HINT =
  'Opcional. Escribe solo lo necesario para el equipo: sin diagnósticos ni detalles médicos.'

function NoteField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const id = useId()
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="font-bold text-ink">
        Nota para el equipo
      </label>
      <textarea
        id={id}
        rows={3}
        maxLength={500}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-describedby={`${id}-hint`}
        className="resize-y rounded-md border border-rule bg-surface px-3 py-2 text-ink"
      />
      <p id={`${id}-hint`} className="text-sm text-ink-soft">
        {NOTE_HINT}
      </p>
    </div>
  )
}

function CreateForm({
  studentId,
  today,
  onDone,
}: {
  studentId: number
  today: string
  onDone: () => void
}) {
  const catalog = useSituationCatalog()
  const create = useCreateSituation()
  const [kind, setKind] = useState('')
  const [note, setNote] = useState('')
  const [startedOn, setStartedOn] = useState(today)
  const kindId = useId()
  const dateId = useId()
  const selected = catalog.data?.find((item) => item.kind === kind)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    create.mutate(
      { studentId, kind, note: note.trim(), startedOn },
      { onSuccess: onDone },
    )
  }

  const groups = [
    { group: 'MESSAGE', label: 'Ajustan el mensaje a la familia' },
    { group: 'TEAM', label: 'Solo para el equipo (nunca llegan a la familia)' },
  ] as const

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <label htmlFor={kindId} className="font-bold text-ink">
          Situación
        </label>
        <select
          id={kindId}
          required
          value={kind}
          onChange={(event) => setKind(event.target.value)}
          className="rounded-md border border-rule bg-surface px-3 py-2.5 text-ink"
        >
          <option value="">Elige una situación</option>
          {groups.map(({ group, label }) => (
            <optgroup key={group} label={label}>
              {catalog.data
                ?.filter((item) => item.group === group)
                .map((item) => (
                  <option key={item.kind} value={item.kind}>
                    {item.label}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>
        {selected && (
          <p className="text-sm text-ink-soft">
            {selected.description}
            {selected.group === 'TEAM' && ' La familia no verá esta situación.'}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={dateId} className="font-bold text-ink">
          Desde cuándo
        </label>
        <input
          id={dateId}
          type="date"
          max={today}
          value={startedOn}
          onChange={(event) => setStartedOn(event.target.value)}
          className="w-fit rounded-md border border-rule bg-surface px-3 py-2 text-ink"
        />
      </div>

      <NoteField value={note} onChange={setNote} />

      {create.isError && <ErrorMessage>{messageFor(create.error)}</ErrorMessage>}
      <div>
        <Button type="submit" pending={create.isPending} disabled={!kind}>
          Guardar situación
        </Button>
      </div>
    </form>
  )
}

function EditForm({ situation, onDone }: { situation: Situation; onDone: () => void }) {
  const update = useUpdateSituation()
  const [note, setNote] = useState(situation.note ?? '')

  return (
    <div className="flex flex-col gap-5">
      <p className="text-ink-soft">
        Desde el {formatDate(situation.started_on)}.
        {situation.group === 'TEAM' && ' La familia no ve esta situación.'}
      </p>
      <NoteField value={note} onChange={setNote} />
      {update.isError && <ErrorMessage>{messageFor(update.error)}</ErrorMessage>}
      <div className="flex flex-wrap gap-3">
        <Button
          pending={update.isPending}
          onClick={() => update.mutate({ id: situation.id, note: note.trim() }, { onSuccess: onDone })}
        >
          Guardar nota
        </Button>
        <Button
          variant="secondary"
          disabled={update.isPending}
          onClick={() => update.mutate({ id: situation.id, resolved: true }, { onSuccess: onDone })}
        >
          Marcar como resuelta
        </Button>
      </div>
    </div>
  )
}

export type SituationDialogState =
  | { mode: 'create'; studentId: number; studentName: string }
  | { mode: 'edit'; situation: Situation; studentName: string }
  | null

export function SituationDialog({
  state,
  today,
  onClose,
}: {
  state: SituationDialogState
  today: string
  onClose: () => void
}) {
  const title =
    state?.mode === 'edit' ? state.situation.label : 'Marcar una situación'
  return (
    <Modal
      open={state !== null}
      onClose={onClose}
      title={title}
      description={state?.studentName}
    >
      {state?.mode === 'create' && (
        <CreateForm studentId={state.studentId} today={today} onDone={onClose} />
      )}
      {state?.mode === 'edit' && <EditForm situation={state.situation} onDone={onClose} />}
    </Modal>
  )
}
