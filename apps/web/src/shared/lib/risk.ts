export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'

export const RISK_LABELS: Record<RiskLevel, string> = {
  LOW: 'Bajo',
  MEDIUM: 'Moderado',
  HIGH: 'Alto',
}

const PRIORITY: Record<RiskLevel, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 }
const UNEVALUATED = 3

/** Priority first (high, moderate, low, not evaluated), then alphabetical by name. */
export function byRiskThenName<T>(level: (item: T) => RiskLevel | null, name: (item: T) => string) {
  return (a: T, b: T): number => {
    const levelA = level(a)
    const levelB = level(b)
    const priorityA = levelA ? PRIORITY[levelA] : UNEVALUATED
    const priorityB = levelB ? PRIORITY[levelB] : UNEVALUATED
    return priorityA - priorityB || name(a).localeCompare(name(b), 'es')
  }
}
