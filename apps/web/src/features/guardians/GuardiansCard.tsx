import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../shared/api/errors'
import { Button } from '../../shared/ui/Button'
import { ErrorMessage } from '../../shared/ui/Feedback'
import { Modal } from '../../shared/ui/Modal'
import { TextField } from '../../shared/ui/TextField'
import {
  useAddGuardian,
  useGuardians,
  useResendInvitation,
  useUnlinkGuardian,
  type Guardian,
} from './api'

const KINSHIPS = ['Madre', 'Padre', 'Tutor legal', 'Abuela', 'Abuelo', 'Tía', 'Tío', 'Otro']

interface Notice {
  text: string
  tone: 'success' | 'warning'
}

function invitationNotice(guardian: Guardian): Notice {
  if (guardian.has_access) {
    return { tone: 'success', text: `${guardian.full_name} ya tenía acceso y quedó vinculado.` }
  }
  return guardian.invitation_sent
    ? { tone: 'success', text: `Invitación enviada a ${guardian.email}.` }
    : {
        tone: 'warning',
        text: `No se pudo enviar la invitación a ${guardian.email}. Puedes reenviarla más tarde.`,
      }
}

function AddGuardianForm({
  studentId,
  onDone,
}: {
  studentId: number
  onDone: (notice: Notice) => void
}) {
  const add = useAddGuardian(studentId)
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [kinship, setKinship] = useState(KINSHIPS[0])
  const kinshipId = useId()

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    add.mutate(
      { full_name: fullName.trim(), email: email.trim(), kinship },
      { onSuccess: (guardian) => onDone(invitationNotice(guardian)) },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <TextField
        label="Nombre completo"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        required
      />
      <TextField
        label="Correo"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        hint="Si es nuevo, le enviaremos un enlace para que cree su contraseña."
        required
      />
      <div className="flex flex-col gap-1.5">
        <label htmlFor={kinshipId} className="font-bold text-ink">
          Parentesco
        </label>
        <select
          id={kinshipId}
          value={kinship}
          onChange={(event) => setKinship(event.target.value)}
          className="w-fit rounded-md border border-rule bg-surface px-3 py-2 text-ink"
        >
          {KINSHIPS.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      </div>
      {add.isError && <ErrorMessage>{messageFor(add.error)}</ErrorMessage>}
      <div>
        <Button type="submit" pending={add.isPending} disabled={!fullName.trim() || !email.trim()}>
          Registrar apoderado
        </Button>
      </div>
    </form>
  )
}

function GuardianRow({
  studentId,
  guardian,
  onNotice,
}: {
  studentId: number
  guardian: Guardian
  onNotice: (notice: Notice) => void
}) {
  const resend = useResendInvitation(studentId)
  const unlink = useUnlinkGuardian(studentId)
  const [confirming, setConfirming] = useState(false)
  const error = resend.error ?? unlink.error

  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <p className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-bold text-ink">
          {guardian.full_name}
          <span className="ml-2 font-normal text-ink-soft">{guardian.kinship}</span>
        </span>
        <span
          className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${
            guardian.has_access
              ? 'bg-risk-low-bg text-risk-low'
              : 'bg-risk-medium-bg text-risk-medium'
          }`}
        >
          {guardian.has_access ? 'Acceso activo' : 'Invitación pendiente'}
        </span>
      </p>
      <p className="text-sm text-ink-soft">{guardian.email}</p>
      {error && (
        <div className="mt-2">
          <ErrorMessage>{messageFor(error)}</ErrorMessage>
        </div>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {!guardian.has_access && (
          <Button
            variant="ghost"
            pending={resend.isPending}
            onClick={() =>
              resend.mutate(guardian.id, { onSuccess: (result) => onNotice(invitationNotice(result)) })
            }
          >
            Reenviar invitación<span className="sr-only"> a {guardian.full_name}</span>
          </Button>
        )}
        {confirming ? (
          <>
            <span className="text-sm text-ink">¿Desvincular? Dejará de ver a este estudiante.</span>
            <Button
              variant="secondary"
              pending={unlink.isPending}
              onClick={() =>
                unlink.mutate(guardian.id, {
                  onSuccess: () =>
                    onNotice({ tone: 'success', text: `${guardian.full_name} fue desvinculado.` }),
                })
              }
            >
              Sí, desvincular
            </Button>
            <Button variant="ghost" onClick={() => setConfirming(false)}>
              Cancelar
            </Button>
          </>
        ) : (
          <Button variant="ghost" onClick={() => setConfirming(true)}>
            Desvincular<span className="sr-only"> a {guardian.full_name}</span>
          </Button>
        )}
      </div>
    </li>
  )
}

/** Guardians of a student, managed by direction and data analysis. */
export function GuardiansCard({ studentId, studentName }: { studentId: number; studentName: string }) {
  const guardians = useGuardians(studentId, true)
  const [adding, setAdding] = useState(false)
  const [notice, setNotice] = useState<Notice | null>(null)

  return (
    <section className="rounded-xl border border-rule bg-surface p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-figure text-xl font-semibold text-ink">Apoderados</h2>
        <Button variant="secondary" onClick={() => setAdding(true)}>
          Agregar apoderado
        </Button>
      </div>
      <div role="status" aria-live="polite">
        {notice && (
          <p
            className={`mb-4 rounded-md px-3 py-2 ${
              notice.tone === 'success'
                ? 'bg-risk-low-bg text-risk-low'
                : 'bg-risk-medium-bg text-risk-medium'
            }`}
          >
            {notice.text}
          </p>
        )}
      </div>
      {guardians.isError && <ErrorMessage>{messageFor(guardians.error)}</ErrorMessage>}
      {guardians.data?.length === 0 && (
        <p className="text-ink-soft">
          Sin apoderados registrados: la familia no recibirá correos ni podrá entrar al portal.
        </p>
      )}
      {guardians.data && guardians.data.length > 0 && (
        <ul className="divide-y divide-rule" aria-label="Apoderados del estudiante">
          {guardians.data.map((guardian) => (
            <GuardianRow
              key={guardian.id}
              studentId={studentId}
              guardian={guardian}
              onNotice={setNotice}
            />
          ))}
        </ul>
      )}

      <Modal
        open={adding}
        onClose={() => setAdding(false)}
        title="Agregar apoderado"
        description={studentName}
      >
        {adding && (
          <AddGuardianForm
            studentId={studentId}
            onDone={(result) => {
              setNotice(result)
              setAdding(false)
            }}
          />
        )}
      </Modal>
    </section>
  )
}
