import { TextField } from '../../../shared/ui/TextField'
import { passwordChecks } from '../invitations'

/** New password twice, with the rules checked live. Used to accept invitations,
 * reset a forgotten password and change it from the account page. */
export function NewPasswordFields({
  password,
  confirmation,
  onPassword,
  onConfirmation,
  label = 'Contraseña',
}: {
  password: string
  confirmation: string
  onPassword: (value: string) => void
  onConfirmation: (value: string) => void
  label?: string
}) {
  const checks = passwordChecks(password, confirmation)
  return (
    <>
      <TextField
        label={label}
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(event) => onPassword(event.target.value)}
      />
      <TextField
        label="Repite la contraseña"
        type="password"
        autoComplete="new-password"
        value={confirmation}
        onChange={(event) => onConfirmation(event.target.value)}
      />
      <ul aria-label="Requisitos de la contraseña" className="flex flex-col gap-1 text-sm">
        {checks.map((check) => (
          <li key={check.label} className={check.ok ? 'text-risk-low' : 'text-ink-soft'}>
            <span aria-hidden="true">{check.ok ? '✓' : '○'}</span> {check.label}
            <span className="sr-only">{check.ok ? ': cumplido' : ': pendiente'}</span>
          </li>
        ))}
      </ul>
    </>
  )
}
