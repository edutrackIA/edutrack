import { Link } from 'react-router-dom'
import { EmptyState } from '../../shared/ui/Feedback'

export function NotFoundPage() {
  return (
    <EmptyState
      title="No encontramos esta página"
      description="Puede que el enlace esté incompleto o que la página ya no exista."
      action={
        <Link to="/" className="font-bold text-accent underline underline-offset-4">
          Ir al inicio
        </Link>
      }
    />
  )
}
