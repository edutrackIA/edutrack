import { describe, expect, it } from 'vitest'
import { byRiskThenName, type RiskLevel } from './risk'

describe('byRiskThenName', () => {
  it('sorts by priority first and then alphabetically, leaving unevaluated last', () => {
    const students: { name: string; level: RiskLevel | null }[] = [
      { name: 'Ñuñez', level: 'LOW' },
      { name: 'Zapata', level: 'HIGH' },
      { name: 'Ávila', level: null },
      { name: 'Benítez', level: 'MEDIUM' },
      { name: 'Álvarez', level: 'HIGH' },
    ]

    const sorted = [...students].sort(
      byRiskThenName(
        (student) => student.level,
        (student) => student.name,
      ),
    )

    expect(sorted.map((student) => student.name)).toEqual([
      'Álvarez',
      'Zapata',
      'Benítez',
      'Ñuñez',
      'Ávila',
    ])
  })
})
