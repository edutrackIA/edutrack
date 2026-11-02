import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { useThresholds, useUpdateThresholds, type Thresholds } from '../api'

function percent(value: number): number {
  return Math.round(value * 100)
}

function Scale({ medium, high }: { medium: number; high: number }) {
  const zones = [
    { label: 'Bajo', width: medium, className: 'bg-risk-low-mark' },
    { label: 'Moderado', width: high - medium, className: 'bg-risk-medium-mark' },
    { label: 'Alto', width: 100 - high, className: 'bg-risk-high-mark' },
  ]
  return (
    <div>
      <div aria-hidden="true" className="flex h-3 overflow-hidden rounded-full">
        {zones.map((zone) => (
          <span key={zone.label} className={zone.className} style={{ width: `${zone.width}%` }} />
        ))}
      </div>
      <p className="mt-2 text-sm text-ink-soft">
        Bajo: menos de {medium} %. Moderado: de {medium} % a {high - 1} %. Alto: {high} % o más.
      </p>
    </div>
  )
}

function ThresholdsForm({ initial }: { initial: Thresholds }) {
  const update = useUpdateThresholds()
  const [medium, setMedium] = useState(percent(initial.medium_from))
  const [high, setHigh] = useState(percent(initial.high_from))
  const [saved, setSaved] = useState(false)
  const mediumId = useId()
  const highId = useId()

  const invalid =
    !Number.isFinite(medium) || !Number.isFinite(high) || medium < 1 || high > 99 || medium >= high

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (invalid) return
    update.mutate(
      { medium_from: medium / 100, high_from: high / 100 },
      { onSuccess: () => setSaved(true) },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex max-w-xl flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={mediumId} className="font-bold text-ink">
            Moderado desde (%)
          </label>
          <input
            id={mediumId}
            type="number"
            min={1}
            max={98}
            value={medium}
            onChange={(event) => {
              setMedium(Number(event.target.value))
              setSaved(false)
            }}
            className="rounded-md border border-rule bg-surface px-3 py-2 text-ink"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={highId} className="font-bold text-ink">
            Alto desde (%)
          </label>
          <input
            id={highId}
            type="number"
            min={2}
            max={99}
            value={high}
            onChange={(event) => {
              setHigh(Number(event.target.value))
              setSaved(false)
            }}
            className="rounded-md border border-rule bg-surface px-3 py-2 text-ink"
          />
        </div>
      </div>

      {invalid ? (
        <ErrorMessage>El umbral moderado debe ser menor que el alto, entre 1 % y 99 %.</ErrorMessage>
      ) : (
        <Scale medium={medium} high={high} />
      )}

      <p className="text-sm text-ink-soft">
        Los cambios se aplican desde la próxima evaluación. Umbrales más bajos detectan más casos,
        pero también generan más alertas para los tutores.
      </p>

      {update.isError && <ErrorMessage>{messageFor(update.error)}</ErrorMessage>}
      <div role="status" aria-live="polite">
        {saved && (
          <p className="rounded-md bg-risk-low-bg px-3 py-2 text-risk-low">Umbrales guardados.</p>
        )}
      </div>
      <div>
        <Button type="submit" pending={update.isPending} disabled={invalid}>
          Guardar umbrales
        </Button>
      </div>
    </form>
  )
}

export default function ThresholdsPage() {
  const thresholds = useThresholds()
  return (
    <>
      <PageHeader
        title="Umbrales de riesgo"
        description="Define desde qué probabilidad un estudiante pasa a riesgo moderado o alto."
      />
      {thresholds.isPending && <LoadingState />}
      {thresholds.isError && <ErrorMessage>{messageFor(thresholds.error)}</ErrorMessage>}
      {thresholds.data && <ThresholdsForm initial={thresholds.data} />}
    </>
  )
}
