import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { ThemeToggle } from '../../../shared/ui/ThemeToggle'
import { NewPasswordFields } from '../components/NewPasswordFields'
import { isValidNewPassword, useAcceptInvitation, useInvitation } from '../invitations'

/** Public page where an invited guardian creates their password. */
export default function AcceptInvitationPage() {
  const token = useParams().token ?? ''
  const invitation = useInvitation(token)
  const accept = useAcceptInvitation(token)
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const valid = isValidNewPassword(password, confirmation)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (valid) accept.mutate(password)
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center px-6 py-12">
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-md">
        <p className="mb-10 font-figure text-2xl font-semibold text-ink">EduTrack</p>

        {invitation.isPending && <LoadingState label="Revisando el enlace…" />}

        {invitation.isError && (
          <>
            <h1 className="font-figure text-3xl font-semibold text-ink">Enlace no válido</h1>
            <div className="mt-6">
              <ErrorMessage>{messageFor(invitation.error)}</ErrorMessage>
            </div>
          </>
        )}

        {invitation.data && accept.isSuccess && (
          <>
            <h1 className="font-figure text-3xl font-semibold text-ink">Tu contraseña está lista</h1>
            <p className="mt-3 text-ink-soft">
              Ya puedes entrar con {invitation.data.email} y la contraseña que acabas de crear.
            </p>
            <Link
              to="/login"
              state={{ email: invitation.data.email }}
              className="mt-8 inline-flex rounded-md bg-accent px-5 py-2.5 font-bold text-on-accent hover:bg-accent-strong"
            >
              Iniciar sesión
            </Link>
          </>
        )}

        {invitation.data && !accept.isSuccess && (
          <>
            <h1 className="font-figure text-3xl font-semibold text-ink">
              Hola, {invitation.data.full_name.split(' ')[0]}
            </h1>
            <p className="mt-2 text-ink-soft">
              Crea tu contraseña para entrar a EduTrack con {invitation.data.email}.
            </p>
            <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5" noValidate>
              <NewPasswordFields
                password={password}
                confirmation={confirmation}
                onPassword={setPassword}
                onConfirmation={setConfirmation}
              />
              {accept.isError && <ErrorMessage>{messageFor(accept.error)}</ErrorMessage>}
              <Button type="submit" pending={accept.isPending} disabled={!valid}>
                Crear contraseña
              </Button>
            </form>
          </>
        )}
      </div>
    </main>
  )
}
