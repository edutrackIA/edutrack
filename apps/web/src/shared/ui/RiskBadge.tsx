import { RISK_LABELS, type RiskLevel } from '../lib/risk'

const STYLES: Record<RiskLevel, { badge: string; dot: string }> = {
  LOW: { badge: 'bg-risk-low-bg text-risk-low', dot: 'bg-risk-low-mark' },
  MEDIUM: { badge: 'bg-risk-medium-bg text-risk-medium', dot: 'bg-risk-medium-mark' },
  HIGH: { badge: 'bg-risk-high-bg text-risk-high', dot: 'bg-risk-high-mark' },
}

/** The level is always written out, so the color is never the only cue. */
export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-bold ${STYLES[level].badge}`}
    >
      <span aria-hidden="true" className={`h-2.5 w-2.5 rounded-full ${STYLES[level].dot}`} />
      {RISK_LABELS[level]}
    </span>
  )
}
