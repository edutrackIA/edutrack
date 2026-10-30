import { useId, useState, type FormEvent } from 'react'
import { Button } from '../../../shared/ui/Button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { useAuth } from '../../auth/auth-context'
import {
  STAFF_ROLE_LABELS,
  useInviteStaff,
  useResendStaffInvitation,
  useSetStaffActive,
  useStaff,
  type StaffMember,
  type StaffRole,
} from '../api'
import { Field, inputClass, MutationError, SetupSection } from './SetupParts'

function status(member: StaffMember): { label: string; className: string } {
  if (!member.is_active) return { label: 'Desactivado', className: 'bg-paper text-ink-soft' }
  if (!member.has_access) {
    return { label: 'Invitación pendiente', className: 'bg-risk-medium-bg text-risk-medium' }
  }
  return { label: 'Activo', className: 'bg-risk-low-bg text-risk-low' }
}

function StaffRow({ member, isMe }: { member: StaffMember; isMe: boolean }) {
  const resend = useResendStaffInvitation()
  const setActive = useSetStaffActive()
  const badge = status(member)

  return (
    <TableRow>
      <TableCell>
        <span className="font-bold">{member.full_name}</span>
        <span className="block text-sm text-ink-soft">{member.email}</span>
      </TableCell>
      <TableCell>{STAFF_ROLE_LABELS[member.role]}</TableCell>
      <TableCell>
        <span className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${badge.className}`}>
          {badge.label}
        </span>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex flex-wrap justify-end gap-2">
          {member.is_active && !member.has_access && (
            <Button variant="ghost" pending={resend.isPending} onClick={() => resend.mutate(member.id)}>
              Reenviar invitación<span className="sr-only"> a {member.full_name}</span>
            </Button>
          )}
          {!isMe && (
            <Button
              variant="ghost"
              pending={setActive.isPending}
              onClick={() => setActive.mutate({ id: member.id, is_active: !member.is_active })}
            >
              {member.is_active ? 'Desactivar' : 'Reactivar'}
              <span className="sr-only"> a {member.full_name}</span>
            </Button>
          )}
        </div>
        <MutationError error={resend.error ?? setActive.error} />
      </TableCell>
    </TableRow>
  )
}

export function StaffSection() {
  const { user } = useAuth()
  const staff = useStaff()
  const invite = useInviteStaff()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<StaffRole>('TEACHER')
  const [notice, setNotice] = useState<string | null>(null)
  const ids = { name: useId(), email: useId(), role: useId() }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setNotice(null)
    invite.mutate(
      { full_name: fullName.trim(), email: email.trim(), role },
      {
        onSuccess: (member) => {
          setFullName('')
          setEmail('')
          setNotice(
            member.invitation_sent
              ? `Invitación enviada a ${member.email}.`
              : `Se registró a ${member.full_name}, pero el correo no se pudo enviar. Reenvía la invitación más tarde.`,
          )
        },
      },
    )
  }

  return (
    <SetupSection
      title="Personal"
      description="Cada persona recibe un correo para crear su contraseña. Desactivar una cuenta bloquea su acceso de inmediato."
      form={
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <Field label="Nombre completo" htmlFor={ids.name}>
            <input id={ids.name} value={fullName} onChange={(event) => setFullName(event.target.value)} className={`${inputClass} w-64`} />
          </Field>
          <Field label="Correo" htmlFor={ids.email}>
            <input id={ids.email} type="email" value={email} onChange={(event) => setEmail(event.target.value)} className={`${inputClass} w-72`} />
          </Field>
          <Field label="Rol" htmlFor={ids.role}>
            <select
              id={ids.role}
              value={role}
              onChange={(event) => setRole(event.target.value as StaffRole)}
              className={inputClass}
            >
              {(Object.keys(STAFF_ROLE_LABELS) as StaffRole[]).map((value) => (
                <option key={value} value={value}>
                  {STAFF_ROLE_LABELS[value]}
                </option>
              ))}
            </select>
          </Field>
          <Button
            type="submit"
            pending={invite.isPending}
            disabled={fullName.trim().length < 3 || !email.trim()}
          >
            Invitar
          </Button>
          <div className="basis-full" role="status" aria-live="polite">
            {notice && <p className="text-risk-low">{notice}</p>}
            <MutationError error={invite.error} />
          </div>
        </form>
      }
    >
      {staff.data && (
        <Table caption="Personal del colegio">
          <TableHead>
            <tr>
              <TableHeaderCell>Persona</TableHeaderCell>
              <TableHeaderCell>Rol</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell>
                <span className="sr-only">Acciones</span>
              </TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {staff.data.map((member) => (
              <StaffRow key={member.id} member={member} isMe={member.id === user?.id} />
            ))}
          </TableBody>
        </Table>
      )}
    </SetupSection>
  )
}
