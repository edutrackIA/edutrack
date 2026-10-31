import type { ExitReason } from './types'

export const EXIT_REASONS: Record<ExitReason, string> = {
  TRANSFER: 'Traslado a otro colegio',
  WORK: 'Trabajo',
  ECONOMIC: 'Situación económica',
  FAMILY: 'Situación familiar',
  HEALTH: 'Salud',
  PREGNANCY: 'Embarazo o paternidad',
  DISTANCE: 'Distancia o transporte',
  DISENGAGEMENT: 'Desmotivación',
  UNKNOWN: 'No se conoce el motivo',
  GRADUATION: 'Egreso',
}
