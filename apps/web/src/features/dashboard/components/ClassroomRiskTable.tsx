import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import type { ClassroomRiskSummary } from '../types'

/** Visual proportion only: the exact numbers are in the neighbouring columns. */
function DistributionBar({ classroom }: { classroom: ClassroomRiskSummary }) {
  const total = classroom.evaluated
  if (total === 0) return <span className="text-sm text-ink-soft">Sin evaluar</span>

  const segments = [
    { value: classroom.high, className: 'bg-risk-high-mark' },
    { value: classroom.medium, className: 'bg-risk-medium-mark' },
    { value: classroom.low, className: 'bg-risk-low-mark' },
  ]
  return (
    <div aria-hidden="true" className="flex h-2.5 w-40 overflow-hidden rounded-full bg-rule">
      {segments.map(
        (segment, index) =>
          segment.value > 0 && (
            <span
              key={index}
              className={segment.className}
              style={{ width: `${(segment.value / total) * 100}%` }}
            />
          ),
      )}
    </div>
  )
}

export function ClassroomRiskTable({ classrooms }: { classrooms: ClassroomRiskSummary[] }) {
  return (
    <section aria-labelledby="classrooms-title">
      <h2 id="classrooms-title" className="mb-4 font-figure text-xl font-semibold text-ink">
        Por aula
      </h2>
      <Table caption="Estudiantes por nivel de riesgo en cada aula">
        <TableHead>
          <tr>
            <TableHeaderCell>Aula</TableHeaderCell>
            <TableHeaderCell>Distribución</TableHeaderCell>
            <TableHeaderCell className="text-right">Alto</TableHeaderCell>
            <TableHeaderCell className="text-right">Moderado</TableHeaderCell>
            <TableHeaderCell className="text-right">Bajo</TableHeaderCell>
            <TableHeaderCell className="text-right">Evaluados</TableHeaderCell>
          </tr>
        </TableHead>
        <TableBody>
          {classrooms.map((classroom) => (
            <TableRow key={classroom.classroom_id}>
              <TableCell className="font-bold">{classroom.label}</TableCell>
              <TableCell>
                <DistributionBar classroom={classroom} />
              </TableCell>
              <TableCell className="text-right tabular-nums">{classroom.high}</TableCell>
              <TableCell className="text-right tabular-nums">{classroom.medium}</TableCell>
              <TableCell className="text-right tabular-nums">{classroom.low}</TableCell>
              <TableCell className="text-right tabular-nums text-ink-soft">
                {classroom.evaluated}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </section>
  )
}
