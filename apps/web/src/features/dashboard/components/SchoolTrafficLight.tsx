import { RISK_LABELS, type RiskLevel } from '../../../shared/lib/risk'
import type { DashboardSummary } from '../types'
import { RiskLamp } from './RiskLamp'
import { StudentChips } from './StudentChips'

const LEVELS: RiskLevel[] = ['HIGH', 'MEDIUM', 'LOW']

function studentsLabel(count: number): string {
  return `${count} ${count === 1 ? 'estudiante' : 'estudiantes'}`
}

/**
 * The school's traffic light. The housing spans three equal rows and its lamps are
 * spread evenly, so each lamp always sits in front of its lane, whatever the lane holds.
 */
export function SchoolTrafficLight({ summary }: { summary: DashboardSummary }) {
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

      {LEVELS.map((level) => {
        const count = summary.by_level[level]
        const students = summary.students.filter((student) => student.level === level)
        return (
          <div
            key={level}
            className={`flex min-h-0 flex-col overflow-y-auto ${
              level === 'LOW' ? '' : 'border-b border-rule'
            }`}
          >
            <div className="my-auto py-3">
              <p className="flex items-baseline gap-3">
                <span className="font-figure text-xl font-semibold text-ink">
                  {RISK_LABELS[level]}
                </span>
                <span className="tabular-nums text-ink-soft">{studentsLabel(count)}</span>
              </p>
              {count > 0 && level !== 'LOW' && (
                <div className="mt-3">
                  <StudentChips students={students} />
                </div>
              )}
              {count > 0 && level === 'LOW' && (
                <details className="mt-2">
                  <summary className="cursor-pointer font-bold text-accent">Ver lista</summary>
                  <div className="mt-3">
                    <StudentChips students={students} />
                  </div>
                </details>
              )}
            </div>
          </div>
        )
      })}
    </section>
  )
}
