import { useId, useState } from 'react'
import { RISK_LABELS, type RiskLevel } from '../../../shared/lib/risk'
import type { DashboardSummary, StudentRisk } from '../types'
import { RiskLamp } from './RiskLamp'
import { StudentChips } from './StudentChips'

const LEVELS: RiskLevel[] = ['HIGH', 'MEDIUM', 'LOW']

function studentsLabel(count: number): string {
  return `${count} ${count === 1 ? 'estudiante' : 'estudiantes'}`
}

/** One lane: the title stays in place and only the names scroll. */
function Lane({
  level,
  count,
  students,
  onSelectStudent,
}: {
  level: RiskLevel
  count: number
  students: StudentRisk[]
  onSelectStudent: (student: StudentRisk) => void
}) {
  const collapsible = level === 'LOW'
  const [expanded, setExpanded] = useState(!collapsible)
  const listId = useId()

  return (
    <div
      className={`flex min-h-0 flex-col justify-center py-3 ${
        level === 'LOW' ? '' : 'border-b border-rule'
      }`}
    >
      <div className="flex shrink-0 flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-figure text-xl font-semibold text-ink">{RISK_LABELS[level]}</span>
        <span className="tabular-nums text-ink-soft">{studentsLabel(count)}</span>
        {collapsible && count > 0 && (
          <button
            type="button"
            aria-expanded={expanded}
            aria-controls={listId}
            onClick={() => setExpanded(!expanded)}
            className="font-bold text-accent hover:text-accent-strong"
          >
            {expanded ? 'Ocultar lista' : 'Ver lista'}
          </button>
        )}
      </div>
      {count > 0 && expanded && (
        <div id={listId} className="mt-3 min-h-0 overflow-y-auto pr-1">
          <StudentChips students={students} onSelect={onSelectStudent} />
        </div>
      )}
    </div>
  )
}

/**
 * The school's traffic light. The housing spans three equal rows and its lamps are
 * spread evenly, so each lamp always sits in front of its lane, whatever the lane holds.
 */
export function SchoolTrafficLight({
  summary,
  onSelectStudent,
}: {
  summary: DashboardSummary
  onSelectStudent: (student: StudentRisk) => void
}) {
  return (
    <section
      aria-labelledby="traffic-light-title"
      className="relative grid h-[30rem] grid-cols-[7rem_minmax(0,1fr)] grid-rows-3 gap-x-6 pb-5 lg:h-full lg:min-h-[22rem]"
    >
      <h2 id="traffic-light-title" className="sr-only">
        Semáforo del colegio
      </h2>

      <div
        aria-hidden="true"
        className="row-span-3 flex flex-col items-center justify-around rounded-3xl bg-housing py-4"
      >
        {LEVELS.map((level) => (
          <RiskLamp key={level} level={level} lit={summary.by_level[level] > 0} />
        ))}
      </div>
      <div aria-hidden="true" className="absolute bottom-0 left-[3rem] h-5 w-4 bg-housing" />

      {LEVELS.map((level) => (
        <Lane
          key={level}
          level={level}
          count={summary.by_level[level]}
          students={summary.students.filter((student) => student.level === level)}
          onSelectStudent={onSelectStudent}
        />
      ))}
    </section>
  )
}
