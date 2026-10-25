import type { ReactNode } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate, formatPercent, formatScore } from '../../../shared/lib/format'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { Modal } from '../../../shared/ui/Modal'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import { usePeriods } from '../../periods/api'
import { useStudent, useStudentRecommendations, useStudentSummary } from '../api'
import { factorWeight, formatFactorValue, WEIGHT_LABELS, type FactorWeight } from '../factor-format'
import type { Recommendation, RiskAssessment, StudentReference } from '../types'

const PASSING_SCORE = 11

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-rule py-5 first:border-t-0 first:pt-0 last:pb-0">
      <h3 className="mb-3 font-figure text-lg font-semibold text-ink">{title}</h3>
      {children}
    </section>
  )
}

function WeightDots({ weight }: { weight: FactorWeight }) {
  return (
    <span aria-hidden="true" className="flex gap-1">
      {[1, 2, 3].map((dot) => (
        <span
          key={dot}
          className={`h-2 w-2 rounded-full ${dot <= weight ? 'bg-risk-high-mark' : 'bg-rule'}`}
        />
      ))}
    </span>
  )
}

function RiskSection({ risk, periodLabel }: { risk: RiskAssessment; periodLabel: string }) {
  const showFactors = risk.level !== 'LOW' && risk.top_factors.length > 0
  const strongest = Math.max(...risk.top_factors.map((factor) => factor.contribution), 0)

  return (
    <Section title="Riesgo">
      <p className="flex flex-wrap items-center gap-3">
        <RiskBadge level={risk.level} />
        <span className="font-bold tabular-nums">
          {formatPercent(risk.probability)} de probabilidad
        </span>
        <span className="text-ink-soft">{periodLabel}</span>
      </p>
      {showFactors ? (
        <>
          <p className="mt-5 flex items-baseline justify-between gap-3">
            <span className="font-bold">Por qué está en riesgo</span>
            <span className="text-sm text-ink-soft">Ordenados por influencia</span>
          </p>
          <ol className="mt-2" aria-label="Qué explica el riesgo">
            {risk.top_factors.map((factor) => {
              const weight = factorWeight(factor.contribution, strongest)
              return (
                <li
                  key={factor.feature}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-0.5 border-b border-rule py-2.5 last:border-b-0 sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_auto]"
                >
                  <span className="font-bold">{factor.label}</span>
                  <span className="text-ink-soft tabular-nums sm:text-ink">
                    {formatFactorValue(factor.feature, factor.value)}
                  </span>
                  <span className="col-span-2 flex items-center gap-2 text-sm text-ink-soft sm:col-span-1 sm:justify-end">
                    <WeightDots weight={weight} />
                    {WEIGHT_LABELS[weight]}
                  </span>
                </li>
              )
            })}
          </ol>
        </>
      ) : (
        <p className="mt-3 text-ink-soft">No hay factores de riesgo relevantes.</p>
      )}
    </Section>
  )
}

const RECOMMENDATION_STATUS: Record<Recommendation['status'], string> = {
  PENDING_REVIEW: 'Pendiente de revisión del tutor',
  APPROVED: 'Aprobada',
  DISCARDED: 'Descartada por el tutor',
}

function recommendationText(recommendation: Recommendation | undefined): string {
  if (!recommendation) return 'Sin recomendaciones'
  if (recommendation.status === 'APPROVED' && recommendation.sent_at) {
    return `Enviada a la familia el ${formatDate(recommendation.sent_at)}`
  }
  return RECOMMENDATION_STATUS[recommendation.status]
}

function QuickViewBody({ studentId, periodId }: { studentId: number; periodId: number | null }) {
  const student = useStudent(studentId)
  const summary = useStudentSummary(studentId, periodId)
  const recommendations = useStudentRecommendations(studentId)
  const periods = usePeriods()

  if (student.isPending || summary.isPending) return <LoadingState label="Cargando la ficha…" />
  if (student.isError) return <ErrorMessage>{messageFor(student.error)}</ErrorMessage>
  if (summary.isError) return <ErrorMessage>{messageFor(summary.error)}</ErrorMessage>

  const labelFor = (id: number | null) =>
    periods.data?.find((period) => period.id === id)?.label ?? 'Bimestre'
  const risk = student.data.latest_risk
  const data = summary.data
  const guardians = student.data.guardians.map((guardian) => guardian.full_name)

  return (
    <>
      {risk ? (
        <RiskSection risk={risk} periodLabel={labelFor(risk.period_id)} />
      ) : (
        <Section title="Riesgo">
          <p className="text-ink-soft">Aún no tiene evaluación de riesgo.</p>
        </Section>
      )}

      <Section title={labelFor(data.period_id)}>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-ink-soft">Promedio</dt>
            <dd className="font-figure text-3xl font-semibold tabular-nums">
              {data.average_score === null ? '—' : formatScore(data.average_score)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-ink-soft">Asistencia</dt>
            <dd className="font-figure text-3xl font-semibold tabular-nums">
              {data.attendance_rate === null ? '—' : formatPercent(data.attendance_rate)}
            </dd>
          </div>
        </dl>
        {data.grades.length > 0 && (
          <ul className="mt-4 grid gap-x-6 sm:grid-cols-2" aria-label="Notas del bimestre">
            {data.grades.map((grade) => {
              const failed = grade.score < PASSING_SCORE
              return (
                <li
                  key={grade.subject_id}
                  className="flex justify-between gap-3 border-b border-rule py-1.5"
                >
                  <span>{grade.subject}</span>
                  <span
                    className={`tabular-nums ${failed ? 'font-bold text-risk-high' : 'text-ink'}`}
                  >
                    {formatScore(grade.score)}
                    {failed && <span className="sr-only"> (desaprobado)</span>}
                  </span>
                </li>
              )
            })}
          </ul>
        )}
      </Section>

      <Section title="Familia y seguimiento">
        <dl className="flex flex-col gap-2">
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-ink-soft">Apoderado:</dt>
            <dd>{guardians.length > 0 ? guardians.join(', ') : 'Sin apoderado registrado'}</dd>
          </div>
          <div className="flex flex-wrap gap-x-2">
            <dt className="text-ink-soft">Recomendación:</dt>
            <dd>
              {recommendations.isError
                ? 'No disponible'
                : recommendationText(recommendations.data?.[0])}
            </dd>
          </div>
        </dl>
      </Section>
    </>
  )
}

export function StudentQuickView({
  student,
  periodId,
  onClose,
}: {
  student: StudentReference | null
  periodId: number | null
  onClose: () => void
}) {
  return (
    <Modal
      open={student !== null}
      onClose={onClose}
      title={student?.full_name ?? ''}
      description={student ? `${student.classroom}, código ${student.code}` : undefined}
    >
      {student && <QuickViewBody studentId={student.student_id} periodId={periodId} />}
    </Modal>
  )
}
