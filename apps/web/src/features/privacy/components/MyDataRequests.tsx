import { useId, useState, type FormEvent } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { firstName, useChildren } from '../../parent-portal/api'
import {
  KIND_LABELS,
  STATUS_LABELS,
  useCreateDataRequest,
  useDataRequests,
  type DataRequestKind,
} from '../api'

const inputClass = 'rounded-md border border-rule bg-surface px-3 py-2 text-ink'

/** A guardian's data rights requests, from the account page. */
export function MyDataRequests() {
  const children = useChildren()
  const requests = useDataRequests()
  const create = useCreateDataRequest()
  const [studentId, setStudentId] = useState<number | null>(null)
  const [kind, setKind] = useState<DataRequestKind>('ACCESS')
  const [details, setDetails] = useState('')
  const [sent, setSent] = useState(false)
  const ids = { student: useId(), kind: useId(), details: useId() }
  const selected = studentId ?? children.data?.[0]?.id ?? null

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (selected === null) return
    create.mutate(
      { student_id: selected, kind, details: details.trim() },
      {
        onSuccess: () => {
          setDetails('')
          setSent(true)
        },
      },
    )
  }

  return (
    <section aria-labelledby="requests-title" className="mt-10">
      <h2 id="requests-title" className="font-figure text-xl font-semibold text-ink">
        Mis datos
      </h2>
      <p className="mt-1 max-w-2xl text-ink-soft">
        Puedes pedir acceso, corrección, eliminación u oposición al uso de los datos. El colegio
        responde dentro del plazo legal.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 flex max-w-2xl flex-col gap-4 rounded-xl border border-rule bg-surface p-5">
        <div className="flex flex-wrap gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor={ids.student} className="font-bold text-ink">Sobre</label>
            <select id={ids.student} value={selected ?? ''} onChange={(event) => setStudentId(Number(event.target.value))} className={inputClass}>
              {children.data?.map((child) => (
                <option key={child.id} value={child.id}>
                  {firstName(child.full_name)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={ids.kind} className="font-bold text-ink">Tipo de solicitud</label>
            <select id={ids.kind} value={kind} onChange={(event) => setKind(event.target.value as DataRequestKind)} className={inputClass}>
              {(Object.keys(KIND_LABELS) as DataRequestKind[]).map((value) => (
                <option key={value} value={value}>
                  {KIND_LABELS[value].label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <p className="text-sm text-ink-soft">{KIND_LABELS[kind].help}</p>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.details} className="font-bold text-ink">Detalle</label>
          <textarea id={ids.details} rows={3} maxLength={2000} value={details} onChange={(event) => setDetails(event.target.value)} className={`${inputClass} resize-y`} />
        </div>
        {create.isError && <ErrorMessage>{messageFor(create.error)}</ErrorMessage>}
        <div role="status" aria-live="polite">
          {sent && <p className="text-risk-low">Solicitud enviada. Te avisaremos por correo cuando el colegio responda.</p>}
        </div>
        <div>
          <Button type="submit" pending={create.isPending} disabled={selected === null || details.trim().length < 10}>
            Enviar solicitud
          </Button>
        </div>
      </form>

      {requests.data && requests.data.length > 0 && (
        <ul aria-label="Mis solicitudes" className="mt-6 max-w-2xl divide-y divide-rule">
          {requests.data.map((request) => (
            <li key={request.id} className="py-3">
              <p className="flex flex-wrap justify-between gap-2">
                <span className="font-bold text-ink">
                  {KIND_LABELS[request.kind].label}, {request.student_name}
                </span>
                <span className="text-sm text-ink-soft">
                  {STATUS_LABELS[request.status]}, {formatDate(request.created_at)}
                </span>
              </p>
              {request.response && <p className="mt-1 text-ink">Respuesta: {request.response}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
