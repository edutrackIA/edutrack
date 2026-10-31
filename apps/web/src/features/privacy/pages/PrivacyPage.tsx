import { Link } from 'react-router-dom'
import { PublicShell } from '../../auth/components/PublicShell'
import { PrivacyNoticeText } from '../components/PrivacyNoticeText'

/** Public privacy notice, readable before signing in. */
export default function PrivacyPage() {
  return (
    <PublicShell wide>
      <h1 className="mb-6 font-figure text-3xl font-semibold text-ink">Aviso de privacidad</h1>
      <PrivacyNoticeText />
      <p className="mt-10">
        <Link to="/login" className="font-bold text-accent hover:underline">
          Ir a iniciar sesión
        </Link>
      </p>
    </PublicShell>
  )
}
