export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'

export const RISK_LABELS: Record<RiskLevel, string> = {
  LOW: 'Bajo',
  MEDIUM: 'Moderado',
  HIGH: 'Alto',
}
