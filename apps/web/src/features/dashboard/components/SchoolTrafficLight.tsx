import { RISK_LABELS, type RiskLevel } from '../../../shared/lib/risk'
import type { DashboardSummary } from '../types'
import { RiskLamp } from './RiskLamp'
import { StudentChips } from './StudentChips'

const LEVELS: RiskLevel[] = ['HIGH', 'MEDIUM', 'LOW']

const HOUSING_SHAPE: Record<RiskLevel, string> = {
  HIGH: 'rounded-t-2xl pt-4',
  MEDIUM: '',
  LOW: 'rounded-b-2xl pb-4',
}

function studentsLabel(count: number): string {
  return `${count} ${count === 1 ? 'estudiante' : 'estudiantes'}`
}

/**
 * The school's traffic light: one lamp per level, lit when it has students.
 * Moderate and high risk list the students by name; low risk stays collapsed.
 */
export function SchoolTrafficLight({ summary }: { summary: DashboardSummary }) {
  return (
    <section aria-labelledby="traffic-light-title" className="mb-12">
      <h2 id="traffic-light-title" className="sr-only">
        Semáforo del colegio
      </h2>
      <ol>
        {LEVELS.map((level) => {
          const count = summary.by_level[level]
          const students = summary.students.filter((student) => student.level === level)
          return (
            <li key={level} className="flex items-stretch gap-6">
              <div
                className={`flex w-24 shrink-0 justify-center bg-housing px-5 py-2 ${HOUSING_SHAPE[level]}`}
              >
                <RiskLamp level={level} lit={count > 0} />
              </div>
              <div
                className={`min-w-0 flex-1 py-4 ${level === 'LOW' ? '' : 'border-b border-rule'}`}
              >
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
            </li>
          )
        })}
      </ol>
      <div aria-hidden="true" className="ml-[2.625rem] h-6 w-3 bg-housing" />
    </section>
  )
}
