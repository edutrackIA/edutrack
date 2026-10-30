import { useId, useState } from 'react'
import { EmptyState, LoadingState } from '../../../shared/ui/Feedback'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { periodOptionLabel, usePeriods } from '../../periods/api'
import {
  periodFor,
  todayValue,
  useGradebook,
  useSaveGrades,
  type Gradebook,
  type TeachingCourse,
} from '../api'
import { SaveBar, selectClass } from './SheetParts'

const PASSING_SCORE = 11

function parseScore(raw: string): number | null | 'invalid' {
  const text = raw.trim().replace(',', '.')
  if (text === '') return null
  const value = Number(text)
  return Number.isFinite(value) && value >= 0 && value <= 20 ? value : 'invalid'
}

function GradesTable({ book }: { book: Gradebook }) {
  const save = useSaveGrades()
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const [saved, setSaved] = useState(false)

  const changed = book.rows.filter((row) => {
    const draft = drafts[row.student_id]
    return draft !== undefined && parseScore(draft) !== row.score
  })
  const invalid = changed.some((row) => parseScore(drafts[row.student_id]) === 'invalid')

  function handleSave() {
    save.mutate(
      {
        classroom_id: book.classroom_id,
        subject_id: book.subject_id,
        period_id: book.period_id,
        scores: changed.map((row) => ({
          student_id: row.student_id,
          score: parseScore(drafts[row.student_id]) as number | null,
        })),
      },
      {
        onSuccess: () => {
          setDrafts({})
          setSaved(true)
        },
      },
    )
  }

  return (
    <>
      <div className="lg:min-h-0 lg:overflow-y-auto">
        <Table caption="Notas del curso en el bimestre">
          <TableHead>
            <tr>
              <TableHeaderCell>Código</TableHeaderCell>
              <TableHeaderCell>Estudiante</TableHeaderCell>
              <TableHeaderCell>Nota (0 a 20)</TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {book.rows.map((row) => {
              const value = drafts[row.student_id] ?? (row.score === null ? '' : String(row.score))
              const parsed = parseScore(value)
              const wrong = parsed === 'invalid'
              return (
                <TableRow key={row.student_id}>
                  <TableCell className="tabular-nums text-ink-soft">{row.code}</TableCell>
                  <TableCell className="font-bold">{row.full_name}</TableCell>
                  <TableCell>
                    <input
                      inputMode="decimal"
                      aria-label={`Nota de ${row.full_name}`}
                      aria-invalid={wrong || undefined}
                      value={value}
                      onChange={(event) => {
                        setSaved(false)
                        setDrafts({ ...drafts, [row.student_id]: event.target.value })
                      }}
                      className={`w-24 rounded-md border bg-surface px-3 py-1.5 text-right tabular-nums ${
                        wrong
                          ? 'border-risk-high text-risk-high'
                          : typeof parsed === 'number' && parsed < PASSING_SCORE
                            ? 'border-rule text-risk-high'
                            : 'border-rule text-ink'
                      }`}
                    />
                    {wrong && <span className="ml-2 text-sm text-risk-high">Entre 0 y 20</span>}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
      <SaveBar
        label="Guardar notas"
        changes={invalid ? 0 : changed.length}
        pending={save.isPending}
        saved={saved}
        error={save.error}
        onSave={handleSave}
        extra={
          invalid && <span className="text-sm text-risk-high">Corrige las notas marcadas en rojo.</span>
        }
      />
    </>
  )
}

export function GradesSheet({ courses }: { courses: TeachingCourse[] }) {
  const periods = usePeriods()
  const [courseKey, setCourseKey] = useState('')
  const [periodId, setPeriodId] = useState<number | null>(null)
  const ids = { course: useId(), period: useId() }

  const course =
    courses.find((item) => `${item.classroom_id}:${item.subject_id}` === courseKey) ?? courses[0]
  const period = periods.data?.find((item) => item.id === periodId) ?? periodFor(periods.data, todayValue())
  const book = useGradebook(
    course && period
      ? { classroomId: course.classroom_id, subjectId: course.subject_id, periodId: period.id }
      : null,
  )

  if (courses.length === 0) {
    return (
      <EmptyState
        title="No tienes cursos asignados"
        description="La dirección asigna los cursos desde Configuración."
      />
    )
  }

  return (
    <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1">
      <div className="flex shrink-0 flex-wrap gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.course} className="text-sm font-bold text-ink">
            Curso
          </label>
          <select id={ids.course} value={course ? `${course.classroom_id}:${course.subject_id}` : ''} onChange={(event) => setCourseKey(event.target.value)} className={selectClass}>
            {courses.map((item) => (
              <option key={`${item.classroom_id}:${item.subject_id}`} value={`${item.classroom_id}:${item.subject_id}`}>
                {item.classroom}, {item.subject} ({item.year})
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.period} className="text-sm font-bold text-ink">
            Bimestre
          </label>
          <select id={ids.period} value={period?.id ?? ''} onChange={(event) => setPeriodId(Number(event.target.value))} className={selectClass}>
            {periods.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {periodOptionLabel(item)}
              </option>
            ))}
          </select>
        </div>
      </div>
      {book.isPending && <LoadingState />}
      {book.data && <GradesTable key={`${courseKey}-${period?.id}`} book={book.data} />}
    </div>
  )
}
