import { useId, useState } from 'react'
import { EmptyState, LoadingState } from '../../../shared/ui/Feedback'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { periodOptionLabel, usePeriods } from '../../periods/api'
import {
  periodFor,
  todayValue,
  useBehaviorSheet,
  useSaveBehavior,
  type BehaviorSheet,
  type TeachingClassroom,
} from '../api'
import { SaveBar, selectClass } from './SheetParts'

const RATINGS = [
  { value: 5, label: '5, excelente' },
  { value: 4, label: '4, buena' },
  { value: 3, label: '3, regular' },
  { value: 2, label: '2, necesita mejorar' },
  { value: 1, label: '1, preocupante' },
]

interface Draft {
  rating: number | null
  notes: string
}

function Sheet({ sheet }: { sheet: BehaviorSheet }) {
  const save = useSaveBehavior(sheet.classroom_id)
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [saved, setSaved] = useState(false)

  const valueOf = (row: BehaviorSheet['rows'][number]): Draft =>
    drafts[row.student_id] ?? { rating: row.rating, notes: row.notes ?? '' }
  const changed = sheet.rows.filter((row) => {
    const draft = drafts[row.student_id]
    return draft && (draft.rating !== row.rating || draft.notes.trim() !== (row.notes ?? ''))
  })

  function update(row: BehaviorSheet['rows'][number], patch: Partial<Draft>) {
    setSaved(false)
    setDrafts({ ...drafts, [row.student_id]: { ...valueOf(row), ...patch } })
  }

  function handleSave() {
    save.mutate(
      {
        period_id: sheet.period_id,
        ratings: changed.map((row) => ({
          student_id: row.student_id,
          rating: drafts[row.student_id].rating,
          notes: drafts[row.student_id].notes.trim() || null,
        })),
      },
      {
        onSuccess: () => {
          setDrafts({})
          setSaved(true)
        },
      },
    )
  }

  return (
    <>
      <div className="lg:min-h-0 lg:overflow-y-auto">
        <Table caption="Conducta del bimestre">
          <TableHead>
            <tr>
              <TableHeaderCell>Estudiante</TableHeaderCell>
              <TableHeaderCell>Conducta</TableHeaderCell>
              <TableHeaderCell>Observación (opcional)</TableHeaderCell>
            </tr>
          </TableHead>
          <TableBody>
            {sheet.rows.map((row) => {
              const value = valueOf(row)
              return (
                <TableRow key={row.student_id}>
                  <TableCell className="font-bold">{row.full_name}</TableCell>
                  <TableCell>
                    <select
                      aria-label={`Conducta de ${row.full_name}`}
                      value={value.rating ?? ''}
                      onChange={(event) =>
                        update(row, { rating: event.target.value ? Number(event.target.value) : null })
                      }
                      className={selectClass}
                    >
                      <option value="">Sin registrar</option>
                      {RATINGS.map((rating) => (
                        <option key={rating.value} value={rating.value}>
                          {rating.label}
                        </option>
                      ))}
                    </select>
                  </TableCell>
                  <TableCell>
                    <input
                      aria-label={`Observación de ${row.full_name}`}
                      maxLength={500}
                      value={value.notes}
                      onChange={(event) => update(row, { notes: event.target.value })}
                      className={`${selectClass} w-full min-w-48`}
                    />
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
      <SaveBar
        label="Guardar conducta"
        changes={changed.length}
        pending={save.isPending}
        saved={saved}
        error={save.error}
        onSave={handleSave}
      />
    </>
  )
}

export function BehaviorSheetView({ classrooms }: { classrooms: TeachingClassroom[] }) {
  const periods = usePeriods()
  const tutored = classrooms.filter((item) => item.is_tutor)
  const [classroomId, setClassroomId] = useState<number | null>(null)
  const [periodId, setPeriodId] = useState<number | null>(null)
  const ids = { classroom: useId(), period: useId() }
  const selected = tutored.find((item) => item.classroom_id === classroomId) ?? tutored[0]
  const period =
    periods.data?.find((item) => item.id === periodId) ?? periodFor(periods.data, todayValue())
  const sheet = useBehaviorSheet(selected?.classroom_id ?? null, period?.id ?? null)

  if (tutored.length === 0) {
    return <EmptyState title="No eres tutor de ningún aula" description="La conducta la registra el tutor del aula." />
  }

  return (
    <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1">
      <div className="flex shrink-0 flex-wrap gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.classroom} className="text-sm font-bold text-ink">
            Aula
          </label>
          <select id={ids.classroom} value={selected?.classroom_id} onChange={(event) => setClassroomId(Number(event.target.value))} className={selectClass}>
            {tutored.map((item) => (
              <option key={item.classroom_id} value={item.classroom_id}>
                {item.classroom} ({item.year})
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={ids.period} className="text-sm font-bold text-ink">
            Bimestre
          </label>
          <select id={ids.period} value={period?.id ?? ''} onChange={(event) => setPeriodId(Number(event.target.value))} className={selectClass}>
            {periods.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {periodOptionLabel(item)}
              </option>
            ))}
          </select>
        </div>
      </div>
      {sheet.isPending && <LoadingState />}
      {sheet.data && <Sheet key={`${sheet.data.classroom_id}-${sheet.data.period_id}`} sheet={sheet.data} />}
    </div>
  )
}
