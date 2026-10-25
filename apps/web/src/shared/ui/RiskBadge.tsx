import { RISK_LABELS, type RiskLevel } from '../lib/risk'

const STYLES: Record<RiskLevel, { badge: string; mark: string }> = {
  LOW: { badge: 'bg-risk-low-bg text-risk-low', mark: 'text-risk-low-mark' },
  MEDIUM: { badge: 'bg-risk-medium-bg text-risk-medium', mark: 'text-risk-medium-mark' },
  HIGH: { badge: 'bg-risk-high-bg text-risk-high', mark: 'text-risk-high-mark' },
}

/** Shape plus color, so the level is readable without color perception. */
function RiskMark({ level }: { level: RiskLevel }) {
  return (
    <svg className={`h-2.5 w-2.5 ${STYLES[level].mark}`} viewBox="0 0 10 10" aria-hidden="true">
      {level === 'LOW' && <circle cx="5" cy="5" r="5" fill="currentColor" />}
      {level === 'MEDIUM' && <path d="M5 0 10 10H0Z" fill="currentColor" />}
      {level === 'HIGH' && <rect width="10" height="10" fill="currentColor" />}
    </svg>
  )
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-bold ${STYLES[level].badge}`}
    >
      <RiskMark level={level} />
      {RISK_LABELS[level]}
    </span>
  )
}
