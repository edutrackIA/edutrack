import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { formatPercent } from '../../../shared/lib/format'
import { RISK_LABELS, type RiskLevel } from '../../../shared/lib/risk'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { useAuth } from '../../auth/auth-context'
import { StudentQuickView } from '../../students/components/StudentQuickView'
import type { StudentReference } from '../../students/types'
import {
  classroomLabel,
  useClassrooms,
  useClassroomStudents,
  type Classroom,
  type ClassroomStudent,
} from '../api'

const LEVEL_FILTERS: (RiskLevel | null)[] = [null, 'HIGH', 'MEDIUM', 'LOW']

/** At-risk students first, then the rest; unevaluated students at the end. */
function byRisk(a: ClassroomStudent, b: ClassroomStudent): number {
  return (b.probability ?? -1) - (a.probability ?? -1) || a.full_name.localeCompare(b.full_name)
}

function ClassroomList({
  classrooms,
  selectedId,
  onSelect,
}: {
  classrooms: Classroom[]
  selectedId: number
  onSelect: (id: number) => void
}) {
  return (
    <nav aria-label="Aulas" className="lg:min-h-0 lg:overflow-y-auto">
      <ul className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-visible lg:pb-0">
        {classrooms.map((classroom) => {
          const selected = classroom.id === selectedId
          return (
            <li key={classroom.id}>
              <button
                type="button"
                aria-current={selected ? 'true' : undefined}
                onClick={() => onSelect(classroom.id)}
                className={`w-full whitespace-nowrap rounded-lg border px-4 py-3 text-left ${
                  selected
                    ? 'border-accent bg-accent-tint'
                    : 'border-rule bg-surface hover:border-accent'
                }`}
              >
                <span className="block font-figure text-lg font-semibold text-ink">
                  {classroomLabel(classroom)}
                </span>
                <span className="block text-sm text-ink-soft">
                  {classroom.student_count}{' '}
                  {classroom.student_count === 1 ? 'estudiante' : 'estudiantes'}
                  {classroom.tutor && `, tutor ${classroom.tutor.full_name}`}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

function LevelFilter({
  value,
  onChange,
}: {
  value: RiskLevel | null
  onChange: (level: RiskLevel | null) => void
}) {
  return (
    <div role="group" aria-label="Filtrar por nivel de riesgo" className="flex flex-wrap gap-1">
      {LEVEL_FILTERS.map((level) => (
        <button
          key={level ?? 'ALL'}
          type="button"
          aria-pressed={value === level}
          onClick={() => onChange(level)}
          className={`rounded-md px-3 py-1.5 text-sm ${
            value === level
              ? 'bg-accent-tint font-bold text-accent-strong'
              : 'text-ink-soft hover:text-ink'
          }`}
        >
          {level ? RISK_LABELS[level] : 'Todos'}
        </button>
      ))}
    </div>
  )
}

function StudentsPanel({ classroom }: { classroom: Classroom }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const level = (searchParams.get('nivel') as RiskLevel | null) ?? null
  const students = useClassroomStudents(classroom.id, level)
  const [selected, setSelected] = useState<StudentReference | null>(null)

  function changeLevel(next: RiskLevel | null) {
    const params = new URLSearchParams(searchParams)
    if (next) params.set('nivel', next)
    else params.delete('nivel')
    setSearchParams(params, { replace: true })
  }

  const rows = [...(students.data ?? [])].sort(byRisk)

  return (
    <section aria-labelledby="students-title" className="flex flex-col lg:min-h-0">
      <div className="mb-3 flex shrink-0 flex-wrap items-center justify-between gap-3">
        <h2 id="students-title" className="font-figure text-xl font-semibold text-ink">
          Estudiantes de {classroomLabel(classroom)}
        </h2>
        <LevelFilter value={level} onChange={changeLevel} />
      </div>

      {students.isPending && <LoadingState label="Cargando estudiantes…" />}
      {students.isError && <ErrorMessage>{messageFor(students.error)}</ErrorMessage>}
      {students.data && rows.length === 0 && (
        <EmptyState
          title="No hay estudiantes con este nivel"
          description="Prueba con otro filtro o elige otra aula."
        />
      )}
      {rows.length > 0 && (
        <div className="lg:min-h-0 lg:overflow-y-auto">
          <Table caption={`Estudiantes de ${classroomLabel(classroom)} con su nivel de riesgo`}>
            <TableHead>
              <tr>
                <TableHeaderCell>Código</TableHeaderCell>
                <TableHeaderCell>Estudiante</TableHeaderCell>
                <TableHeaderCell>Riesgo</TableHeaderCell>
                <TableHeaderCell className="text-right">Probabilidad</TableHeaderCell>
                <TableHeaderCell>
                  <span className="sr-only">Ficha</span>
                </TableHeaderCell>
              </tr>
            </TableHead>
            <TableBody>
              {rows.map((student) => (
                <TableRow key={student.id}>
                  <TableCell className="tabular-nums text-ink-soft">{student.code}</TableCell>
                  <TableCell>
                    <button
                      type="button"
                      onClick={() =>
                        setSelected({
                          student_id: student.id,
                          full_name: student.full_name,
                          code: student.code,
                          classroom: student.classroom,
                        })
                      }
                      className="text-left font-bold text-ink hover:text-accent hover:underline"
                    >
                      {student.full_name}
                    </button>
                  </TableCell>
                  <TableCell>
                    {student.risk_level ? (
                      <RiskBadge level={student.risk_level} />
                    ) : (
                      <span className="text-sm text-ink-soft">Sin evaluar</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {student.probability === null ? '—' : formatPercent(student.probability)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link
                      to={`/estudiantes/${student.id}`}
                      className="text-sm font-bold text-accent hover:underline"
                    >
                      Ver ficha<span className="sr-only"> de {student.full_name}</span>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <StudentQuickView student={selected} periodId={null} onClose={() => setSelected(null)} />
    </section>
  )
}

export default function ClassroomsPage() {
  const { user } = useAuth()
  const classrooms = useClassrooms()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedId = Number(searchParams.get('aula'))
  const list = classrooms.data ?? []
  const selected = list.find((classroom) => classroom.id === requestedId) ?? list[0]

  function selectClassroom(id: number) {
    setSearchParams({ aula: String(id) }, { replace: true })
  }

  const isTeacher = user?.role === 'TEACHER'

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title={isTeacher ? 'Mis aulas' : 'Aulas'}
        description={
          isTeacher
            ? 'Las aulas que tutoreas o donde dictas un curso.'
            : 'Estudiantes de cada aula con su nivel de riesgo.'
        }
      />

      {classrooms.isPending && <LoadingState label="Cargando aulas…" />}
      {classrooms.isError && <ErrorMessage>{messageFor(classrooms.error)}</ErrorMessage>}
      {classrooms.data && list.length === 0 && (
        <EmptyState
          title="Todavía no tienes aulas asignadas"
          description="Cuando la dirección te asigne un aula o un curso, aparecerá aquí."
        />
      )}

      {selected && (
        <div className="grid gap-6 lg:min-h-0 lg:flex-1 lg:grid-cols-[17rem_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)]">
          <ClassroomList classrooms={list} selectedId={selected.id} onSelect={selectClassroom} />
          <StudentsPanel key={selected.id} classroom={selected} />
        </div>
      )}
    </div>
  )
}
