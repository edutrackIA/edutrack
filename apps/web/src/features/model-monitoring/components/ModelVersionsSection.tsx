import { useState } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate, formatPercent } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { useActivateModel, useModels, useTrainModel, type ModelVersion } from '../api'

function dataLabel(model: ModelVersion): string {
  const synthetic = model.synthetic_samples ? `${model.synthetic_samples} sintéticos` : 'Sintéticos'
  return model.school_samples ? `${synthetic} + ${model.school_samples} del colegio` : synthetic
}

function ActivateButton({ model }: { model: ModelVersion }) {
  const activate = useActivateModel()
  const [confirming, setConfirming] = useState(false)
  if (model.active) return null
  return (
    <div className="flex flex-col items-end gap-1">
      {confirming ? (
        <div className="flex flex-wrap justify-end gap-2">
          <Button pending={activate.isPending} onClick={() => activate.mutate(model.version)}>
            Sí, activar
          </Button>
          <Button variant="ghost" onClick={() => setConfirming(false)}>
            Cancelar
          </Button>
        </div>
      ) : (
        <Button variant="ghost" onClick={() => setConfirming(true)}>
          Activar<span className="sr-only"> {model.version}</span>
        </Button>
      )}
      {activate.isError && <ErrorMessage>{messageFor(activate.error)}</ErrorMessage>}
    </div>
  )
}

function TrainingPanel() {
  const models = useModels()
  const train = useTrainModel()
  const readiness = models.data?.training
  if (!readiness) return null

  return (
    <div className="rounded-xl border border-rule bg-surface p-5">
      <h3 className="font-bold text-ink">Entrenar con datos del colegio</h3>
      <p className="mt-1 text-sm text-ink-soft">
        Crea un modelo candidato con los datos sintéticos y los resultados reales anonimizados del
        colegio. No reemplaza al actual: la dirección decide si lo activa.
      </p>
      {!readiness.can_train && (
        <p className="mt-3 text-sm text-ink">
          Hacen falta {readiness.min_labeled} evaluaciones con resultado y {readiness.min_dropouts}{' '}
          retiros; hay {readiness.labeled} y {readiness.dropouts}.
        </p>
      )}
      <div className="mt-4">
        <Button
          pending={train.isPending}
          disabled={!readiness.can_train}
          onClick={() => train.mutate()}
        >
          {train.isPending ? 'Entrenando, puede tardar unos minutos…' : 'Entrenar modelo candidato'}
        </Button>
      </div>
      {train.isError && (
        <div className="mt-3">
          <ErrorMessage>{messageFor(train.error)}</ErrorMessage>
        </div>
      )}
      {train.data && (
        <p role="status" className="mt-4 rounded-md bg-accent-tint px-4 py-3 text-ink">
          {train.data.candidate.school_holdout
            ? `En ${train.data.candidate.school_holdout.cases} casos reales reservados, el candidato detecta el ${formatPercent(
                train.data.candidate.school_holdout.recall,
              )} de los retiros`
            : 'Candidato entrenado'}
          {train.data.active_on_holdout &&
            `; el modelo actual, el ${formatPercent(train.data.active_on_holdout.recall)}`}
          . La dirección decide si lo activa.
        </p>
      )}
    </div>
  )
}

export function ModelVersionsSection({ role }: { role: 'DIRECTOR' | 'ANALYST' }) {
  const models = useModels()

  return (
    <section aria-labelledby="versions-title" className="flex flex-col gap-4">
      <h2 id="versions-title" className="font-figure text-xl font-semibold text-ink">
        Versiones del modelo
      </h2>
      {role === 'ANALYST' && <TrainingPanel />}
      {models.isPending && <LoadingState />}
      {models.isError && <ErrorMessage>{messageFor(models.error)}</ErrorMessage>}
      {models.data && (
        <Table caption="Versiones del modelo de riesgo">
          <TableHead>
            <tr>
              <TableHeaderCell>Versión</TableHeaderCell>
              <TableHeaderCell>Datos</TableHeaderCell>
              <TableHeaderCell>En casos reales del colegio</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell>
                <span className="sr-only">Acciones</span>
              </TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {models.data.versions.map((model) => (
              <TableRow key={model.version}>
                <TableCell>
                  <span className="font-mono text-sm">{model.version}</span>
                  {model.trained_at && (
                    <span className="block text-sm text-ink-soft">
                      {formatDate(model.trained_at)}
                      {model.trained_by && `, por ${model.trained_by}`}
                    </span>
                  )}
                </TableCell>
                <TableCell>{dataLabel(model)}</TableCell>
                <TableCell>
                  {model.school_holdout
                    ? `Detecta ${formatPercent(model.school_holdout.recall)} de ${model.school_holdout.dropouts ?? '—'} retiros`
                    : '—'}
                </TableCell>
                <TableCell>
                  {model.active ? (
                    <span className="rounded-full bg-risk-low-bg px-2.5 py-0.5 text-sm font-bold text-risk-low">
                      Activo
                    </span>
                  ) : (
                    <span className="text-sm text-ink-soft">Disponible</span>
                  )}
                  {model.active && model.activated_by && (
                    <span className="block text-sm text-ink-soft">por {model.activated_by}</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {role === 'DIRECTOR' && <ActivateButton model={model} />}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </section>
  )
}
