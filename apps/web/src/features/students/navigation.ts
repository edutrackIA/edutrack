import { useLocation } from 'react-router-dom'

export interface RecordLinkState {
  from: string
}

/** Link state so the student record can offer a way back to where it was opened. */
export function useRecordLinkState(): RecordLinkState {
  const location = useLocation()
  return { from: `${location.pathname}${location.search}` }
}

const BACK_LABELS: [string, string][] = [
  ['/resumen', 'Volver al resumen'],
  ['/alertas', 'Volver a alertas'],
  ['/recomendaciones', 'Volver a recomendaciones'],
]

/** Where "back" goes from the record: the page that opened it, or the student's classroom. */
export function backLink(
  state: unknown,
  classroomId: number,
  classroomName: string,
): { to: string; label: string } {
  const from = (state as Partial<RecordLinkState> | null)?.from
  const safe = typeof from === 'string' && from.startsWith('/') && !from.startsWith('//')
  if (!safe) return { to: `/aulas?aula=${classroomId}`, label: `Volver a ${classroomName}` }
  const label = BACK_LABELS.find(([prefix]) => from.startsWith(prefix))?.[1]
  return { to: from, label: label ?? `Volver a ${classroomName}` }
}
