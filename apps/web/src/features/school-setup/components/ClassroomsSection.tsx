import { useId, useState, type FormEvent } from 'react'
import { Button } from '../../../shared/ui/Button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { classroomLabel, useClassrooms, type Classroom } from '../../classrooms/api'
import { useCreateClassroom, useSetTutor, useStaff, type StaffMember } from '../api'
import { Field, inputClass, MutationError, SetupSection } from './SetupParts'

function TutorSelect({ classroom, teachers }: { classroom: Classroom; teachers: StaffMember[] }) {
  const setTutor = useSetTutor()
  return (
    <div className="flex flex-col gap-1">
      <select
        aria-label={`Tutor de ${classroomLabel(classroom)}`}
        value={classroom.tutor?.id ?? ''}
        disabled={setTutor.isPending}
        onChange={(event) =>
          setTutor.mutate({
            id: classroom.id,
            tutor_id: event.target.value ? Number(event.target.value) : null,
          })
        }
        className={inputClass}
      >
        <option value="">Sin tutor</option>
        {teachers.map((teacher) => (
          <option key={teacher.id} value={teacher.id}>
            {teacher.full_name}
          </option>
        ))}
      </select>
      <MutationError error={setTutor.error} />
    </div>
  )
}

export function ClassroomsSection() {
  const classrooms = useClassrooms()
  const staff = useStaff()
  const create = useCreateClassroom()
  const [year, setYear] = useState(new Date().getFullYear())
  const [grade, setGrade] = useState(1)
  const [section, setSection] = useState('A')
  const ids = { year: useId(), grade: useId(), section: useId() }
  const teachers = (staff.data ?? []).filter(
    (member) => member.role === 'TEACHER' && member.is_active,
  )

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    create.mutate({ year, grade, section })
  }

  return (
    <SetupSection
      title="Aulas"
      description="Cada aula tiene un tutor: es quien hace el seguimiento semanal y revisa las recomendaciones."
      form={
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <Field label="Año" htmlFor={ids.year}>
            <input
              id={ids.year}
              type="number"
              min={2020}
              max={2100}
              value={year}
              onChange={(event) => setYear(Number(event.target.value))}
              className={`${inputClass} w-28`}
            />
          </Field>
          <Field label="Grado" htmlFor={ids.grade}>
            <select
              id={ids.grade}
              value={grade}
              onChange={(event) => setGrade(Number(event.target.value))}
              className={inputClass}
            >
              {[1, 2, 3, 4, 5, 6].map((value) => (
                <option key={value} value={value}>
                  {value}°
                </option>
              ))}
            </select>
          </Field>
          <Field label="Sección" htmlFor={ids.section}>
            <input
              id={ids.section}
              maxLength={2}
              value={section}
              onChange={(event) => setSection(event.target.value.toUpperCase())}
              className={`${inputClass} w-20`}
            />
          </Field>
          <Button type="submit" pending={create.isPending} disabled={!section.trim()}>
            Agregar aula
          </Button>
          <div className="basis-full">
            <MutationError error={create.error} />
          </div>
        </form>
      }
    >
      {classrooms.data && classrooms.data.length > 0 && (
        <Table caption="Aulas del colegio">
          <TableHead>
            <tr>
              <TableHeaderCell>Aula</TableHeaderCell>
              <TableHeaderCell>Año</TableHeaderCell>
              <TableHeaderCell className="text-right">Estudiantes</TableHeaderCell>
              <TableHeaderCell>Tutor</TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {classrooms.data.map((classroom) => (
              <TableRow key={classroom.id}>
                <TableCell className="font-bold">{classroomLabel(classroom)}</TableCell>
                <TableCell className="tabular-nums">{classroom.year}</TableCell>
                <TableCell className="text-right tabular-nums">{classroom.student_count}</TableCell>
                <TableCell>
                  <TutorSelect classroom={classroom} teachers={teachers} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </SetupSection>
  )
}
