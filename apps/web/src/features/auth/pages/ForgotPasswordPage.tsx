import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { TextField } from '../../../shared/ui/TextField'
import { PublicShell } from '../components/PublicShell'
import { useForgotPassword } from '../passwords'

export default function ForgotPasswordPage() {
  const forgot = useForgotPassword()
  const [email, setEmail] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    forgot.mutate(email.trim())
  }

  return (
    <PublicShell>
      <h1 className="font-figure text-3xl font-semibold text-ink">Recupera tu acceso</h1>
      {forgot.isSuccess ? (
        <div role="status" className="mt-6 flex flex-col gap-4">
          <p className="text-ink">
            Si {email.trim()} está registrado, te enviamos un enlace para crear una nueva
            contraseña. Vence en una hora.
          </p>
          <p className="text-sm text-ink-soft">Revisa también la carpeta de spam.</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5" noValidate>
          <p className="text-ink-soft">
            Escribe el correo con el que entras a EduTrack y te enviaremos un enlace.
          </p>
          <TextField
            label="Correo"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          {forgot.isError && <ErrorMessage>{messageFor(forgot.error)}</ErrorMessage>}
          <Button type="submit" pending={forgot.isPending} disabled={!email.includes('@')}>
            Enviar enlace
          </Button>
        </form>
      )}
      <p className="mt-8">
        <Link to="/login" className="font-bold text-accent hover:underline">
          Volver a iniciar sesión
        </Link>
      </p>
    </PublicShell>
  )
}
