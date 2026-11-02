import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { apiRequest } from '../../../shared/api/client'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { Modal } from '../../../shared/ui/Modal'
import type { User } from '../../auth/types'
import type { Commitment, CommitmentStatus } from '../types'

const STATUS: Record<CommitmentStatus, { label: string; className: string }> = {
  OPEN: { label: 'En seguimiento', className: 'bg-risk-medium-bg text-risk-medium' },
  FULFILLED: { label: 'Cumplido', className: 'bg-risk-low-bg text-risk-low' },
  BREACHED: { label: 'No cumplido', className: 'bg-risk-high-bg text-risk-high' },
}

const inputClass = 'rounded-md border border-rule bg-surface px-3 py-2 text-ink'

function useCommitmentMutations(studentId: number) {
  const queryClient = useQueryClient()
  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ['students', studentId, 'commitments'] })
  const create = useMutation({
    mutationFn: (body: {
      guardian_id: number
      meeting_date: string
      agreements: string
      follow_up_date: string | null
    }) =>
      apiRequest<Commitment>(`/students/${studentId}/commitments`, { method: 'POST', body }),
    onSuccess: refresh,
  })
  const update = useMutation({
    mutationFn: ({ id, status }: { id: number; status: CommitmentStatus }) =>
      apiRequest<Commitment>(`/students/${studentId}/commitments/${id}`, {
        method: 'PATCH',
        body: { status },
      }),
    onSuccess: refresh,
  })
  return { create, update }
}

function NewCommitmentForm({
  studentId,
  guardians,
  onDone,
}: {
  studentId: number
  guardians: User[]
  onDone: () => void
}) {
  const { create } = useCommitmentMutations(studentId)
  const [guardianId, setGuardianId] = useState(guardians[0]?.id ?? 0)
  const [meetingDate, setMeetingDate] = useState('')
  const [agreements, setAgreements] = useState('')
  const [followUp, setFollowUp] = useState('')
  const ids = { guardian: useId(), meeting: useId(), agreements: useId(), followUp: useId() }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    create.mutate(
      {
        guardian_id: guardianId,
        meeting_date: meetingDate,
        agreements: agreements.trim(),
        follow_up_date: followUp || null,
      },
      { onSuccess: onDone },
    )
  }

  if (guardians.length === 0) {
    return (
      <p className="text-ink-soft">
        El estudiante no tiene apoderados registrados. La dirección o el área de análisis puede
        registrarlos desde esta ficha.
      </p>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor={ids.guardian} className="font-bold text-ink">
          Apoderado presente
        </label>
        <select
          id={ids.guardian}
          value={guardianId}
          onChange={(event) => setGuardianId(Number(event.target.value))}
          className={`${inputClass} w-fit`}
        >
          {guardians.map((guardian) => (
            <option key={guardian.id} value={guardian.id}>
              {guardian.full_name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-wrap gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.meeting} className="font-bold text-ink">
            Fecha de la reunión
          </label>
          <input id={ids.meeting} type="date" required value={meetingDate} onChange={(event) => setMeetingDate(event.target.value)} className={inputClass} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.followUp} className="font-bold text-ink">
            Fecha de seguimiento (opcional)
          </label>
          <input id={ids.followUp} type="date" min={meetingDate || undefined} value={followUp} onChange={(event) => setFollowUp(event.target.value)} className={inputClass} />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={ids.agreements} className="font-bold text-ink">
          Acuerdos
        </label>
        <textarea
          id={ids.agreements}
          rows={4}
          maxLength={4000}
          value={agreements}
          onChange={(event) => setAgreements(event.target.value)}
          className={`${inputClass} resize-y`}
        />
      </div>
      {create.isError && <ErrorMessage>{messageFor(create.error)}</ErrorMessage>}
      <div>
        <Button type="submit" pending={create.isPending} disabled={!meetingDate || !agreements.trim()}>
          Guardar acta
        </Button>
      </div>
    </form>
  )
}

/** Meetings with the family and their agreements; the tutor and direction can manage them. */
export function CommitmentsCard({
  studentId,
  studentName,
  commitments,
  guardians,
  canManage,
}: {
  studentId: number
  studentName: string
  commitments: Commitment[]
  guardians: User[]
  canManage: boolean
}) {
  const { update } = useCommitmentMutations(studentId)
  const [adding, setAdding] = useState(false)

  return (
    <section className="rounded-xl border border-rule bg-surface p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-figure text-xl font-semibold text-ink">Actas con la familia</h2>
        {canManage && (
          <Button variant="secondary" onClick={() => setAdding(true)}>
            Registrar acta
          </Button>
        )}
      </div>
      {update.isError && <ErrorMessage>{messageFor(update.error)}</ErrorMessage>}
      {commitments.length === 0 ? (
        <p className="text-ink-soft">No hay actas registradas.</p>
      ) : (
        <ul className="divide-y divide-rule" aria-label="Actas con la familia">
          {commitments.map((commitment) => (
            <li key={commitment.id} className="py-3 first:pt-0 last:pb-0">
              <p className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-bold">{formatDate(commitment.meeting_date)}</span>
                <span className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${STATUS[commitment.status].className}`}>
                  {STATUS[commitment.status].label}
                </span>
              </p>
              <p className="mt-1 whitespace-pre-line">{commitment.agreements}</p>
              {commitment.follow_up_date && (
                <p className="mt-1 text-sm text-ink-soft">
                  Seguimiento: {formatDate(commitment.follow_up_date)}
                </p>
              )}
              {canManage && commitment.status === 'OPEN' && (
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    disabled={update.isPending}
                    onClick={() => update.mutate({ id: commitment.id, status: 'FULFILLED' })}
                  >
                    Marcar cumplido
                  </Button>
                  <Button
                    variant="ghost"
                    disabled={update.isPending}
                    onClick={() => update.mutate({ id: commitment.id, status: 'BREACHED' })}
                  >
                    Marcar no cumplido
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <Modal open={adding} onClose={() => setAdding(false)} title="Registrar acta" description={studentName}>
        {adding && (
          <NewCommitmentForm studentId={studentId} guardians={guardians} onDone={() => setAdding(false)} />
        )}
      </Modal>
    </section>
  )
}
