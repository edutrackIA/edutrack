import { useState, type ReactNode } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { useAuth } from '../../auth/auth-context'
import { useAcceptPrivacy, usePrivacyStatus } from '../api'
import { PrivacyNoticeText } from './PrivacyNoticeText'

/**
 * Guardians must accept the current privacy notice before using the portal: the law
 * requires their consent to process their children's data.
 */
export function ConsentGate({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const isParent = user?.role === 'PARENT'
  const status = usePrivacyStatus(isParent)
  const accept = useAcceptPrivacy()
  const [checked, setChecked] = useState(false)

  if (!isParent) return <>{children}</>
  if (status.isPending) return <LoadingState />
  if (status.isError) return <ErrorMessage>{messageFor(status.error)}</ErrorMessage>
  if (status.data.accepted_at) return <>{children}</>

  return (
    <section aria-labelledby="consent-title" className="mx-auto max-w-2xl">
      <h1 id="consent-title" className="font-figure text-3xl font-semibold text-ink">
        Antes de empezar
      </h1>
      <p className="mt-2 text-ink-soft">
        Lee cómo el colegio usa los datos de tu familia. Necesitamos tu consentimiento para
        mostrarte el avance de tu hijo o hija.
      </p>
      <div className="mt-6 max-h-[50vh] overflow-y-auto rounded-xl border border-rule bg-surface p-5">
        <PrivacyNoticeText />
      </div>
      <label className="mt-6 flex items-start gap-2">
        <input
          type="checkbox"
          checked={checked}
          onChange={(event) => setChecked(event.target.checked)}
          className="mt-1 accent-accent"
        />
        <span>
          Leí el aviso de privacidad y autorizo el tratamiento de los datos de mi hijo o hija y
          los míos para los fines descritos.
        </span>
      </label>
      {accept.isError && (
        <div className="mt-4">
          <ErrorMessage>{messageFor(accept.error)}</ErrorMessage>
        </div>
      )}
      <div className="mt-6 flex flex-wrap gap-3">
        <Button
          pending={accept.isPending}
          disabled={!checked}
          onClick={() => accept.mutate(status.data.version)}
        >
          Acepto
        </Button>
        <Button variant="ghost" onClick={() => void logout()}>
          No acepto, salir
        </Button>
      </div>
      <p className="mt-4 text-sm text-ink-soft">
        Si no aceptas, no podrás usar el portal. Puedes comunicarte con la dirección del colegio
        para resolver tus dudas.
      </p>
    </section>
  )
}
