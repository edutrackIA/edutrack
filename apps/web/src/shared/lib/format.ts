const LOCALE = 'es-PE'

const scoreFormat = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})
const percentFormat = new Intl.NumberFormat(LOCALE, { style: 'percent', maximumFractionDigits: 0 })
const dateFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'long', year: 'numeric' })
const dayMonthFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'long' })
const weekdayFormat = new Intl.DateTimeFormat(LOCALE, {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/

/**
 * "2026-10-26" is a calendar date, not an instant. Parsing it with `new Date()` would
 * read it as UTC midnight and show the previous day in Peru (UTC-5).
 */
export function parseDate(value: string | Date): Date {
  if (value instanceof Date) return value
  const match = DATE_ONLY.exec(value)
  if (match) return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  return new Date(value)
}

export function formatScore(value: number): string {
  return scoreFormat.format(value)
}

export function formatPercent(value: number): string {
  return percentFormat.format(value)
}

export function formatDate(value: string | Date): string {
  return dateFormat.format(parseDate(value))
}

export function formatDayMonth(value: string | Date): string {
  return dayMonthFormat.format(parseDate(value))
}

export function formatWeekday(value: string | Date): string {
  return weekdayFormat.format(parseDate(value))
}
