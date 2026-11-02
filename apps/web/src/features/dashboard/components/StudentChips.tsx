import type { StudentRisk } from '../types'

export function StudentChips({
  students,
  showClassroom = true,
  onSelect,
}: {
  students: StudentRisk[]
  showClassroom?: boolean
  onSelect: (student: StudentRisk) => void
}) {
  return (
    <ul className="flex flex-wrap gap-2">
      {students.map((student) => (
        <li key={student.student_id}>
          <button
            type="button"
            onClick={() => onSelect(student)}
            className="rounded-md border border-rule bg-surface px-2.5 py-1 text-left text-sm text-ink hover:border-accent hover:text-accent"
          >
            {student.full_name}
            {showClassroom && <span className="ml-2 text-ink-soft">{student.classroom}</span>}
          </button>
        </li>
      ))}
    </ul>
  )
}
