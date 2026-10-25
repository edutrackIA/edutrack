import { useState } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate, formatPercent } from '../../../shared/lib/format'
import { byRiskThenName } from '../../../shared/lib/risk'
import { Button } from '../../../shared/ui/Button'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { RiskBadge } from '../../../shared/ui/RiskBadge'
import { StudentQuickView } from '../../students/components/StudentQuickView'
import type { StudentReference } from '../../students/types'
import { useAlerts, useMarkAlertRead, useUnreadAlertsCount, type Alert } from '../api'

const byPriority = byRiskThenName<Alert>(
  (alert) => alert.level,
  (alert) => alert.student.full_name,
)

function AlertRow({
  alert,
  onOpenStudent,
}: {
  alert: Alert
  onOpenStudent: (student: StudentReference) => void
}) {
  const markRead = useMarkAlertRead()
  const { student } = alert

  return (
    <li
      className={`flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-rule py-4 pl-4 last:border-b-0 ${
        alert.is_read ? 'border-l-4 border-l-transparent' : 'border-l-4 border-l-accent'
      }`}
    >
      <RiskBadge level={alert.level} />
      <div className="min-w-0 flex-1">
        <button
          type="button"
          onClick={() =>
            onOpenStudent({
              student_id: student.id,
              full_name: student.full_name,
              code: student.code,
              classroom: student.classroom,
            })
          }
          className="text-left font-bold text-ink hover:text-accent hover:underline"
        >
          {student.full_name}
        </button>
        <p className="text-sm text-ink-soft">
          {student.classroom}
          {student.probability !== null && `, ${formatPercent(student.probability)} de probabilidad`}
          {`, ${formatDate(alert.created_at)}`}
        </p>
      </div>
      {alert.is_read ? (
        <span className="text-sm text-ink-soft">Leída</span>
      ) : (
        <Button
          variant="ghost"
          pending={markRead.isPending}
          onClick={() => markRead.mutate(alert.id)}
        >
          Marcar como leída
          <span className="sr-only"> la alerta de {student.full_name}</span>
        </Button>
      )}
    </li>
  )
}

export default function AlertsPage() {
  const [unreadOnly, setUnreadOnly] = useState(true)
  const alerts = useAlerts(unreadOnly)
  const unread = useUnreadAlertsCount(true)
  const [selected, setSelected] = useState<StudentReference | null>(null)
  const items = [...(alerts.data?.items ?? [])].sort(byPriority)

  return (
    <div className="flex flex-col lg:h-full">
      <PageHeader
        className="mb-5 shrink-0"
        title="Alertas"
        description="Estudiantes de tus aulas que pasaron a riesgo moderado o alto."
        actions={
          <div role="group" aria-label="Mostrar alertas" className="flex gap-1">
            {[
              { value: true, label: `Sin leer${unread.data ? ` (${unread.data})` : ''}` },
              { value: false, label: 'Todas' },
            ].map((option) => (
              <button
                key={option.label}
                type="button"
                aria-pressed={unreadOnly === option.value}
                onClick={() => setUnreadOnly(option.value)}
                className={`rounded-md px-3 py-1.5 text-sm ${
                  unreadOnly === option.value
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

      {alerts.isPending && <LoadingState label="Cargando alertas…" />}
      {alerts.isError && <ErrorMessage>{messageFor(alerts.error)}</ErrorMessage>}
      {alerts.data && items.length === 0 && (
        <EmptyState
          title={unreadOnly ? 'No tienes alertas sin leer' : 'Aún no tienes alertas'}
          description="Las alertas aparecen cuando una evaluación detecta riesgo moderado o alto en tus aulas."
        />
      )}
      {items.length > 0 && (
        <ul
          aria-label="Alertas"
          className="rounded-xl border border-rule bg-surface pr-4 lg:min-h-0 lg:overflow-y-auto"
        >
          {items.map((alert) => (
            <AlertRow key={alert.id} alert={alert} onOpenStudent={setSelected} />
          ))}
        </ul>
      )}

      <StudentQuickView student={selected} periodId={null} onClose={() => setSelected(null)} />
    </div>
  )
}
