import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { apiRequest } from '../../../shared/api/client'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { Modal } from '../../../shared/ui/Modal'
import type { ExitReason, StudentDetail, StudentStatus } from '../types'

export const EXIT_REASONS: Record<ExitReason, string> = {
  TRANSFER: 'Traslado a otro colegio',
  WORK: 'Trabajo',
  ECONOMIC: 'Situación económica',
  FAMILY: 'Situación familiar',
  HEALTH: 'Salud',
  PREGNANCY: 'Embarazo o paternidad',
  DISTANCE: 'Distancia o transporte',
  DISENGAGEMENT: 'Desmotivación',
  UNKNOWN: 'No se conoce el motivo',
  GRADUATION: 'Egreso',
}

const STATUS_LABELS: Record<Exclude<StudentStatus, 'ENROLLED'>, string> = {
  WITHDRAWN: 'Se retiró',
  TRANSFERRED: 'Se trasladó',
  GRADUATED: 'Egresó',
}

const DROPOUT_REASONS: ExitReason[] = [
  'WORK',
  'ECONOMIC',
  'FAMILY',
  'HEALTH',
  'PREGNANCY',
  'DISTANCE',
  'DISENGAGEMENT',
  'UNKNOWN',
]

const inputClass = 'rounded-md border border-rule bg-surface px-3 py-2 text-ink'

function useEnrollmentMutations(studentId: number) {
  const queryClient = useQueryClient()
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['students', studentId] })
  return {
    withdraw: useMutation({
      mutationFn: (body: { exit_date: string; reason: ExitReason; note: string | null }) =>
        apiRequest<StudentDetail>(`/students/${studentId}/withdrawal`, { method: 'POST', body }),
      onSuccess: refresh,
    }),
    reinstate: useMutation({
      mutationFn: () =>
        apiRequest<StudentDetail>(`/students/${studentId}/reinstatement`, { method: 'POST' }),
      onSuccess: refresh,
    }),
  }
}

function WithdrawalForm({ studentId, onDone }: { studentId: number; onDone: () => void }) {
  const { withdraw } = useEnrollmentMutations(studentId)
  const [reason, setReason] = useState<ExitReason>('TRANSFER')
  const [exitDate, setExitDate] = useState('')
  const [note, setNote] = useState('')
  const ids = { reason: useId(), date: useId(), note: useId() }
  const now = new Date()
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    withdraw.mutate(
      { exit_date: exitDate, reason, note: note.trim() || null },
      { onSuccess: onDone },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor={ids.reason} className="font-bold text-ink">
          Motivo
        </label>
        <select
          id={ids.reason}
          value={reason}
          onChange={(event) => setReason(event.target.value as ExitReason)}
          className={inputClass}
        >
          <option value="TRANSFER">{EXIT_REASONS.TRANSFER}</option>
          <optgroup label="Dejó de estudiar">
            {DROPOUT_REASONS.map((value) => (
              <option key={value} value={value}>
                {EXIT_REASONS[value]}
              </option>
            ))}
          </optgroup>
        </select>
        <p className="text-sm text-ink-soft">
          {reason === 'TRANSFER'
            ? 'Un traslado no cuenta como deserción.'
            : 'Se registra como deserción: es el dato real con el que el modelo aprende.'}
        </p>
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={ids.date} className="font-bold text-ink">
          Fecha de salida
        </label>
        <input id={ids.date} type="date" required max={today} value={exitDate} onChange={(event) => setExitDate(event.target.value)} className={`${inputClass} w-fit`} />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={ids.note} className="font-bold text-ink">
          Nota (opcional)
        </label>
        <textarea id={ids.note} rows={3} maxLength={500} value={note} onChange={(event) => setNote(event.target.value)} className={`${inputClass} resize-y`} />
      </div>
      {withdraw.isError && <ErrorMessage>{messageFor(withdraw.error)}</ErrorMessage>}
      <div>
        <Button type="submit" pending={withdraw.isPending} disabled={!exitDate}>
          Registrar salida
        </Button>
      </div>
    </form>
  )
}

/** Banner shown to everyone when the student is no longer enrolled. */
export function ExitBanner({
  student,
  canManage,
}: {
  student: StudentDetail
  canManage: boolean
}) {
  const { reinstate } = useEnrollmentMutations(student.id)
  const [confirming, setConfirming] = useState(false)
  if (student.status === 'ENROLLED') return null

  return (
    <div role="status" className="mb-6 rounded-xl border border-risk-medium/40 bg-risk-medium-bg p-4 text-risk-medium">
      <p className="font-bold">
        {STATUS_LABELS[student.status]}
        {student.exit_date && ` el ${formatDate(student.exit_date)}`}
        {student.exit_reason && student.exit_reason !== 'GRADUATION' && `: ${EXIT_REASONS[student.exit_reason]}`}.
      </p>
      {student.exit_note && <p className="mt-1">{student.exit_note}</p>}
      {canManage && student.status !== 'GRADUATED' && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {confirming ? (
            <>
              <span>¿Volver a matricularlo? Úsalo si se registró por error o si regresó.</span>
              <Button variant="secondary" pending={reinstate.isPending} onClick={() => reinstate.mutate()}>
                Sí, matricular de nuevo
              </Button>
              <Button variant="ghost" onClick={() => setConfirming(false)}>
                Cancelar
              </Button>
            </>
          ) : (
            <Button variant="ghost" onClick={() => setConfirming(true)}>
              Revertir salida
            </Button>
          )}
          {reinstate.isError && <ErrorMessage>{messageFor(reinstate.error)}</ErrorMessage>}
        </div>
      )}
    </div>
  )
}

/** Action to register that an enrolled student left the school. */
export function WithdrawalAction({ student }: { student: StudentDetail }) {
  const [open, setOpen] = useState(false)
  if (student.status !== 'ENROLLED') return null
  return (
    <>
      <Button variant="ghost" onClick={() => setOpen(true)}>
        Registrar retiro o traslado
      </Button>
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Registrar retiro o traslado"
        description={`${student.last_name}, ${student.first_name}`}
      >
        {open && <WithdrawalForm studentId={student.id} onDone={() => setOpen(false)} />}
      </Modal>
    </>
  )
}
