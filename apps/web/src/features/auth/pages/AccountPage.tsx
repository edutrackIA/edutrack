import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { TextField } from '../../../shared/ui/TextField'
import { useAuth } from '../auth-context'
import { isValidNewPassword, NewPasswordFields } from '../components/NewPasswordFields'
import { useChangePassword } from '../passwords'
import { ROLE_LABELS } from '../roles'
import { MyDataRequests } from '../../privacy/components/MyDataRequests'

export default function AccountPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const change = useChangePassword()
  const [current, setCurrent] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const valid = current.length > 0 && isValidNewPassword(password, confirmation)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    change.mutate(
      { current_password: current, new_password: password },
      {
        // Every session was closed on the server: sign in again with the new password.
        onSuccess: async () => {
          const email = user?.email
          await logout()
          navigate('/login', {
            replace: true,
            state: { email, notice: 'Tu contraseña se cambió. Entra con la nueva.' },
          })
        },
      },
    )
  }

  if (!user) return null

  return (
    <>
      <PageHeader title="Mi cuenta" description="Tus datos de acceso a EduTrack." />
      <div className="grid gap-10 lg:grid-cols-2">
        <section aria-labelledby="profile-title">
          <h2 id="profile-title" className="mb-4 font-figure text-xl font-semibold text-ink">
            Datos
          </h2>
          <dl className="divide-y divide-rule rounded-xl border border-rule bg-surface">
            {[
              ['Nombre', user.full_name],
              ['Correo', user.email],
              ['Rol', ROLE_LABELS[user.role]],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between gap-4 px-4 py-3">
                <dt className="text-ink-soft">{label}</dt>
                <dd className="text-right font-bold text-ink">{value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 text-sm text-ink-soft">
            Para corregir tu nombre o correo, comunícate con la dirección del colegio.
          </p>
        </section>

        <section aria-labelledby="password-title">
          <h2 id="password-title" className="mb-4 font-figure text-xl font-semibold text-ink">
            Cambiar contraseña
          </h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
            <TextField
              label="Contraseña actual"
              type="password"
              autoComplete="current-password"
              value={current}
              onChange={(event) => setCurrent(event.target.value)}
            />
            <NewPasswordFields
              label="Nueva contraseña"
              password={password}
              confirmation={confirmation}
              onPassword={setPassword}
              onConfirmation={setConfirmation}
            />
            <p className="text-sm text-ink-soft">
              Al cambiarla se cerrarán tus sesiones en todos los dispositivos.
            </p>
            {change.isError && <ErrorMessage>{messageFor(change.error)}</ErrorMessage>}
            <div>
              <Button type="submit" pending={change.isPending} disabled={!valid}>
                Cambiar contraseña
              </Button>
            </div>
          </form>
        </section>
      </div>
      {user.role === 'PARENT' && <MyDataRequests />}
    </>
  )
}
