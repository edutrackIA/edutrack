import { RISK_LABELS, type RiskLevel } from '../../../shared/lib/risk'
import type { ClassroomRiskSummary } from '../types'
import { RiskLamp } from './RiskLamp'

const LEVELS: { level: RiskLevel; key: 'high' | 'medium' | 'low' }[] = [
  { level: 'HIGH', key: 'high' },
  { level: 'MEDIUM', key: 'medium' },
  { level: 'LOW', key: 'low' },
]

export function MiniTrafficLight({ classroom }: { classroom: ClassroomRiskSummary }) {
  if (classroom.evaluated === 0) return <span className="text-sm text-ink-soft">Sin evaluar</span>

  const description = LEVELS.map(
    ({ level, key }) => `${classroom[key]} ${RISK_LABELS[level].toLowerCase()}`,
  ).join(', ')

  return (
    <span className="inline-flex items-center gap-3 rounded-full bg-housing px-3 py-1.5">
      <span className="sr-only">{description}</span>
      {LEVELS.map(({ level, key }) => (
        <span key={level} aria-hidden="true" className="flex items-center gap-1.5">
          <RiskLamp level={level} lit={classroom[key] > 0} size="sm" />
          <span className="text-sm font-bold tabular-nums text-white">{classroom[key]}</span>
        </span>
      ))}
    </span>
  )
}
