import { useId, useState } from 'react'
import { messageFor } from '../../../shared/api/errors'
import type { RiskLevel } from '../../../shared/lib/risk'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { usePeriods } from '../../periods/api'
import { useRunAssessment, type AssessmentRun } from '../api'

const LEVELS: RiskLevel[] = ['HIGH', 'MEDIUM', 'LOW']

function RunResult({ run, periodLabel }: { run: AssessmentRun; periodLabel: string }) {
  return (
    <section aria-labelledby="run-title" className="flex flex-col gap-5 lg:min-h-0">
      <div className="shrink-0">
        <h2 id="run-title" className="font-figure text-xl font-semibold text-ink">
          {periodLabel}: {run.evaluated} {run.evaluated === 1 ? 'estudiante evaluado' : 'estudiantes evaluados'}
        </h2>
        {run.model_version && (
          <p className="mt-1 text-sm text-ink-soft">Modelo {run.model_version}</p>
        )}
        <ul className="mt-4 flex flex-wrap gap-x-6 gap-y-3" aria-label="Estudiantes por nivel">
          {LEVELS.map((level) => (
            <li key={level} className="flex items-center gap-2">
              <RiskBadge level={level} />
              <span className="text-lg font-bold tabular-nums">{run.by_level[level]}</span>
            </li>
          ))}
        </ul>
      </div>

      {run.skipped > 0 && (
        <div className="flex flex-col gap-3 lg:min-h-0">
          <p className="shrink-0 rounded-md bg-risk-medium-bg px-3 py-2 text-risk-medium">
            {run.skipped} {run.skipped === 1 ? 'estudiante no se pudo evaluar' : 'estudiantes no se pudieron evaluar'}{' '}
            por falta de datos. Complétalos en Carga de datos o pide la encuesta a la familia, y vuelve a
            ejecutar.
          </p>
          <div className="lg:min-h-0 lg:overflow-y-auto">
            <Table caption="Estudiantes sin evaluar y el dato que falta">
              <TableHead>
                <tr>
                  <TableHeaderCell>Código</TableHeaderCell>
                  <TableHeaderCell>Estudiante</TableHeaderCell>
                  <TableHeaderCell>Qué falta</TableHeaderCell>
                </tr>
              </TableHead>
              <TableBody>
                {run.skipped_students.map((student) => (
                  <TableRow key={student.student_id}>
                    <TableCell className="tabular-nums text-ink-soft">{student.code}</TableCell>
                    <TableCell className="font-bold">{student.full_name}</TableCell>
                    <TableCell>{student.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </section>
  )
}

export default function AssessmentsPage() {
  const periods = usePeriods()
  const run = useRunAssessment()
  const [periodId, setPeriodId] = useState<number | null>(null)
  const selectId = useId()
  const period = periods.data?.find((item) => item.id === periodId) ?? periods.data?.[periods.data.length - 1]

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title="Evaluaciones de riesgo"
        description="Ejecuta el modelo para un bimestre con los datos cargados."
      />
      <div className="grid gap-8 lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:grid-rows-[minmax(0,1fr)]">
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label htmlFor={selectId} className="font-bold text-ink">
              Bimestre
            </label>
            <select
              id={selectId}
              value={period?.id ?? ''}
              onChange={(event) => {
                setPeriodId(Number(event.target.value))
                run.reset()
              }}
              className="w-fit rounded-md border border-rule bg-surface px-3 py-2 text-ink"
            >
              {periods.data?.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div className="text-ink-soft">
            <p className="font-bold text-ink">Al ejecutar la evaluación:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>El modelo calcula el nivel de cada estudiante con notas, asistencia, conducta y encuesta.</li>
              <li>Se generan recomendaciones que los tutores revisan antes de enviarlas.</li>
              <li>Los tutores reciben alertas de los casos moderados y altos.</li>
              <li>Las recomendaciones ya aprobadas no cambian.</li>
            </ul>
          </div>
          {run.isError && <ErrorMessage>{messageFor(run.error)}</ErrorMessage>}
          <div>
            <Button
              pending={run.isPending}
              disabled={!period}
              onClick={() => period && run.mutate(period.id)}
            >
              Ejecutar evaluación
            </Button>
          </div>
        </div>

        <div className="rounded-xl border border-rule bg-surface p-6 lg:flex lg:min-h-0 lg:flex-col">
          {run.data && period ? (
            <RunResult run={run.data} periodLabel={period.label} />
          ) : (
            <p className="text-ink-soft">Aquí verás el resultado de la evaluación.</p>
          )}
        </div>
      </div>
    </div>
  )
}
