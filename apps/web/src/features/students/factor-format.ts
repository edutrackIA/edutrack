import { formatPercent, formatScore } from '../../shared/lib/format'

const PARENT_EDUCATION: Record<string, string> = {
  NONE: 'Sin estudios',
  PRIMARY: 'Primaria',
  SECONDARY: 'Secundaria',
  TECHNICAL: 'Técnica',
  UNIVERSITY: 'Universitaria',
}

function plural(value: number, singular: string, pluralForm: string): string {
  return `${value} ${value === 1 ? singular : pluralForm}`
}

/** The student's own value for a model feature, written as people read it. */
export function formatFactorValue(feature: string, value: unknown): string {
  if (typeof value === 'boolean') return value ? 'Sí' : 'No'
  if (typeof value === 'string') return PARENT_EDUCATION[value] ?? value
  if (typeof value !== 'number') return '—'

  switch (feature) {
    case 'avg_score':
      return `${formatScore(value)} de 20`
    case 'failed_subjects':
      return plural(value, 'curso', 'cursos')
    case 'score_trend':
      return value === 0
        ? 'Sin cambio'
        : `${value > 0 ? '+' : ''}${formatScore(value)} vs. bimestre anterior`
    case 'attendance_rate':
      return formatPercent(value)
    case 'late_count':
      return plural(value, 'tardanza', 'tardanzas')
    case 'behavior_rating':
    case 'family_communication':
      return `${value} de 5`
    case 'study_hours_week':
      return `${value} h por semana`
    case 'household_size':
      return plural(value, 'persona', 'personas')
    default:
      return String(value)
  }
}

export type FactorWeight = 3 | 2 | 1

export const WEIGHT_LABELS: Record<FactorWeight, string> = {
  3: 'Pesa mucho',
  2: 'Pesa bastante',
  1: 'Pesa poco',
}

/** Influence relative to the strongest factor of the same student. */
export function factorWeight(contribution: number, strongest: number): FactorWeight {
  const ratio = strongest > 0 ? contribution / strongest : 0
  if (ratio >= 0.66) return 3
  if (ratio >= 0.33) return 2
  return 1
}
