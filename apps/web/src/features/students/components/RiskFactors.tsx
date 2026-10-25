import { factorWeight, formatFactorValue, WEIGHT_LABELS, type FactorWeight } from '../factor-format'
import type { RiskFactor } from '../types'

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

export function RiskFactors({ factors }: { factors: RiskFactor[] }) {
  const strongest = Math.max(...factors.map((factor) => factor.contribution), 0)

  return (
    <>
      <p className="flex items-baseline justify-between gap-3">
        <span className="font-bold">Por qué está en riesgo</span>
        <span className="text-sm text-ink-soft">Ordenados por influencia</span>
      </p>
      <ol className="mt-2" aria-label="Qué explica el riesgo">
        {factors.map((factor) => {
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
  )
}
