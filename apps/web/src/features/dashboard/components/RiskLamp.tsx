import type { RiskLevel } from '../../../shared/lib/risk'

const LIT: Record<RiskLevel, string> = {
  HIGH: 'bg-risk-high-mark shadow-[0_0_18px_2px_rgb(var(--color-risk-high-mark)/0.55)]',
  MEDIUM: 'bg-risk-medium-mark shadow-[0_0_18px_2px_rgb(var(--color-risk-medium-mark)/0.55)]',
  LOW: 'bg-risk-low-mark shadow-[0_0_18px_2px_rgb(var(--color-risk-low-mark)/0.55)]',
}

const SIZES = {
  lg: { lamp: 'h-14 w-14', shape: 'h-5 w-5' },
  sm: { lamp: 'h-5 w-5', shape: 'h-2 w-2' },
}

/** A traffic light lamp: lit when the level has students, with its shape inside. */
export function RiskLamp({
  level,
  lit,
  size = 'lg',
}: {
  level: RiskLevel
  lit: boolean
  size?: keyof typeof SIZES
}) {
  const { lamp, shape } = SIZES[size]
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-full ${lamp} ${
        lit ? LIT[level] : 'bg-white/10 ring-1 ring-inset ring-white/15'
      }`}
    >
      <svg viewBox="0 0 10 10" className={`${shape} ${lit ? 'text-housing' : 'text-white/25'}`}>
        {level === 'LOW' && <circle cx="5" cy="5" r="5" fill="currentColor" />}
        {level === 'MEDIUM' && <path d="M5 0 10 10H0Z" fill="currentColor" />}
        {level === 'HIGH' && <rect width="10" height="10" fill="currentColor" />}
      </svg>
    </span>
  )
}
