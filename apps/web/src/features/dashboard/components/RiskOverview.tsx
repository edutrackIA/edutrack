import type { DashboardSummary } from '../types'

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
    <section aria-labelledby="overview-title" className="mb-6 shrink-0">
      <h2 id="overview-title" className="sr-only">
        Panorama del bimestre
      </h2>
      <p className="font-figure text-2xl font-semibold leading-snug text-ink lg:text-3xl">
        {headline(atRisk, summary.evaluated_students)}
      </p>
      <p className="mt-1 text-ink-soft">
        {periodLabel}.
        {pending > 0 &&
          ` ${pending} ${pending === 1 ? 'estudiante aún no tiene' : 'estudiantes aún no tienen'} evaluación.`}
      </p>
    </section>
  )
}
