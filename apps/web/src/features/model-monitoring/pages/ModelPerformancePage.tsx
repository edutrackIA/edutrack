import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { formatDate, formatPercent } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
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
import { useAuth } from '../../auth/auth-context'
import { EXIT_REASONS } from '../../students/exitReasons'
import { ModelVersionsSection } from '../components/ModelVersionsSection'
import {
  downloadDataset,
  useModelPerformance,
  type ModelPerformance,
  type PerformanceMetrics,
} from '../api'

function Progress({ label, value, goal }: { label: string; value: number; goal: number }) {
  const ratio = Math.min(value / goal, 1)
  return (
    <div>
      <p className="flex justify-between text-sm">
        <span className="text-ink">{label}</span>
        <span className="tabular-nums text-ink-soft">
          {value} de {goal}
        </span>
      </p>
      <div aria-hidden="true" className="mt-1 h-2 rounded-full bg-rule">
        <div className="h-full rounded-full bg-accent" style={{ width: `${ratio * 100}%` }} />
      </div>
    </div>
  )
}

function NotEnoughData({ data }: { data: ModelPerformance }) {
  return (
    <section className="rounded-xl border border-rule bg-surface p-6">
      <h2 className="font-figure text-xl font-semibold text-ink">
        Aún no hay suficientes resultados reales
      </h2>
      <p className="mt-2 max-w-2xl text-ink-soft">
        El resultado de una evaluación se conoce cuando el estudiante se retira o cuando pasan{' '}
        {data.window_days} días desde el fin del bimestre sin que se retire. Con pocos casos, los
        porcentajes dirían más del azar que del modelo.
      </p>
      <div className="mt-5 grid max-w-xl gap-4">
        <Progress label="Evaluaciones con resultado conocido" value={data.labeled} goal={data.min_labeled} />
        <Progress label="Retiros registrados" value={data.dropouts} goal={data.min_dropouts} />
      </div>
      <p className="mt-4 text-sm text-ink-soft">
        {data.pending} evaluaciones esperan que se cumpla el plazo. Registrar cada retiro en la
        ficha del estudiante es lo que permite medir el modelo.
      </p>
    </section>
  )
}

function Metrics({ metrics }: { metrics: PerformanceMetrics }) {
  const dropouts = metrics.true_positives + metrics.false_negatives
  const alerts = metrics.true_positives + metrics.false_positives
  return (
    <section aria-labelledby="metrics-title" className="flex flex-col gap-5">
      <h2 id="metrics-title" className="sr-only">
        Resultados del modelo
      </h2>
      <div className="grid gap-5 md:grid-cols-2">
        <div className="rounded-xl border border-rule bg-surface p-5">
          <p className="font-figure text-4xl font-semibold tabular-nums text-ink">
            {metrics.recall === null ? '—' : formatPercent(metrics.recall)}
          </p>
          <p className="mt-2 text-ink">
            El modelo había alertado a <strong>{metrics.true_positives}</strong> de los{' '}
            <strong>{dropouts}</strong> estudiantes que se retiraron.
          </p>
          <p className="mt-1 text-sm text-ink-soft">
            Es lo más importante: un retiro sin alerta previa es una oportunidad perdida.
          </p>
        </div>
        <div className="rounded-xl border border-rule bg-surface p-5">
          <p className="font-figure text-4xl font-semibold tabular-nums text-ink">
            {metrics.precision === null ? '—' : formatPercent(metrics.precision)}
          </p>
          <p className="mt-2 text-ink">
            <strong>{metrics.true_positives}</strong> de las <strong>{alerts}</strong> alertas
            terminaron en retiro.
          </p>
          <p className="mt-1 text-sm text-ink-soft">
            Una alerta sin retiro no siempre es un error: el acompañamiento pudo evitarlo.
          </p>
        </div>
      </div>
      <Table caption="Alertas frente a lo que ocurrió">
        <TableHead>
          <tr>
            <TableHeaderCell> </TableHeaderCell>
            <TableHeaderCell className="text-right">Se retiraron</TableHeaderCell>
            <TableHeaderCell className="text-right">Siguieron estudiando</TableHeaderCell>
          </tr>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell className="font-bold">Con alerta (moderado o alto)</TableCell>
            <TableCell className="text-right tabular-nums">{metrics.true_positives}</TableCell>
            <TableCell className="text-right tabular-nums">{metrics.false_positives}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell className="font-bold">Sin alerta (bajo)</TableCell>
            <TableCell className="text-right tabular-nums">{metrics.false_negatives}</TableCell>
            <TableCell className="text-right tabular-nums">{metrics.true_negatives}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </section>
  )
}

function Cases({ data }: { data: ModelPerformance }) {
  if (data.cases.length === 0) return null
  return (
    <section aria-labelledby="cases-title">
      <h2 id="cases-title" className="mb-3 font-figure text-xl font-semibold text-ink">
        Estudiantes que se retiraron
      </h2>
      <Table caption="Estudiantes que se retiraron y la última evaluación previa">
        <TableHead>
          <tr>
            <TableHeaderCell>Estudiante</TableHeaderCell>
            <TableHeaderCell>Fecha</TableHeaderCell>
            <TableHeaderCell>Motivo</TableHeaderCell>
            <TableHeaderCell>Última evaluación</TableHeaderCell>
            <TableHeaderCell>¿Hubo alerta?</TableHeaderCell>
          </tr>
        </TableHead>
        <TableBody>
          {data.cases.map((item) => (
            <TableRow key={item.student_id}>
              <TableCell>
                <Link to={`/estudiantes/${item.student_id}`} className="font-bold text-ink hover:text-accent hover:underline">
                  {item.full_name}
                </Link>
              </TableCell>
              <TableCell>{item.exit_date ? formatDate(item.exit_date) : '—'}</TableCell>
              <TableCell>{item.exit_reason ? EXIT_REASONS[item.exit_reason] : '—'}</TableCell>
              <TableCell>
                <span className="flex items-center gap-2">
                  <RiskBadge level={item.last_level} />
                  <span className="tabular-nums text-ink-soft">{formatPercent(item.last_probability)}</span>
                </span>
              </TableCell>
              <TableCell className={item.alerted ? 'text-risk-low' : 'font-bold text-risk-high'}>
                {item.alerted ? 'Sí' : 'No'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </section>
  )
}

export default function ModelPerformancePage() {
  const { user } = useAuth()
  const performance = useModelPerformance()
  const download = useMutation({ mutationFn: downloadDataset })
  const data = performance.data

  return (
    <>
      <PageHeader
        title="Rendimiento del modelo"
        description="Cómo acertó el modelo frente a lo que realmente pasó con los estudiantes."
        actions={
          user?.role === 'ANALYST' && (
            <Button variant="secondary" pending={download.isPending} onClick={() => download.mutate()}>
              Descargar datos anonimizados
            </Button>
          )
        }
      />
      {download.isError && <ErrorMessage>{messageFor(download.error)}</ErrorMessage>}
      {performance.isPending && <LoadingState />}
      {performance.isError && <ErrorMessage>{messageFor(performance.error)}</ErrorMessage>}
      {data && data.model_versions.length === 0 && (
        <EmptyState
          title="Todavía no hay evaluaciones"
          description="El rendimiento se mide sobre las evaluaciones de riesgo ejecutadas."
        />
      )}
      {data && data.model_versions.length > 0 && (
        <div className="flex flex-col gap-8">
          <p className="text-sm text-ink-soft">
            Modelos evaluados: {data.model_versions.join(', ')}. Resultados conocidos:{' '}
            {data.labeled}; en espera: {data.pending}.
          </p>
          {data.metrics ? <Metrics metrics={data.metrics} /> : <NotEnoughData data={data} />}
          <Cases data={data} />
        </div>
      )}
      {(user?.role === 'DIRECTOR' || user?.role === 'ANALYST') && (
        <div className="mt-10">
          <ModelVersionsSection role={user.role} />
        </div>
      )}
    </>
  )
}
