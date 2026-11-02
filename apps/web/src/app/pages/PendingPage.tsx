import { EmptyState } from '../../shared/ui/Feedback'
import { PageHeader } from '../../shared/ui/PageHeader'

interface PendingPageProps {
  title: string
  description: string
}

/** Placeholder for sections that arrive in the next frontend features. */
export function PendingPage({ title, description }: PendingPageProps) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <EmptyState
        title="Disponible muy pronto"
        description="Esta sección se habilitará en la próxima versión de EduTrack."
      />
    </>
  )
}
