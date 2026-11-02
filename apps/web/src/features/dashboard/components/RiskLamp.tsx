import type { RiskLevel } from '../../../shared/lib/risk'

const LIT: Record<RiskLevel, string> = {
  HIGH: 'bg-risk-high-mark shadow-[0_0_22px_4px_rgb(var(--color-risk-high-mark)/0.6)]',
  MEDIUM: 'bg-risk-medium-mark shadow-[0_0_22px_4px_rgb(var(--color-risk-medium-mark)/0.6)]',
  LOW: 'bg-risk-low-mark shadow-[0_0_22px_4px_rgb(var(--color-risk-low-mark)/0.6)]',
}

const SIZES = {
  lg: 'h-[4.5rem] w-[4.5rem]',
  sm: 'h-4 w-4',
}

/** A traffic light lamp: lit with its color when the level has students. */
export function RiskLamp({
  level,
  lit,
  size = 'lg',
}: {
  level: RiskLevel
  lit: boolean
  size?: keyof typeof SIZES
}) {
  return (
    <span
      aria-hidden="true"
      className={`block shrink-0 rounded-full ${SIZES[size]} ${
        lit ? LIT[level] : 'bg-white/10 ring-1 ring-inset ring-white/15'
      }`}
    />
  )
}
