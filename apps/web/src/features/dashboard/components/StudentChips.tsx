import type { StudentRisk } from '../types'

export function StudentChips({
  students,
  showClassroom = true,
}: {
  students: StudentRisk[]
  showClassroom?: boolean
}) {
  return (
    <ul className="flex flex-wrap gap-2">
      {students.map((student) => (
        <li
          key={student.student_id}
          className="rounded-md border border-rule bg-surface px-2.5 py-1 text-sm text-ink"
        >
          {student.full_name}
          {showClassroom && <span className="ml-2 text-ink-soft">{student.classroom}</span>}
        </li>
      ))}
    </ul>
  )
}
