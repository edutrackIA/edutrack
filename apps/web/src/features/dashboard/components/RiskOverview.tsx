import type { RiskLevel } from '../../../shared/lib/risk'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import type { DashboardSummary } from '../types'

const LEVEL_ORDER: RiskLevel[] = ['HIGH', 'MEDIUM', 'LOW']

function headline(atRisk: number, evaluated: number): string {
  if (atRisk === 0) return 'Ningún estudiante evaluado está en riesgo este bimestre.'
  const verb = atRisk === 1 ? 'necesita' : 'necesitan'
  return `${atRisk} de ${evaluated} estudiantes ${verb} acompañamiento este bimestre.`
}

export function RiskOverview({
  summary,
  periodLabel,
}: {
  summary: DashboardSummary
  periodLabel: string
}) {
  const atRisk = summary.by_level.HIGH + summary.by_level.MEDIUM
  const pending = summary.total_students - summary.evaluated_students

  return (
    <section aria-labelledby="overview-title" className="mb-12">
      <h2 id="overview-title" className="sr-only">
        Panorama del bimestre
      </h2>
      <p className="max-w-3xl font-figure text-3xl font-semibold leading-snug text-ink sm:text-4xl">
        {headline(atRisk, summary.evaluated_students)}
      </p>
      <p className="mt-3 text-ink-soft">
        {periodLabel}.
        {pending > 0 &&
          ` ${pending} ${pending === 1 ? 'estudiante aún no tiene' : 'estudiantes aún no tienen'} evaluación.`}
      </p>
      <ul className="mt-6 flex flex-wrap gap-x-6 gap-y-3" aria-label="Estudiantes por nivel">
        {LEVEL_ORDER.map((level) => (
          <li key={level} className="flex items-center gap-2">
            <RiskBadge level={level} />
            <span className="text-lg font-bold tabular-nums text-ink">{summary.by_level[level]}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
