import { useId, useState, type FormEvent } from 'react'
import { Button } from '../../../shared/ui/Button'
import { classroomLabel, useClassrooms } from '../../classrooms/api'
import {
  useAssignCourse,
  useAssignments,
  useStaff,
  useSubjects,
  useUnassignCourse,
  type Assignment,
} from '../api'
import { Field, inputClass, MutationError, SetupSection } from './SetupParts'

function AssignmentItem({ assignment }: { assignment: Assignment }) {
  const unassign = useUnassignCourse()
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 border-b border-rule py-2.5 last:border-b-0">
      <span>
        <span className="font-bold text-ink">{assignment.subject}</span>
        <span className="ml-2 text-ink-soft">{assignment.teacher}</span>
      </span>
      <Button variant="ghost" pending={unassign.isPending} onClick={() => unassign.mutate(assignment.id)}>
        Quitar<span className="sr-only"> {assignment.subject}</span>
      </Button>
      <MutationError error={unassign.error} />
    </li>
  )
}

export function AssignmentsSection() {
  const classrooms = useClassrooms()
  const subjects = useSubjects()
  const staff = useStaff()
  const [classroomId, setClassroomId] = useState<number | null>(null)
  const selected = classroomId ?? classrooms.data?.[0]?.id ?? null
  const assignments = useAssignments(selected)
  const assign = useAssignCourse()
  const [subjectId, setSubjectId] = useState('')
  const [teacherId, setTeacherId] = useState('')
  const ids = { classroom: useId(), subject: useId(), teacher: useId() }

  const taken = new Set((assignments.data ?? []).map((item) => item.subject_id))
  const free = (subjects.data ?? []).filter((subject) => !taken.has(subject.id))
  const teachers = (staff.data ?? []).filter(
    (member) => member.role === 'TEACHER' && member.is_active,
  )

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (selected === null) return
    assign.mutate(
      { classroom_id: selected, subject_id: Number(subjectId), teacher_id: Number(teacherId) },
      { onSuccess: () => setSubjectId('') },
    )
  }

  return (
    <SetupSection
      title="Asignaciones"
      description="Qué docente dicta cada curso en cada aula. Cada docente registra las notas de sus cursos."
      form={
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <Field label="Aula" htmlFor={ids.classroom}>
            <select
              id={ids.classroom}
              value={selected ?? ''}
              onChange={(event) => setClassroomId(Number(event.target.value))}
              className={inputClass}
            >
              {classrooms.data?.map((classroom) => (
                <option key={classroom.id} value={classroom.id}>
                  {classroomLabel(classroom)} ({classroom.year})
                </option>
              ))}
            </select>
          </Field>
          <Field label="Curso" htmlFor={ids.subject}>
            <select
              id={ids.subject}
              value={subjectId}
              onChange={(event) => setSubjectId(event.target.value)}
              className={inputClass}
            >
              <option value="">Elige un curso</option>
              {free.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Docente" htmlFor={ids.teacher}>
            <select
              id={ids.teacher}
              value={teacherId}
              onChange={(event) => setTeacherId(event.target.value)}
              className={inputClass}
            >
              <option value="">Elige un docente</option>
              {teachers.map((teacher) => (
                <option key={teacher.id} value={teacher.id}>
                  {teacher.full_name}
                </option>
              ))}
            </select>
          </Field>
          <Button
            type="submit"
            pending={assign.isPending}
            disabled={selected === null || !subjectId || !teacherId}
          >
            Asignar
          </Button>
          <div className="basis-full">
            <MutationError error={assign.error} />
          </div>
        </form>
      }
    >
      {assignments.data && assignments.data.length === 0 && (
        <p className="text-ink-soft">Esta aula todavía no tiene cursos asignados.</p>
      )}
      {assignments.data && assignments.data.length > 0 && (
        <ul aria-label="Cursos asignados del aula" className="max-w-2xl">
          {assignments.data.map((assignment) => (
            <AssignmentItem key={assignment.id} assignment={assignment} />
          ))}
        </ul>
      )}
    </SetupSection>
  )
}
