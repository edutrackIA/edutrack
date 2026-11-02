import { useId, useState, type FormEvent } from 'react'
import { formatDate } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { usePeriods, type Period } from '../../periods/api'
import { useCreatePeriod, useUpdatePeriod } from '../api'
import { Field, inputClass, MutationError, SetupSection } from './SetupParts'

function PeriodRow({ period }: { period: Period }) {
  const update = useUpdatePeriod()
  const [editing, setEditing] = useState(false)
  const [start, setStart] = useState(period.start_date)
  const [end, setEnd] = useState(period.end_date)

  if (!editing) {
    return (
      <TableRow>
        <TableCell className="font-bold">{period.label}</TableCell>
        <TableCell>{formatDate(period.start_date)}</TableCell>
        <TableCell>{formatDate(period.end_date)}</TableCell>
        <TableCell className="text-ink-soft">{period.has_grades ? 'Con notas' : 'Sin notas'}</TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" onClick={() => setEditing(true)}>
            Cambiar fechas<span className="sr-only"> de {period.label}</span>
          </Button>
        </TableCell>
      </TableRow>
    )
  }
  return (
    <TableRow>
      <TableCell className="font-bold">{period.label}</TableCell>
      <TableCell>
        <input
          type="date"
          aria-label={`Inicio de ${period.label}`}
          value={start}
          onChange={(event) => setStart(event.target.value)}
          className={inputClass}
        />
      </TableCell>
      <TableCell>
        <input
          type="date"
          aria-label={`Fin de ${period.label}`}
          value={end}
          onChange={(event) => setEnd(event.target.value)}
          className={inputClass}
        />
      </TableCell>
      <TableCell colSpan={2}>
        <div className="flex flex-wrap justify-end gap-2">
          <Button
            pending={update.isPending}
            onClick={() =>
              update.mutate(
                { id: period.id, start_date: start, end_date: end },
                { onSuccess: () => setEditing(false) },
              )
            }
          >
            Guardar
          </Button>
          <Button variant="ghost" onClick={() => setEditing(false)}>
            Cancelar
          </Button>
        </div>
        <MutationError error={update.error} />
      </TableCell>
    </TableRow>
  )
}

export function PeriodsSection() {
  const periods = usePeriods()
  const create = useCreatePeriod()
  const [year, setYear] = useState(new Date().getFullYear())
  const [bimester, setBimester] = useState(1)
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const ids = { year: useId(), bimester: useId(), start: useId(), end: useId() }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    create.mutate(
      { year, bimester, start_date: start, end_date: end },
      {
        onSuccess: () => {
          setStart('')
          setEnd('')
          setBimester((value) => Math.min(value + 1, 4))
        },
      },
    )
  }

  return (
    <SetupSection
      title="Bimestres"
      description="Las fechas de cada bimestre definen qué notas y asistencia se evalúan juntas."
      form={
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
          <Field label="Año" htmlFor={ids.year}>
            <input
              id={ids.year}
              type="number"
              min={2020}
              max={2100}
              value={year}
              onChange={(event) => setYear(Number(event.target.value))}
              className={`${inputClass} w-28`}
            />
          </Field>
          <Field label="Bimestre" htmlFor={ids.bimester}>
            <select
              id={ids.bimester}
              value={bimester}
              onChange={(event) => setBimester(Number(event.target.value))}
              className={inputClass}
            >
              {[1, 2, 3, 4].map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </Field>
          <Field label="Inicio" htmlFor={ids.start}>
            <input id={ids.start} type="date" required value={start} onChange={(event) => setStart(event.target.value)} className={inputClass} />
          </Field>
          <Field label="Fin" htmlFor={ids.end}>
            <input id={ids.end} type="date" required value={end} onChange={(event) => setEnd(event.target.value)} className={inputClass} />
          </Field>
          <Button type="submit" pending={create.isPending} disabled={!start || !end}>
            Agregar bimestre
          </Button>
          <div className="basis-full">
            <MutationError error={create.error} />
          </div>
        </form>
      }
    >
      {periods.data && periods.data.length > 0 && (
        <Table caption="Bimestres del colegio">
          <TableHead>
            <tr>
              <TableHeaderCell>Bimestre</TableHeaderCell>
              <TableHeaderCell>Inicio</TableHeaderCell>
              <TableHeaderCell>Fin</TableHeaderCell>
              <TableHeaderCell>Notas</TableHeaderCell>
              <TableHeaderCell>
                <span className="sr-only">Acciones</span>
              </TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {periods.data.map((period) => (
              <PeriodRow key={period.id} period={period} />
            ))}
          </TableBody>
        </Table>
      )}
    </SetupSection>
  )
}
