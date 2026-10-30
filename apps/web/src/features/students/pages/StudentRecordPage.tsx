import type { ReactNode } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiError } from '../../../shared/api/client'
import { messageFor } from '../../../shared/api/errors'
import { formatDate, formatPercent, formatScore } from '../../../shared/lib/format'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import { useAuth } from '../../auth/auth-context'
import { classroomLabel, useClassrooms } from '../../classrooms/api'
import { GuardiansCard } from '../../guardians/GuardiansCard'
import { usePeriods, type Period } from '../../periods/api'
import { useStudentSituations, type Situation } from '../../situations/api'
import { SituationChip } from '../../situations/components/SituationChip'
import {
  useStudent,
  useStudentCommitments,
  useStudentGrades,
  useStudentRecommendations,
  useStudentRiskHistory,
  useStudentSummary,
  useStudentSurveys,
} from '../api'
import { formatFactorValue } from '../factor-format'
import { RiskFactors } from '../components/RiskFactors'
import { backLink } from '../navigation'
import type { Commitment, FamilySurvey, Grade, Recommendation, RiskAssessment } from '../types'

const PASSING_SCORE = 11

function isForbidden(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-rule bg-surface p-5">
      <h2 className="mb-4 font-figure text-xl font-semibold text-ink">{title}</h2>
      {children}
    </section>
  )
}

function periodName(periods: Period[] | undefined, id: number): string {
  return periods?.find((period) => period.id === id)?.label ?? `Periodo ${id}`
}

function RiskCard({ history, periods }: { history: RiskAssessment[]; periods?: Period[] }) {
  const latest = history[0]
  if (!latest) {
    return (
      <Card title="Riesgo">
        <p className="text-ink-soft">Aún no tiene evaluación de riesgo.</p>
      </Card>
    )
  }
  return (
    <Card title="Riesgo">
      <p className="flex flex-wrap items-center gap-3">
        <RiskBadge level={latest.level} />
        <span className="font-bold tabular-nums">
          {formatPercent(latest.probability)} de probabilidad
        </span>
        <span className="text-ink-soft">{periodName(periods, latest.period_id)}</span>
      </p>
      {latest.level !== 'LOW' && latest.top_factors.length > 0 ? (
        <div className="mt-5">
          <RiskFactors factors={latest.top_factors} />
        </div>
      ) : (
        <p className="mt-3 text-ink-soft">No hay factores de riesgo relevantes.</p>
      )}
      {history.length > 1 && (
        <>
          <p className="mt-6 font-bold">Evaluaciones anteriores</p>
          <ul className="mt-2" aria-label="Evaluaciones anteriores">
            {history.slice(1).map((assessment) => (
              <li
                key={assessment.id}
                className="flex items-center justify-between gap-3 border-b border-rule py-2 last:border-b-0"
              >
                <span>{periodName(periods, assessment.period_id)}</span>
                <span className="flex items-center gap-3">
                  <RiskBadge level={assessment.level} />
                  <span className="tabular-nums text-ink-soft">
                    {formatPercent(assessment.probability)}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  )
}

function GradesCard({ grades, periods }: { grades: Grade[]; periods?: Period[] }) {
  if (grades.length === 0) {
    return (
      <Card title="Notas">
        <p className="text-ink-soft">Aún no tiene notas registradas.</p>
      </Card>
    )
  }
  const periodIds = [...new Set(grades.map((grade) => grade.period_id))].sort((a, b) => a - b)
  const subjects = [...new Set(grades.map((grade) => grade.subject))].sort((a, b) =>
    a.localeCompare(b),
  )
  const scoreOf = (subject: string, periodId: number) =>
    grades.find((grade) => grade.subject === subject && grade.period_id === periodId)?.score

  return (
    <Card title="Notas">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <caption className="sr-only">Notas por curso y bimestre</caption>
          <thead className="border-b-2 border-ink text-sm text-ink-soft">
            <tr>
              <th scope="col" className="py-2 pr-4 font-bold">
                Curso
              </th>
              {periodIds.map((id) => (
                <th key={id} scope="col" className="px-2 py-2 text-right font-bold">
                  {periodName(periods, id).replace(', ', ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {subjects.map((subject) => (
              <tr key={subject}>
                <th scope="row" className="py-2 pr-4 text-left font-normal">
                  {subject}
                </th>
                {periodIds.map((id) => {
                  const score = scoreOf(subject, id)
                  const failed = score !== undefined && score < PASSING_SCORE
                  return (
                    <td
                      key={id}
                      className={`px-2 py-2 text-right tabular-nums ${
                        failed ? 'font-bold text-risk-high' : ''
                      }`}
                    >
                      {score === undefined ? '—' : formatScore(score)}
                      {failed && <span className="sr-only"> (desaprobado)</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

const RECOMMENDATION_STATUS: Record<Recommendation['status'], string> = {
  PENDING_REVIEW: 'Pendiente de revisión del tutor',
  APPROVED: 'Aprobada',
  DISCARDED: 'Descartada por el tutor',
}

function RecommendationCard({ recommendation }: { recommendation?: Recommendation }) {
  if (!recommendation) {
    return (
      <Card title="Recomendaciones">
        <p className="text-ink-soft">Aún no tiene recomendaciones.</p>
      </Card>
    )
  }
  const status =
    recommendation.status === 'APPROVED' && recommendation.sent_at
      ? `Enviada a la familia el ${formatDate(recommendation.sent_at)}`
      : RECOMMENDATION_STATUS[recommendation.status]
  return (
    <Card title="Recomendaciones">
      <p className="text-ink-soft">{status}</p>
      <p className="mt-4 font-bold">Para la familia</p>
      <ul className="mt-2 list-disc space-y-2 pl-5">
        {recommendation.parent_items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p className="mt-4 font-bold">Acciones para el tutor</p>
      <ul className="mt-2 list-disc space-y-2 pl-5">
        {recommendation.teacher_items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </Card>
  )
}

const COMMITMENT_STATUS: Record<Commitment['status'], string> = {
  OPEN: 'En seguimiento',
  FULFILLED: 'Cumplido',
  BREACHED: 'No cumplido',
}

function CommitmentsCard({ commitments }: { commitments: Commitment[] }) {
  return (
    <Card title="Actas con la familia">
      {commitments.length === 0 ? (
        <p className="text-ink-soft">No hay actas registradas.</p>
      ) : (
        <ul className="divide-y divide-rule">
          {commitments.map((commitment) => (
            <li key={commitment.id} className="py-3 first:pt-0 last:pb-0">
              <p className="flex flex-wrap justify-between gap-2">
                <span className="font-bold">{formatDate(commitment.meeting_date)}</span>
                <span className="text-sm text-ink-soft">
                  {COMMITMENT_STATUS[commitment.status]}
                </span>
              </p>
              <p className="mt-1">{commitment.agreements}</p>
              {commitment.follow_up_date && (
                <p className="mt-1 text-sm text-ink-soft">
                  Seguimiento: {formatDate(commitment.follow_up_date)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

function SurveyCard({ survey, periods }: { survey: FamilySurvey; periods?: Period[] }) {
  const rows: [string, string][] = [
    ['Horas de estudio', formatFactorValue('study_hours_week', survey.study_hours_week)],
    ['Educación de los padres', formatFactorValue('parent_education', survey.parent_education)],
    ['Internet en casa', formatFactorValue('home_internet', survey.home_internet)],
    ['Dispositivo para estudiar', formatFactorValue('has_study_device', survey.has_study_device)],
    ['Comunicación familiar', formatFactorValue('family_communication', survey.family_communication)],
    ['Trabaja', formatFactorValue('student_works', survey.student_works)],
    ['Personas en el hogar', formatFactorValue('household_size', survey.household_size)],
  ]
  return (
    <Card title="Encuesta familiar">
      <p className="mb-3 text-sm text-ink-soft">{periodName(periods, survey.period_id)}</p>
      <dl className="divide-y divide-rule">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 py-2">
            <dt className="text-ink-soft">{label}</dt>
            <dd className="text-right">{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

function SituationsCard({ situations }: { situations: Situation[] }) {
  return (
    <Card title="Situaciones de contexto">
      {situations.length === 0 ? (
        <p className="text-ink-soft">No hay situaciones activas.</p>
      ) : (
        <ul className="divide-y divide-rule">
          {situations.map((situation) => (
            <li key={situation.id} className="py-3 first:pt-0 last:pb-0">
              <p className="flex flex-wrap items-center justify-between gap-2">
                <SituationChip situation={situation} />
                <span className="text-sm text-ink-soft">
                  Desde el {formatDate(situation.started_on)}
                </span>
              </p>
              {situation.note && <p className="mt-2">{situation.note}</p>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export default function StudentRecordPage() {
  const studentId = Number(useParams().studentId)
  const location = useLocation()
  const student = useStudent(studentId)
  const summary = useStudentSummary(studentId, null)
  const risk = useStudentRiskHistory(studentId)
  const grades = useStudentGrades(studentId)
  const recommendations = useStudentRecommendations(studentId)
  const commitments = useStudentCommitments(studentId)
  const surveys = useStudentSurveys(studentId)
  const situations = useStudentSituations(studentId)
  const { user } = useAuth()
  const managesGuardians = user?.role === 'DIRECTOR' || user?.role === 'ANALYST'
  const periods = usePeriods()
  const classrooms = useClassrooms()

  if (student.isPending) return <LoadingState label="Cargando la ficha…" />
  if (student.isError) {
    return (
      <EmptyState
        title="No pudimos abrir esta ficha"
        description={messageFor(student.error)}
        action={
          <Link to="/aulas" className="font-bold text-accent underline underline-offset-4">
            Volver a las aulas
          </Link>
        }
      />
    )
  }

  const detail = student.data
  const classroom = classrooms.data?.find((item) => item.id === detail.classroom_id)
  const classroomName = classroom ? classroomLabel(classroom) : 'Aula'
  const guardians = detail.guardians.map((guardian) => guardian.full_name).join(', ')
  const back = backLink(location.state, detail.classroom_id, classroomName)

  return (
    <>
      <p className="mb-3">
        <Link to={back.to} className="text-sm font-bold text-accent hover:underline">
          {back.label}
        </Link>
      </p>
      <PageHeader
        title={`${detail.last_name}, ${detail.first_name}`}
        description={`${classroomName}, código ${detail.code}. Apoderado: ${
          guardians || 'sin registrar'
        }.`}
      />

      {summary.data && summary.data.period_id !== null && (
        <dl className="mb-8 flex flex-wrap gap-x-12 gap-y-4">
          <div>
            <dt className="text-sm text-ink-soft">
              Promedio, {periodName(periods.data, summary.data.period_id)}
            </dt>
            <dd className="font-figure text-4xl font-semibold tabular-nums">
              {summary.data.average_score === null ? '—' : formatScore(summary.data.average_score)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-ink-soft">Asistencia</dt>
            <dd className="font-figure text-4xl font-semibold tabular-nums">
              {summary.data.attendance_rate === null
                ? '—'
                : formatPercent(summary.data.attendance_rate)}
            </dd>
          </div>
        </dl>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          {risk.isError ? (
            <ErrorMessage>{messageFor(risk.error)}</ErrorMessage>
          ) : (
            risk.data && <RiskCard history={risk.data} periods={periods.data} />
          )}
          {/* Only the tutor and the director see context situations. */}
          {situations.data && <SituationsCard situations={situations.data} />}
          {recommendations.isError ? (
            <ErrorMessage>{messageFor(recommendations.error)}</ErrorMessage>
          ) : (
            recommendations.data && (
              <RecommendationCard recommendation={recommendations.data[0]} />
            )
          )}
        </div>
        <div className="flex flex-col gap-6">
          {grades.data && <GradesCard grades={grades.data} periods={periods.data} />}
          {commitments.isError ? (
            isForbidden(commitments.error) ? (
              <Card title="Actas con la familia">
                <p className="text-ink-soft">
                  Solo el tutor del aula y la dirección pueden ver las actas.
                </p>
              </Card>
            ) : (
              <ErrorMessage>{messageFor(commitments.error)}</ErrorMessage>
            )
          ) : (
            commitments.data && <CommitmentsCard commitments={commitments.data} />
          )}
          {managesGuardians && (
            <GuardiansCard
              studentId={studentId}
              studentName={`${detail.last_name}, ${detail.first_name}`}
            />
          )}
          {/* Teachers never see socio-family data: the section is simply not shown. */}
          {surveys.data?.[0] && <SurveyCard survey={surveys.data[0]} periods={periods.data} />}
        </div>
      </div>
    </>
  )
}
