import { describe, expect, it } from 'vitest'
import { formatDate, formatDayMonth, parseDate } from './format'

describe('dates', () => {
  it('reads calendar dates as local days, never shifting them', () => {
    const day = parseDate('2026-10-26')

    expect([day.getFullYear(), day.getMonth(), day.getDate()]).toEqual([2026, 9, 26])
    expect(formatDate('2026-06-12')).toContain('12')
    expect(formatDayMonth('2026-10-31')).toContain('31')
  })
})
