const LOCALE = 'es-PE'

const scoreFormat = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})
const percentFormat = new Intl.NumberFormat(LOCALE, { style: 'percent', maximumFractionDigits: 0 })
const dateFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'long', year: 'numeric' })

export function formatScore(value: number): string {
  return scoreFormat.format(value)
}

export function formatPercent(value: number): string {
  return percentFormat.format(value)
}

export function formatDate(value: string | Date): string {
  return dateFormat.format(typeof value === 'string' ? new Date(value) : value)
}
