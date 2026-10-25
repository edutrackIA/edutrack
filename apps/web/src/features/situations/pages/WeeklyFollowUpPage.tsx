import { useState } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDayMonth, formatWeekday } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { useAuth } from '../../auth/auth-context'
import { classroomLabel, useClassrooms, useClassroomStudents, type Classroom } from '../../classrooms/api'
import { useCheckin, useClassroomSituations, useCompleteCheckin, type Checkin } from '../api'
import { SituationChip } from '../components/SituationChip'
import { SituationDialog, type SituationDialogState } from '../components/SituationDialog'

function CheckinStatus({ checkin }: { checkin: Checkin }) {
  if (checkin.completed && checkin.completed_at) {
    return (
      <p className="rounded-md bg-risk-low-bg px-3 py-2 text-risk-low">
        Completado. Puedes hacer cambios hasta el {formatWeekday(checkin.deadline)}.
      </p>
    )
  }
  if (!checkin.editable) {
    return (
      <p className="rounded-md bg-paper px-3 py-2 text-ink-soft">
        La semana ya cerró. El seguimiento de la próxima semana se abre el lunes.
      </p>
    )
  }
  return (
    <p className="rounded-md bg-risk-medium-bg px-3 py-2 text-risk-medium">
      Pendiente. Tienes hasta el {formatWeekday(checkin.deadline)}.
    </p>
  )
}

function ClassroomFollowUp({ classroom }: { classroom: Classroom }) {
  const checkin = useCheckin(classroom.id)
  const students = useClassroomStudents(classroom.id, null)
  const situations = useClassroomSituations(classroom.id)
  const complete = useCompleteCheckin(classroom.id)
  const [dialog, setDialog] = useState<SituationDialogState>(null)

  if (checkin.isPending || students.isPending) return <LoadingState />
  if (checkin.isError) return <ErrorMessage>{messageFor(checkin.error)}</ErrorMessage>
  if (students.isError) return <ErrorMessage>{messageFor(students.error)}</ErrorMessage>

  const week = checkin.data
  const today = new Date()
  const todayValue = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(
    today.getDate(),
  ).padStart(2, '0')}`
  const rows = [...students.data].sort((a, b) => a.full_name.localeCompare(b.full_name, 'es'))
  const byStudent = (studentId: number) =>
    (situations.data ?? []).filter((situation) => situation.student_id === studentId)

  return (
    <div className="flex flex-col gap-5 lg:min-h-0 lg:flex-1">
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-4">
        <h2 className="font-figure text-xl font-semibold text-ink">
          {classroomLabel(classroom)}, semana del {formatDayMonth(week.week_start)} al{' '}
          {formatDayMonth(week.deadline)}
        </h2>
        <CheckinStatus checkin={week} />
      </div>

      <div className="lg:min-h-0 lg:overflow-y-auto">
        <Table caption={`Situaciones de los estudiantes de ${classroomLabel(classroom)}`}>
          <TableHead>
            <tr>
              <TableHeaderCell>Estudiante</TableHeaderCell>
              <TableHeaderCell>Situaciones activas</TableHeaderCell>
              <TableHeaderCell>
                <span className="sr-only">Acciones</span>
              </TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {rows.map((student) => {
              const active = byStudent(student.id)
              return (
                <TableRow key={student.id}>
                  <TableCell className="font-bold">{student.full_name}</TableCell>
                  <TableCell>
                    {active.length === 0 ? (
                      <span className="text-sm text-ink-soft">Sin cambios</span>
                    ) : (
                      <ul className="flex flex-wrap gap-2">
                        {active.map((situation) => (
                          <li key={situation.id}>
                            <SituationChip
                              situation={situation}
                              onClick={() =>
                                setDialog({
                                  mode: 'edit',
                                  situation,
                                  studentName: student.full_name,
                                })
                              }
                            />
                          </li>
                        ))}
                      </ul>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      onClick={() =>
                        setDialog({
                          mode: 'create',
                          studentId: student.id,
                          studentName: student.full_name,
                        })
                      }
                    >
                      Marcar situación
                      <span className="sr-only"> de {student.full_name}</span>
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      <footer className="flex shrink-0 flex-wrap items-center gap-4 border-t border-rule pt-4">
        <Button
          pending={complete.isPending}
          disabled={!week.editable}
          onClick={() => complete.mutate()}
        >
          {week.completed ? 'Volver a confirmar la semana' : 'Confirmar seguimiento de la semana'}
        </Button>
        <p className="text-sm text-ink-soft">
          Los estudiantes sin marcas quedan registrados como sin cambios.
        </p>
        {complete.isError && <ErrorMessage>{messageFor(complete.error)}</ErrorMessage>}
      </footer>

      <SituationDialog state={dialog} today={todayValue} onClose={() => setDialog(null)} />
    </div>
  )
}

export default function WeeklyFollowUpPage() {
  const { user } = useAuth()
  const classrooms = useClassrooms()
  const tutored = (classrooms.data ?? []).filter((classroom) => classroom.tutor?.id === user?.id)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selected = tutored.find((classroom) => classroom.id === selectedId) ?? tutored[0]

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title="Seguimiento semanal"
        description="Marca lo que sepas de tus estudiantes para que las recomendaciones tengan en cuenta su contexto."
        actions={
          tutored.length > 1 && (
            <select
              aria-label="Aula"
              value={selected?.id}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="rounded-md border border-rule bg-surface px-3 py-2 text-ink"
            >
              {tutored.map((classroom) => (
                <option key={classroom.id} value={classroom.id}>
                  {classroomLabel(classroom)}
                </option>
              ))}
            </select>
          )
        }
      />

      {classrooms.isPending && <LoadingState />}
      {classrooms.isError && <ErrorMessage>{messageFor(classrooms.error)}</ErrorMessage>}
      {classrooms.data && !selected && (
        <EmptyState
          title="No eres tutor de ninguna aula"
          description="El seguimiento semanal lo completa el tutor de cada aula."
        />
      )}
      {selected && <ClassroomFollowUp key={selected.id} classroom={selected} />}
    </div>
  )
}
