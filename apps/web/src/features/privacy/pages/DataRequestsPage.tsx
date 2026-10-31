import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { EmptyState, ErrorMessage, LoadingState } from '../../../shared/ui/Feedback'
import { Modal } from '../../../shared/ui/Modal'
import { PageHeader } from '../../../shared/ui/PageHeader'
import {
  downloadStudentExport,
  KIND_LABELS,
  STATUS_LABELS,
  useDataRequests,
  useResolveDataRequest,
  type DataRequest,
} from '../api'

function todayValue(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

function ResolveForm({ request, onDone }: { request: DataRequest; onDone: () => void }) {
  const resolve = useResolveDataRequest()
  const [status, setStatus] = useState<'RESOLVED' | 'REJECTED'>('RESOLVED')
  const [response, setResponse] = useState('')
  const responseId = useId()

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    resolve.mutate({ id: request.id, status, response: response.trim() }, { onSuccess: onDone })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <p className="text-ink">{request.details}</p>
      <fieldset className="flex flex-wrap gap-4">
        <legend className="mb-2 font-bold text-ink">Resultado</legend>
        {(['RESOLVED', 'REJECTED'] as const).map((value) => (
          <label key={value} className="flex items-center gap-2">
            <input type="radio" name="status" checked={status === value} onChange={() => setStatus(value)} className="accent-accent" />
            {value === 'RESOLVED' ? 'Atendida' : 'Rechazada'}
          </label>
        ))}
      </fieldset>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={responseId} className="font-bold text-ink">
          Respuesta para la familia
        </label>
        <textarea id={responseId} rows={4} maxLength={2000} value={response} onChange={(event) => setResponse(event.target.value)} className="resize-y rounded-md border border-rule bg-surface px-3 py-2 text-ink" />
        <p className="text-sm text-ink-soft">Se enviará por correo. Si rechazas, explica el motivo.</p>
      </div>
      {resolve.isError && <ErrorMessage>{messageFor(resolve.error)}</ErrorMessage>}
      <div>
        <Button type="submit" pending={resolve.isPending} disabled={response.trim().length < 10}>
          Enviar respuesta
        </Button>
      </div>
    </form>
  )
}

function RequestItem({ request, onResolve }: { request: DataRequest; onResolve: () => void }) {
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const overdue = request.status === 'PENDING' && request.due_date < todayValue()

  return (
    <li className="rounded-xl border border-rule bg-surface p-4">
      <p className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-bold text-ink">
          {KIND_LABELS[request.kind].label}: {request.student_name}
        </span>
        <span className={`text-sm ${overdue ? 'font-bold text-risk-high' : 'text-ink-soft'}`}>
          {request.status === 'PENDING'
            ? `${overdue ? 'Vencida' : 'Responder'} hasta el ${formatDate(request.due_date)}`
            : STATUS_LABELS[request.status]}
        </span>
      </p>
      <p className="mt-1 text-sm text-ink-soft">
        {request.requester_name}, {formatDate(request.created_at)}
      </p>
      <p className="mt-2 text-ink">{request.details}</p>
      {request.response && <p className="mt-2 text-ink-soft">Respuesta: {request.response}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        {request.status === 'PENDING' && (
          <Button variant="secondary" onClick={onResolve}>
            Responder<span className="sr-only"> la solicitud sobre {request.student_name}</span>
          </Button>
        )}
        {request.kind === 'ACCESS' && (
          <Button
            variant="ghost"
            pending={exporting}
            onClick={() => {
              setExporting(true)
              setExportError(null)
              downloadStudentExport(request.student_id)
                .catch((error) => setExportError(messageFor(error)))
                .finally(() => setExporting(false))
            }}
          >
            Descargar expediente
          </Button>
        )}
      </div>
      {request.kind === 'ACCESS' && (
        <p className="mt-2 text-sm text-ink-soft">
          Revisa el expediente antes de entregarlo: incluye notas internas del equipo.
        </p>
      )}
      {exportError && <ErrorMessage>{exportError}</ErrorMessage>}
    </li>
  )
}

/** Direction answers the families' data rights requests within the legal deadline. */
export default function DataRequestsPage() {
  const requests = useDataRequests()
  const [answering, setAnswering] = useState<DataRequest | null>(null)
  const pending = (requests.data ?? []).filter((item) => item.status === 'PENDING')
  const answered = (requests.data ?? []).filter((item) => item.status !== 'PENDING')

  return (
    <>
      <PageHeader
        title="Solicitudes de datos"
        description="Pedidos de acceso, rectificación, cancelación u oposición de las familias (Ley N.° 29733)."
      />
      {requests.isPending && <LoadingState />}
      {requests.isError && <ErrorMessage>{messageFor(requests.error)}</ErrorMessage>}
      {requests.data && requests.data.length === 0 && (
        <EmptyState title="No hay solicitudes" description="Las familias las envían desde su cuenta." />
      )}
      {pending.length > 0 && (
        <section aria-labelledby="pending-title" className="mb-8">
          <h2 id="pending-title" className="mb-3 font-figure text-xl font-semibold text-ink">
            Pendientes ({pending.length})
          </h2>
          <ul className="flex flex-col gap-3">
            {pending.map((request) => (
              <RequestItem key={request.id} request={request} onResolve={() => setAnswering(request)} />
            ))}
          </ul>
        </section>
      )}
      {answered.length > 0 && (
        <section aria-labelledby="answered-title">
          <h2 id="answered-title" className="mb-3 font-figure text-xl font-semibold text-ink">
            Respondidas
          </h2>
          <ul className="flex flex-col gap-3">
            {answered.map((request) => (
              <RequestItem key={request.id} request={request} onResolve={() => undefined} />
            ))}
          </ul>
        </section>
      )}
      <Modal
        open={answering !== null}
        onClose={() => setAnswering(null)}
        title={answering ? `Solicitud de ${KIND_LABELS[answering.kind].label.toLowerCase()}` : ''}
        description={answering?.student_name}
      >
        {answering && <ResolveForm request={answering} onDone={() => setAnswering(null)} />}
      </Modal>
    </>
  )
}
