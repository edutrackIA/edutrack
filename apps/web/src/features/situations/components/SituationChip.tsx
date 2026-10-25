import type { Situation } from '../api'

/** Team-only situations look different so the tutor knows they never reach the family. */
export function SituationChip({ situation, onClick }: { situation: Situation; onClick?: () => void }) {
  const team = situation.group === 'TEAM'
  const className = `inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-left text-sm ${
    team ? 'border-risk-high/40 bg-risk-high-bg text-risk-high' : 'border-rule bg-paper text-ink'
  }`
  const content = (
    <>
      {situation.label}
      {team && <span className="text-xs font-bold">(solo equipo)</span>}
    </>
  )
  if (!onClick) return <span className={className}>{content}</span>
  return (
    <button type="button" onClick={onClick} className={`${className} hover:border-accent`}>
      {content}
    </button>
  )
}
