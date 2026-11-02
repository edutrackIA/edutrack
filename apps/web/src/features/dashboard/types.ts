import type { RiskLevel } from '../../shared/lib/risk'

export interface ClassroomRiskSummary {
  classroom_id: number
  label: string
  evaluated: number
  low: number
  medium: number
  high: number
}

export interface FactorFrequency {
  feature: string
  label: string
  frequency: number
}

export interface StudentRisk {
  student_id: number
  code: string
  full_name: string
  classroom_id: number
  classroom: string
  level: RiskLevel
  probability: number
}

export interface DashboardSummary {
  period_id: number | null
  period_label: string | null
  total_students: number
  evaluated_students: number
  by_level: Record<RiskLevel, number>
  by_classroom: ClassroomRiskSummary[]
  top_factors: FactorFrequency[]
  students: StudentRisk[]
}
