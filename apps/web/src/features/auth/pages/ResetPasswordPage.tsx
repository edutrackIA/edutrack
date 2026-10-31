import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../../../shared/api/client'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { NewPasswordFields } from '../components/NewPasswordFields'
import { isValidNewPassword } from '../invitations'
import { PublicShell } from '../components/PublicShell'
import { useResetPassword, useResetTarget } from '../passwords'

function isExpiredLink(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 404 || error.status === 409)
}

export default function ResetPasswordPage() {
  const token = useParams().token ?? ''
  const target = useResetTarget(token)
  const reset = useResetPassword(token)
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const valid = isValidNewPassword(password, confirmation)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (valid) reset.mutate(password)
  }

  return (
    <PublicShell>
      {target.isPending && <LoadingState label="Revisando el enlace…" />}
      {target.isError && (
        <>
          <h1 className="font-figure text-3xl font-semibold text-ink">Enlace no válido</h1>
          <div className="mt-6">
            <ErrorMessage>
              {isExpiredLink(target.error)
                ? 'Este enlace ya no es válido: venció o ya se usó.'
                : messageFor(target.error)}
            </ErrorMessage>
          </div>
          <Link to="/recuperar" className="mt-6 inline-flex font-bold text-accent hover:underline">
            Pedir otro enlace
          </Link>
        </>
      )}
      {target.data && reset.isSuccess && (
        <>
          <h1 className="font-figure text-3xl font-semibold text-ink">Contraseña actualizada</h1>
          <p className="mt-3 text-ink-soft">
            Por seguridad cerramos todas tus sesiones abiertas. Entra con tu nueva contraseña.
          </p>
          <Link
            to="/login"
            state={{ email: target.data.email }}
            className="mt-8 inline-flex rounded-md bg-accent px-5 py-2.5 font-bold text-on-accent hover:bg-accent-strong"
          >
            Iniciar sesión
          </Link>
        </>
      )}
      {target.data && !reset.isSuccess && (
        <>
          <h1 className="font-figure text-3xl font-semibold text-ink">Nueva contraseña</h1>
          <p className="mt-2 text-ink-soft">Para {target.data.email}.</p>
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5" noValidate>
            <NewPasswordFields
              label="Nueva contraseña"
              password={password}
              confirmation={confirmation}
              onPassword={setPassword}
              onConfirmation={setConfirmation}
            />
            {reset.isError && <ErrorMessage>{messageFor(reset.error)}</ErrorMessage>}
            <Button type="submit" pending={reset.isPending} disabled={!valid}>
              Guardar contraseña
            </Button>
          </form>
        </>
      )}
    </PublicShell>
  )
}
