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
    // On desktop the page fills the viewport exactly; long lists scroll inside their panel.
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
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
        <div className="mb-4 shrink-0">
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

      {data && data.period_id !== null && data.evaluated_students === 0 && (
        <EmptyState
          title={`${periodLabel || 'Este bimestre'} aún no tiene evaluación de riesgo`}
          description="Elige otro bimestre o pide al área de análisis que ejecute la evaluación."
        />
      )}

      {data && data.period_id !== null && data.evaluated_students > 0 && (
        <>
          <RiskOverview summary={data} periodLabel={periodLabel} />
          <div className="grid gap-8 lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:grid-rows-[minmax(0,1fr)]">
            <SchoolTrafficLight summary={data} />
            <div className="flex flex-col gap-8 lg:min-h-0">
              <ClassroomRiskTable classrooms={data.by_classroom} students={data.students} />
              <TopFactors factors={data.top_factors} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
