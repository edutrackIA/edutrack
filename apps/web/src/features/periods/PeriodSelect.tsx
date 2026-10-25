import { useId } from 'react'
import type { Period } from './api'

interface PeriodSelectProps {
  periods: Period[]
  value: number | null
  onChange: (periodId: number) => void
}

export function PeriodSelect({ periods, value, onChange }: PeriodSelectProps) {
  const id = useId()
  return (
    <div className="flex items-center gap-2">
      <label htmlFor={id} className="font-bold text-ink">
        Bimestre
      </label>
      <select
        id={id}
        value={value ?? ''}
        onChange={(event) => onChange(Number(event.target.value))}
        className="rounded-md border border-rule bg-surface px-3 py-2 text-ink"
      >
        {value === null && <option value="">Elige un bimestre</option>}
        {periods.map((period) => (
          <option key={period.id} value={period.id}>
            {period.label}
          </option>
        ))}
      </select>
    </div>
  )
}
