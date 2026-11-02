import type { User } from '../auth/types'
import type { RiskLevel } from '../../shared/lib/risk'

export interface RiskFactor {
  feature: string
  label: string
  value: unknown
  contribution: number
}

export interface RiskAssessment {
  id: number
  period_id: number
  probability: number
  level: RiskLevel
  model_version: string
  top_factors: RiskFactor[]
  created_at: string
}

export type StudentStatus = 'ENROLLED' | 'WITHDRAWN' | 'TRANSFERRED' | 'GRADUATED'

export type ExitReason =
  | 'TRANSFER'
  | 'WORK'
  | 'ECONOMIC'
  | 'FAMILY'
  | 'HEALTH'
  | 'PREGNANCY'
  | 'DISTANCE'
  | 'DISENGAGEMENT'
  | 'UNKNOWN'
  | 'GRADUATION'

export interface StudentDetail {
  id: number
  code: string
  first_name: string
  last_name: string
  birth_date: string
  sex: 'M' | 'F'
  classroom_id: number
  status: StudentStatus
  exit_date: string | null
  exit_reason: ExitReason | null
  exit_note: string | null
  guardians: User[]
  latest_risk: RiskAssessment | null
}

export interface Grade {
  subject_id: number
  subject: string
  period_id: number
  score: number
}

export interface StudentSummary {
  period_id: number | null
  average_score: number | null
  attendance_rate: number | null
  grades: Grade[]
  /** Approved recommendations for the family; empty until the tutor approves them. */
  parent_suggestions: string[]
  disclaimer: string | null
}

export type RecommendationStatus = 'PENDING_REVIEW' | 'APPROVED' | 'DISCARDED'

export interface Recommendation {
  id: number
  period_id: number
  status: RecommendationStatus
  parent_items: string[]
  teacher_items: string[]
  reviewed_at: string | null
  sent_at: string | null
  created_at: string
}

export type CommitmentStatus = 'OPEN' | 'FULFILLED' | 'BREACHED'

export interface Commitment {
  id: number
  guardian_id: number
  meeting_date: string
  agreements: string
  follow_up_date: string | null
  status: CommitmentStatus
}

export interface FamilySurvey {
  id: number
  period_id: number
  study_hours_week: number
  parent_education: string
  home_internet: boolean
  has_study_device: boolean
  family_communication: number
  student_works: boolean
  household_size: number
  submitted_at: string
}

/** Minimal data a list already has, enough to open the quick view instantly. */
export interface StudentReference {
  student_id: number
  full_name: string
  code: string
  classroom: string
}
