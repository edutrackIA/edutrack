import { useState, type ReactNode } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate, formatPercent, formatScore } from '../../../shared/lib/format'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { usePeriods, type Period } from '../../periods/api'
import { useStudentCommitments, useStudentSummary, useStudentSurveys } from '../../students/api'
import { firstName, useChildren, useCurrentCheckin } from '../api'
import { FamilySurveyForm } from '../components/FamilySurveyForm'
import { MonthlyCheckinForm } from '../components/MonthlyCheckinForm'

const PASSING_SCORE = 11

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-rule bg-surface p-5">
      <h2 className="mb-4 font-figure text-xl font-semibold text-ink">{title}</h2>
      {children}
    </section>
  )
}

function currentPeriod(periods: Period[] | undefined): Period | undefined {
  const today = new Date()
  const value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(
    today.getDate(),
  ).padStart(2, '0')}`
  return periods?.find((period) => period.start_date <= value && value <= period.end_date)
}

function ChildPortal({ studentId, fullName }: { studentId: number; fullName: string }) {
  const name = firstName(fullName)
  const summary = useStudentSummary(studentId, null)
  const checkin = useCurrentCheckin(studentId)
  const surveys = useStudentSurveys(studentId)
  const commitments = useStudentCommitments(studentId)
  const periods = usePeriods()
  const period = currentPeriod(periods.data)
  const answeredSurvey = surveys.data?.some((survey) => survey.period_id === period?.id)

  if (summary.isPending) return <LoadingState label="Cargando el avance…" />
  if (summary.isError) return <ErrorMessage>{messageFor(summary.error)}</ErrorMessage>
  const data = summary.data
  const periodLabel = periods.data?.find((item) => item.id === data.period_id)?.label

  return (
    <div className="grid items-start gap-6 lg:grid-cols-2">
      <div className="flex flex-col gap-6">
        <Card title={periodLabel ? `Avance, ${periodLabel}` : 'Avance'}>
          {data.period_id === null ? (
            <p className="text-ink-soft">Aún no hay notas registradas.</p>
          ) : (
            <>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-ink-soft">Promedio</dt>
                  <dd className="font-figure text-4xl font-semibold tabular-nums">
                    {data.average_score === null ? '—' : formatScore(data.average_score)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-ink-soft">Asistencia</dt>
                  <dd className="font-figure text-4xl font-semibold tabular-nums">
                    {data.attendance_rate === null ? '—' : formatPercent(data.attendance_rate)}
                  </dd>
                </div>
              </dl>
              <ul className="mt-4" aria-label="Notas del bimestre">
                {data.grades.map((grade) => {
                  const failed = grade.score < PASSING_SCORE
                  return (
                    <li
                      key={grade.subject_id}
                      className="flex justify-between gap-3 border-b border-rule py-1.5 last:border-b-0"
                    >
                      <span>{grade.subject}</span>
                      <span className={`tabular-nums ${failed ? 'font-bold text-risk-high' : ''}`}>
                        {formatScore(grade.score)}
                        {failed && <span className="sr-only"> (desaprobado)</span>}
                      </span>
                    </li>
                  )
                })}
              </ul>
            </>
          )}
        </Card>

        <Card title="Sugerencias del tutor">
          {data.parent_suggestions.length === 0 ? (
            <p className="text-ink-soft">Aún no hay sugerencias para este bimestre.</p>
          ) : (
            <>
              <ol className="list-decimal space-y-3 pl-5">
                {data.parent_suggestions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
              {data.disclaimer && (
                <p className="mt-4 border-t border-rule pt-3 text-sm text-ink-soft">
                  {data.disclaimer}
                </p>
              )}
            </>
          )}
        </Card>

        {commitments.data && commitments.data.length > 0 && (
          <Card title="Acuerdos con el tutor">
            <ul className="divide-y divide-rule">
              {commitments.data.map((commitment) => (
                <li key={commitment.id} className="py-3 first:pt-0 last:pb-0">
                  <p className="font-bold">{formatDate(commitment.meeting_date)}</p>
                  <p className="mt-1">{commitment.agreements}</p>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      <div className="flex flex-col gap-6">
        <Card title="Seguimiento del mes">
          {checkin.data ? (
            <MonthlyCheckinForm
              key={checkin.data.checkin?.id ?? 'new'}
              studentId={studentId}
              name={name}
              month={checkin.data.month}
              current={checkin.data.checkin}
            />
          ) : (
            <LoadingState />
          )}
        </Card>

        {period && surveys.data && (
          <Card title="Encuesta familiar del bimestre">
            {answeredSurvey ? (
              <p className="text-ink-soft">Gracias, ya respondió la encuesta de este bimestre.</p>
            ) : (
              <>
                <p className="mb-4 text-sm text-ink-soft">
                  Nos ayuda a entender el contexto de {name} para acompañarle mejor. Solo la ven la
                  dirección y el área de análisis.
                </p>
                <FamilySurveyForm studentId={studentId} periodId={period.id} />
              </>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}

export default function ParentPortalPage() {
  const children = useChildren()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const list = children.data ?? []
  const selected = list.find((child) => child.id === selectedId) ?? list[0]

  return (
    <>
      <PageHeader
        title={selected ? `Avance de ${firstName(selected.full_name)}` : 'Mi hijo'}
        description={selected ? `${selected.classroom}, código ${selected.code}` : undefined}
        actions={
          list.length > 1 && (
            <select
              aria-label="Hijo o hija"
              value={selected?.id}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="rounded-md border border-rule bg-surface px-3 py-2 text-ink"
            >
              {list.map((child) => (
                <option key={child.id} value={child.id}>
                  {firstName(child.full_name)}
                </option>
              ))}
            </select>
          )
        }
      />
      {children.isPending && <LoadingState />}
      {children.isError && <ErrorMessage>{messageFor(children.error)}</ErrorMessage>}
      {children.data && !selected && (
        <EmptyState
          title="Aún no hay estudiantes vinculados a su cuenta"
          description="Comuníquese con el colegio para que vinculen a su hijo o hija."
        />
      )}
      {selected && <ChildPortal key={selected.id} studentId={selected.id} fullName={selected.full_name} />}
    </>
  )
}
