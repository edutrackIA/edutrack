import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { byRiskThenName } from '../../../shared/lib/risk'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import type { RecommendationStatus } from '../../students/types'
import { useRecommendationQueue, type ReviewItem } from '../api'
import { RecommendationEditor, type Notice } from '../components/RecommendationEditor'

const byPriority = byRiskThenName<ReviewItem>(
  (item) => item.student.risk_level,
  (item) => item.student.full_name,
)

const TABS: { value: RecommendationStatus; label: string; empty: string }[] = [
  { value: 'PENDING_REVIEW', label: 'Por revisar', empty: 'No tienes recomendaciones por revisar' },
  { value: 'APPROVED', label: 'Aprobadas', empty: 'Aún no hay recomendaciones aprobadas' },
  { value: 'DISCARDED', label: 'Descartadas', empty: 'No hay recomendaciones descartadas' },
]

export default function RecommendationsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const status = (TABS.find((tab) => tab.value === searchParams.get('estado'))?.value ??
    'PENDING_REVIEW') as RecommendationStatus
  const queue = useRecommendationQueue(status)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [notice, setNotice] = useState<Notice | null>(null)

  const items = [...(queue.data ?? [])].sort(byPriority)
  const selected = items.find((item) => item.id === selectedId) ?? items[0]
  const tab = TABS.find((item) => item.value === status)!

  function changeTab(value: RecommendationStatus) {
    setSearchParams({ estado: value }, { replace: true })
    setSelectedId(null)
    setNotice(null)
  }

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title="Recomendaciones"
        description="Revisa las sugerencias antes de que lleguen a las familias."
        actions={
          <div role="group" aria-label="Estado de las recomendaciones" className="flex gap-1">
            {TABS.map((option) => (
              <button
                key={option.value}
                type="button"
                aria-pressed={status === option.value}
                onClick={() => changeTab(option.value)}
                className={`rounded-md px-3 py-1.5 text-sm ${
                  status === option.value
                    ? 'bg-accent-tint font-bold text-accent-strong'
                    : 'text-ink-soft hover:text-ink'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        }
      />

      <div role="status" aria-live="polite" className="shrink-0">
        {notice && (
          <p
            className={`mb-4 rounded-md border px-4 py-3 ${
              notice.tone === 'success'
                ? 'border-risk-low/30 bg-risk-low-bg text-risk-low'
                : 'border-risk-medium/30 bg-risk-medium-bg text-risk-medium'
            }`}
          >
            {notice.text}
          </p>
        )}
      </div>

      {queue.isPending && <LoadingState label="Cargando recomendaciones…" />}
      {queue.isError && <ErrorMessage>{messageFor(queue.error)}</ErrorMessage>}
      {queue.data && items.length === 0 && (
        <EmptyState
          title={tab.empty}
          description="Las recomendaciones se generan cuando el área de análisis evalúa un bimestre."
        />
      )}

      {selected && (
        <div className="grid gap-6 lg:min-h-0 lg:flex-1 lg:grid-cols-[19rem_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)]">
          <nav aria-label={tab.label} className="lg:min-h-0 lg:overflow-y-auto">
            <ul className="flex flex-col gap-2">
              {items.map((item) => {
                const active = item.id === selected.id
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      aria-current={active ? 'true' : undefined}
                      onClick={() => {
                        setSelectedId(item.id)
                        setNotice(null)
                      }}
                      className={`w-full rounded-lg border px-4 py-3 text-left ${
                        active
                          ? 'border-accent bg-accent-tint'
                          : 'border-rule bg-surface hover:border-accent'
                      }`}
                    >
                      <span className="block font-bold text-ink">{item.student.full_name}</span>
                      <span className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-soft">
                        {item.student.classroom}
                        {item.student.risk_level && <RiskBadge level={item.student.risk_level} />}
                        <span>{formatDate(item.created_at)}</span>
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </nav>
          <div className="rounded-xl border border-rule bg-surface p-6 lg:min-h-0 lg:overflow-y-auto">
            <RecommendationEditor
              key={selected.id}
              recommendation={selected}
              onDone={(message) => {
                setNotice(message)
                setSelectedId(null)
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
