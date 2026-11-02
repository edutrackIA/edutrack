import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { usePendingFamilyReports, useReviewFamilyReport, type FamilyCheckin } from '../api'

function Report({ report }: { report: FamilyCheckin }) {
  const review = useReviewFamilyReport()
  return (
    <li
      className={`rounded-lg border p-4 ${
        report.peer_concern ? 'border-risk-high/50 bg-risk-high-bg' : 'border-rule bg-surface'
      }`}
    >
      <p className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-bold text-ink">{report.student.full_name}</span>
        <span className="text-sm text-ink-soft">Enviado el {formatDate(report.submitted_at)}</span>
      </p>
      {report.peer_concern && (
        <p className="mt-2 font-bold text-risk-high">
          La familia indica que le preocupa cómo lo tratan sus compañeros.
        </p>
      )}
      <p className="mt-2 text-ink">Cómo lo ven: {report.mood_label}.</p>
      {report.home_change_labels.length > 0 && (
        <p className="mt-1 text-ink">Cambios en casa: {report.home_change_labels.join(', ')}.</p>
      )}
      {report.comment && <p className="mt-1 italic text-ink">“{report.comment}”</p>}
      {review.isError && (
        <div className="mt-3">
          <ErrorMessage>{messageFor(review.error)}</ErrorMessage>
        </div>
      )}
      <div className="mt-3">
        <Button variant="secondary" pending={review.isPending} onClick={() => review.mutate(report.id)}>
          Marcar como revisado
          <span className="sr-only"> el reporte de {report.student.full_name}</span>
        </Button>
      </div>
    </li>
  )
}

/** Monthly family reports that need the tutor's attention. */
export function FamilyReports() {
  const reports = usePendingFamilyReports()
  if (!reports.data || reports.data.length === 0) return null

  return (
    <section aria-labelledby="family-reports-title" className="shrink-0">
      <h2 id="family-reports-title" className="font-figure text-lg font-semibold text-ink">
        Reportes de las familias ({reports.data.length})
      </h2>
      <p className="mt-1 text-sm text-ink-soft">
        Si corresponde, marca la situación del estudiante en la tabla de abajo.
      </p>
      <ul className="mt-3 grid gap-3 lg:grid-cols-2">
        {reports.data.map((report) => (
          <Report key={report.id} report={report} />
        ))}
      </ul>
    </section>
  )
}
