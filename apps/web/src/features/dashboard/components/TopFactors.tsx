import type { FactorFrequency } from '../types'

export function TopFactors({ factors }: { factors: FactorFrequency[] }) {
  const max = Math.max(1, ...factors.map((factor) => factor.frequency))

  return (
    <section aria-labelledby="factors-title">
      <h2 id="factors-title" className="font-figure text-xl font-semibold text-ink">
        Qué explica el riesgo
      </h2>
      <p className="mt-1 text-sm text-ink-soft">
        Factores más frecuentes entre los estudiantes en riesgo moderado y alto.
      </p>
      {factors.length === 0 ? (
        <p className="mt-6 text-ink-soft">No hay estudiantes en riesgo moderado o alto.</p>
      ) : (
        <ol className="mt-6 flex flex-col gap-4">
          {factors.map((factor) => (
            <li key={factor.feature}>
              <div className="flex items-baseline justify-between gap-4">
                <span className="font-bold text-ink">{factor.label}</span>
                <span className="text-sm tabular-nums text-ink-soft">
                  {factor.frequency} {factor.frequency === 1 ? 'estudiante' : 'estudiantes'}
                </span>
              </div>
              <div aria-hidden="true" className="mt-1.5 h-1.5 rounded-full bg-rule">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${(factor.frequency / max) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
