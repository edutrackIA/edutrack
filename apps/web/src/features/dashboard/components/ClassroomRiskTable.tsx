import { Fragment, useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import type { ClassroomRiskSummary, StudentRisk } from '../types'
import { MiniTrafficLight } from './MiniTrafficLight'
import { StudentChips } from './StudentChips'

export function ClassroomRiskTable({
  classrooms,
  students,
  onSelectStudent,
}: {
  classrooms: ClassroomRiskSummary[]
  students: StudentRisk[]
  onSelectStudent: (student: StudentRisk) => void
}) {
  const [openId, setOpenId] = useState<number | null>(null)

  return (
    <section aria-labelledby="classrooms-title" className="flex flex-col lg:min-h-0">
      <h2 id="classrooms-title" className="mb-3 shrink-0 font-figure text-xl font-semibold text-ink">
        Por aula
      </h2>
      <div className="lg:min-h-0 lg:overflow-y-auto">
        <Table caption="Semáforo de cada aula">
        <TableHead>
          <tr>
            <TableHeaderCell>Aula</TableHeaderCell>
            <TableHeaderCell>Semáforo</TableHeaderCell>
            <TableHeaderCell className="text-right">Evaluados</TableHeaderCell>
          </tr>
        </TableHead>
        <TableBody>
          {classrooms.map((classroom) => {
            const open = openId === classroom.classroom_id
            const panelId = `aula-${classroom.classroom_id}`
            const atRisk = students.filter(
              (student) => student.classroom_id === classroom.classroom_id && student.level !== 'LOW',
            )
            return (
              <Fragment key={classroom.classroom_id}>
                <TableRow>
                  <TableCell>
                    <button
                      type="button"
                      aria-expanded={open}
                      aria-controls={panelId}
                      onClick={() => setOpenId(open ? null : classroom.classroom_id)}
                      className="flex items-center gap-2 font-bold text-ink hover:text-accent"
                    >
                      <svg
                        aria-hidden="true"
                        viewBox="0 0 10 10"
                        className={`h-2.5 w-2.5 transition-transform ${open ? 'rotate-90' : ''}`}
                      >
                        <path d="M3 1 8 5 3 9Z" fill="currentColor" />
                      </svg>
                      {classroom.label}
                    </button>
                  </TableCell>
                  <TableCell>
                    <MiniTrafficLight classroom={classroom} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-ink-soft">
                    {classroom.evaluated}
                  </TableCell>
                </TableRow>
                {open && (
                  <tr id={panelId}>
                    <td colSpan={3} className="bg-paper px-4 py-4">
                      {atRisk.length > 0 ? (
                        <StudentChips
                          students={atRisk}
                          showClassroom={false}
                          onSelect={onSelectStudent}
                        />
                      ) : (
                        <p className="text-ink-soft">
                          No hay estudiantes en riesgo moderado o alto en esta aula.
                        </p>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </TableBody>
        </Table>
      </div>
    </section>
  )
}
