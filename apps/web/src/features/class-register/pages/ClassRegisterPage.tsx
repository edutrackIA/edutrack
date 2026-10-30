import { useSearchParams } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { useMyTeaching } from '../api'
import { AttendanceSheetView } from '../components/AttendanceSheetView'
import { BehaviorSheetView } from '../components/BehaviorSheetView'
import { GradesSheet } from '../components/GradesSheet'

const SHEETS = [
  { id: 'asistencia', label: 'Asistencia' },
  { id: 'notas', label: 'Notas' },
  { id: 'conducta', label: 'Conducta' },
] as const

/** The teacher's daily register: attendance, grades of their courses and conduct. */
export default function ClassRegisterPage() {
  const teaching = useMyTeaching()
  const [searchParams, setSearchParams] = useSearchParams()
  const isTutor = teaching.data?.classrooms.some((item) => item.is_tutor) ?? false
  const sheets = SHEETS.filter((sheet) => sheet.id !== 'conducta' || isTutor)
  const current = sheets.find((sheet) => sheet.id === searchParams.get('hoja')) ?? sheets[0]

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title="Registro"
        description="Asistencia del día, notas de tus cursos y conducta de tu aula."
        actions={
          <div role="tablist" aria-label="Hojas del registro" className="flex gap-1">
            {sheets.map((sheet) => (
              <button
                key={sheet.id}
                type="button"
                role="tab"
                aria-selected={sheet.id === current.id}
                onClick={() => setSearchParams({ hoja: sheet.id }, { replace: true })}
                className={`rounded-md px-3 py-1.5 ${
                  sheet.id === current.id
                    ? 'bg-accent-tint font-bold text-accent-strong'
                    : 'text-ink-soft hover:text-ink'
                }`}
              >
                {sheet.label}
              </button>
            ))}
          </div>
        }
      />
      {teaching.isPending && <LoadingState />}
      {teaching.isError && <ErrorMessage>{messageFor(teaching.error)}</ErrorMessage>}
      {teaching.data && current.id === 'asistencia' && (
        <AttendanceSheetView classrooms={teaching.data.classrooms} />
      )}
      {teaching.data && current.id === 'notas' && <GradesSheet courses={teaching.data.courses} />}
      {teaching.data && current.id === 'conducta' && (
        <BehaviorSheetView classrooms={teaching.data.classrooms} />
      )}
    </div>
  )
}
