import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { usePeriods } from '../../periods/api'
import { PeriodSelect } from '../../periods/PeriodSelect'
import { downloadRiskReport, useDashboardSummary } from '../api'
import { ClassroomRiskTable } from '../components/ClassroomRiskTable'
import { RiskOverview } from '../components/RiskOverview'
import { SchoolTrafficLight } from '../components/SchoolTrafficLight'
import { TopFactors } from '../components/TopFactors'

export default function DashboardPage() {
  const [periodId, setPeriodId] = useState<number | null>(null)
  const summary = useDashboardSummary(periodId)
  const periods = usePeriods()
  const report = useMutation({ mutationFn: downloadRiskReport })

  const data = summary.data
  const activePeriod = data?.period_id ?? null
  const periodLabel =
    periods.data?.find((period) => period.id === activePeriod)?.label ?? data?.period_label ?? ''

  return (
    <>
      <PageHeader
        title="Resumen del colegio"
        description="Cómo está cada aula y qué explica el riesgo en el bimestre."
        actions={
          activePeriod !== null && (
            <>
              {periods.data && (
                <PeriodSelect periods={periods.data} value={activePeriod} onChange={setPeriodId} />
              )}
              <Button
                variant="secondary"
                pending={report.isPending}
                onClick={() => report.mutate(activePeriod)}
              >
                Descargar reporte PDF
              </Button>
            </>
          )
        }
      />

      {report.isError && (
        <div className="mb-6">
          <ErrorMessage>{messageFor(report.error)}</ErrorMessage>
        </div>
      )}

      {summary.isPending && <LoadingState label="Cargando el resumen…" />}
      {summary.isError && <ErrorMessage>{messageFor(summary.error)}</ErrorMessage>}

      {data && data.period_id === null && (
        <EmptyState
          title="Aún no hay evaluaciones de riesgo"
          description="Cuando el área de análisis evalúe un bimestre, aquí verás cómo está cada aula."
        />
      )}

      {data && data.period_id !== null && (
        <>
          <RiskOverview summary={data} periodLabel={periodLabel} />
          <SchoolTrafficLight summary={data} />
          <div className="grid gap-10 lg:grid-cols-[1.6fr_1fr]">
            <ClassroomRiskTable classrooms={data.by_classroom} students={data.students} />
            <TopFactors factors={data.top_factors} />
          </div>
        </>
      )}
    </>
  )
}
