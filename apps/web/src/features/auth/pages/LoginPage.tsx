import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { TextField } from '../../../shared/ui/TextField'
import { ThemeToggle } from '../../../shared/ui/ThemeToggle'
import { useAuth } from '../auth-context'
import { roleHome } from '../roles'

export default function LoginPage() {
  const { status, user, sessionExpired, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // Pages that send people here (invitation, reset, password change) pass the email along.
  const state = location.state as { email?: string; notice?: string } | null
  const [email, setEmail] = useState(() => state?.email ?? '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated' && user) return <Navigate to={roleHome(user.role)} replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const loggedUser = await login(email.trim(), password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(isSafeRedirect(from) ? from : roleHome(loggedUser.role), { replace: true })
    } catch (err) {
      setError(messageFor(err))
      setSubmitting(false)
    }
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.15fr_1fr]">
      <section className="bg-ruled relative hidden flex-col justify-between overflow-hidden border-r border-rule px-14 py-12 lg:flex">
        <span aria-hidden="true" className="absolute inset-y-0 left-10 w-px bg-accent/30" />
        <p className="font-figure text-2xl font-semibold text-ink">EduTrack</p>
        <div className="max-w-lg">
          <p className="font-figure text-5xl font-semibold leading-[1.15] text-ink">
            Cada estudiante, a tiempo.
          </p>
          <p className="mt-6 text-lg leading-8 text-ink-soft">
            Notas, asistencia y contexto familiar en un solo registro, para acompañar a quien lo
            necesita antes de que se quede atrás.
          </p>
        </div>
        <p className="text-sm text-ink-soft">Seguimiento académico y alerta temprana</p>
      </section>

      <section className="relative flex items-center justify-center px-6 py-12">
        <div className="absolute right-6 top-6">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-sm">
          <p className="mb-10 font-figure text-2xl font-semibold text-ink lg:hidden">EduTrack</p>
          <h1 className="font-figure text-3xl font-semibold text-ink">Inicia sesión</h1>
          <p className="mt-2 text-ink-soft">Usa el correo que te asignó tu colegio.</p>

          <form className="mt-8 flex flex-col gap-5" onSubmit={handleSubmit} noValidate>
            {state?.notice && !error && (
              <p
                role="status"
                className="rounded-md border border-risk-low/30 bg-risk-low-bg px-4 py-3 text-risk-low"
              >
                {state.notice}
              </p>
            )}
            {sessionExpired && !state?.notice && !error && (
              <p
                role="status"
                className="rounded-md border border-risk-medium/30 bg-risk-medium-bg px-4 py-3 text-risk-medium"
              >
                Tu sesión expiró. Vuelve a iniciar sesión para continuar donde estabas.
              </p>
            )}
            {error && <ErrorMessage>{error}</ErrorMessage>}
            <TextField
              label="Correo"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <TextField
              label="Contraseña"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <Button type="submit" pending={submitting} className="mt-2 w-full">
              Ingresar
            </Button>
          </form>

          <p className="mt-8">
            <Link to="/recuperar" className="font-bold text-accent hover:underline">
              ¿Olvidaste tu contraseña?
            </Link>
          </p>
        </div>
      </section>
    </main>
  )
}

/** Only same-app paths: blocks "//host", "/\\host" and absolute URLs. */
function isSafeRedirect(path: string | undefined): path is string {
  return (
    typeof path === 'string' &&
    path.startsWith('/') &&
    path !== '/' &&
    !path.startsWith('//') &&
    !path.includes('\\')
  )
}
