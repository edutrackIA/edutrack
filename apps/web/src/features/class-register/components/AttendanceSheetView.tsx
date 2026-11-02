import { useId, useState } from 'react'
import { Button } from '../../../shared/ui/Button'
import { EmptyState, LoadingState } from '../../../shared/ui/Feedback'
import {
  todayValue,
  useAttendanceSheet,
  useSaveAttendance,
  type AttendanceSheet,
  type AttendanceStatus,
  type TeachingClassroom,
} from '../api'
import { SaveBar, selectClass } from './SheetParts'

const OPTIONS: { value: AttendanceStatus; short: string; label: string; on: string }[] = [
  { value: 'PRESENT', short: 'P', label: 'Presente', on: 'bg-risk-low-bg text-risk-low border-risk-low/40' },
  { value: 'LATE', short: 'T', label: 'Tardanza', on: 'bg-risk-medium-bg text-risk-medium border-risk-medium/40' },
  { value: 'ABSENT', short: 'F', label: 'Falta', on: 'bg-risk-high-bg text-risk-high border-risk-high/40' },
  { value: 'JUSTIFIED', short: 'J', label: 'Justificada', on: 'bg-accent-tint text-accent-strong border-accent/40' },
]

function Sheet({ sheet }: { sheet: AttendanceSheet }) {
  const save = useSaveAttendance(sheet.classroom_id)
  const [marks, setMarks] = useState<Record<number, AttendanceStatus>>({})
  const [saved, setSaved] = useState(false)
  const statusOf = (studentId: number, recorded: AttendanceStatus | null) =>
    marks[studentId] ?? recorded

  const changed = sheet.rows.filter(
    (row) => marks[row.student_id] !== undefined && marks[row.student_id] !== row.status,
  )
  const missing = sheet.rows.filter((row) => statusOf(row.student_id, row.status) === null)

  function setMark(studentId: number, status: AttendanceStatus) {
    setSaved(false)
    setMarks((current) => ({ ...current, [studentId]: status }))
  }

  function handleSave() {
    save.mutate(
      {
        date: sheet.date,
        records: changed.map((row) => ({ student_id: row.student_id, status: marks[row.student_id] })),
      },
      {
        onSuccess: () => {
          setMarks({})
          setSaved(true)
        },
      },
    )
  }

  if (sheet.period_id === null) {
    return (
      <EmptyState
        title="Esta fecha no pertenece a ningún bimestre"
        description="Elige un día de clases. La dirección define las fechas de cada bimestre."
      />
    )
  }

  return (
    <>
      <ul aria-label="Asistencia del día" className="divide-y divide-rule rounded-xl border border-rule bg-surface lg:min-h-0 lg:overflow-y-auto">
        {sheet.rows.map((row) => {
          const current = statusOf(row.student_id, row.status)
          return (
            <li key={row.student_id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5">
              <span className="font-bold text-ink">{row.full_name}</span>
              <div role="radiogroup" aria-label={`Asistencia de ${row.full_name}`} className="flex gap-1">
                {OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    role="radio"
                    aria-checked={current === option.value}
                    aria-label={option.label}
                    title={option.label}
                    onClick={() => setMark(row.student_id, option.value)}
                    className={`h-9 w-9 rounded-md border font-bold ${
                      current === option.value ? option.on : 'border-rule text-ink-soft hover:text-ink'
                    }`}
                  >
                    {option.short}
                  </button>
                ))}
              </div>
            </li>
          )
        })}
      </ul>
      <SaveBar
        label="Guardar asistencia"
        changes={changed.length}
        pending={save.isPending}
        saved={saved}
        error={save.error}
        onSave={handleSave}
        extra={
          missing.length > 0 && (
            <Button
              variant="ghost"
              onClick={() => missing.forEach((row) => setMark(row.student_id, 'PRESENT'))}
            >
              {missing.length === 1
                ? 'Marcar presente al estudiante restante'
                : `Marcar presentes a los ${missing.length} restantes`}
            </Button>
          )
        }
      />
    </>
  )
}

export function AttendanceSheetView({ classrooms }: { classrooms: TeachingClassroom[] }) {
  const [classroomId, setClassroomId] = useState<number | null>(null)
  const [day, setDay] = useState(todayValue())
  const ids = { classroom: useId(), day: useId() }
  const selected = classrooms.find((item) => item.classroom_id === classroomId) ?? classrooms[0]
  const sheet = useAttendanceSheet(selected?.classroom_id ?? null, day)

  if (classrooms.length === 0) {
    return <EmptyState title="No tienes aulas a cargo" description="Necesitas ser tutor o dictar un curso en el aula." />
  }

  return (
    <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1">
      <div className="flex shrink-0 flex-wrap gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.classroom} className="text-sm font-bold text-ink">
            Aula
          </label>
          <select id={ids.classroom} value={selected?.classroom_id} onChange={(event) => setClassroomId(Number(event.target.value))} className={selectClass}>
            {classrooms.map((item) => (
              <option key={item.classroom_id} value={item.classroom_id}>
                {item.classroom} ({item.year})
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.day} className="text-sm font-bold text-ink">
            Fecha
          </label>
          <input id={ids.day} type="date" max={todayValue()} value={day} onChange={(event) => setDay(event.target.value)} className={selectClass} />
        </div>
      </div>
      <p className="shrink-0 text-sm text-ink-soft">P: presente, T: tardanza, F: falta, J: falta justificada.</p>
      {sheet.isPending && <LoadingState />}
      {sheet.data && <Sheet key={`${sheet.data.classroom_id}-${sheet.data.date}`} sheet={sheet.data} />}
    </div>
  )
}
