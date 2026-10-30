import { useMutation } from '@tanstack/react-query'
import { useId, useState } from 'react'
import { apiRequest } from '../../../shared/api/client'
import { Button } from '../../../shared/ui/Button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../../../shared/ui/Table'
import { useClassrooms } from '../../classrooms/api'
import { Field, inputClass, MutationError, SetupSection } from './SetupParts'

interface PromotionPlan {
  year: number
  moves: { source: string; target: string; students: number }[]
  promoted: number
  repeating: number
  graduated: number
  unknown_codes: string[]
  applied: boolean
}

interface PromotionRequest {
  year: number
  final_grade: number
  repeating_codes: string[]
  dry_run: boolean
}

function usePromotion() {
  return useMutation({
    mutationFn: ({ year, ...body }: PromotionRequest) =>
      apiRequest<PromotionPlan>(`/school-years/${year}/promotion`, { method: 'POST', body }),
  })
}

function codes(text: string): string[] {
  return text
    .split(/[\s,;]+/)
    .map((code) => code.trim())
    .filter(Boolean)
}

/** Closes a school year: everyone moves up a grade, repeaters stay, the last grade graduates. */
export function YearClosingSection() {
  const classrooms = useClassrooms()
  const years = [...new Set((classrooms.data ?? []).map((item) => item.year))].sort((a, b) => b - a)
  const [year, setYear] = useState<number | null>(null)
  const [finalGrade, setFinalGrade] = useState(5)
  const [repeating, setRepeating] = useState('')
  const [confirming, setConfirming] = useState(false)
  const preview = usePromotion()
  const apply = usePromotion()
  const ids = { year: useId(), grade: useId(), repeating: useId() }
  const selectedYear = year ?? years[0] ?? null

  const request = (dryRun: boolean): PromotionRequest | null =>
    selectedYear === null
      ? null
      : { year: selectedYear, final_grade: finalGrade, repeating_codes: codes(repeating), dry_run: dryRun }

  function reset() {
    preview.reset()
    apply.reset()
    setConfirming(false)
  }

  const plan = apply.data ?? preview.data

  return (
    <SetupSection
      title="Cierre de año"
      description="Pasa a todos al grado siguiente en aulas del nuevo año. Quienes repiten se quedan en su grado y los del último grado egresan. Primero revisa el plan; nada cambia hasta que lo apliques."
      form={
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end gap-4">
            <Field label="Año que se cierra" htmlFor={ids.year}>
              <select
                id={ids.year}
                value={selectedYear ?? ''}
                onChange={(event) => {
                  setYear(Number(event.target.value))
                  reset()
                }}
                className={inputClass}
              >
                {years.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </Field>
            <Field label="Último grado del colegio" htmlFor={ids.grade}>
              <select
                id={ids.grade}
                value={finalGrade}
                onChange={(event) => {
                  setFinalGrade(Number(event.target.value))
                  reset()
                }}
                className={inputClass}
              >
                {[1, 2, 3, 4, 5, 6].map((value) => (
                  <option key={value} value={value}>
                    {value}°
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <Field label="Códigos de quienes repiten el grado (opcional)" htmlFor={ids.repeating}>
            <textarea
              id={ids.repeating}
              rows={3}
              value={repeating}
              placeholder="20260007, 20260015"
              onChange={(event) => {
                setRepeating(event.target.value)
                reset()
              }}
              className={`${inputClass} max-w-xl resize-y font-mono`}
            />
          </Field>
          <div>
            <Button
              variant="secondary"
              pending={preview.isPending}
              disabled={selectedYear === null}
              onClick={() => {
                const body = request(true)
                if (body) preview.mutate(body)
              }}
            >
              Ver plan
            </Button>
          </div>
          <MutationError error={preview.error ?? apply.error} />
        </div>
      }
    >
      {plan && (
        <section aria-labelledby="plan-title" className="flex flex-col gap-4">
          <h3 id="plan-title" className="font-figure text-lg font-semibold text-ink">
            {plan.applied ? `Año ${plan.year} cerrado` : `Plan de cierre de ${plan.year}`}
          </h3>
          <p className={plan.applied ? 'text-risk-low' : 'text-ink'}>
            {plan.promoted} pasan de grado, {plan.repeating} repiten y {plan.graduated} egresan.
          </p>
          {plan.unknown_codes.length > 0 && (
            <p className="rounded-md bg-risk-medium-bg px-3 py-2 text-risk-medium">
              Estos códigos no corresponden a estudiantes matriculados en {plan.year}:{' '}
              {plan.unknown_codes.join(', ')}.
            </p>
          )}
          {plan.moves.length > 0 && (
            <Table caption="Movimientos del cierre de año">
              <TableHead>
                <tr>
                  <TableHeaderCell>Desde</TableHeaderCell>
                  <TableHeaderCell>Hacia</TableHeaderCell>
                  <TableHeaderCell className="text-right">Estudiantes</TableHeaderCell>
                </tr>
              </TableHead>
              <TableBody>
                {plan.moves.map((move) => (
                  <TableRow key={`${move.source}-${move.target}`}>
                    <TableCell>{move.source}</TableCell>
                    <TableCell className="font-bold">{move.target}</TableCell>
                    <TableCell className="text-right tabular-nums">{move.students}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {!plan.applied && plan.moves.length > 0 && (
            <div className="flex flex-wrap items-center gap-3">
              {confirming ? (
                <>
                  <span className="text-ink">
                    Esto mueve a todos los estudiantes de {plan.year}. ¿Aplicar?
                  </span>
                  <Button
                    pending={apply.isPending}
                    onClick={() => {
                      const body = request(false)
                      if (body) apply.mutate(body)
                    }}
                  >
                    Sí, cerrar el año
                  </Button>
                  <Button variant="ghost" onClick={() => setConfirming(false)}>
                    Cancelar
                  </Button>
                </>
              ) : (
                <Button onClick={() => setConfirming(true)}>Aplicar cierre de año</Button>
              )}
            </div>
          )}
          {plan.applied && (
            <p className="text-sm text-ink-soft">
              Se crearon las aulas del nuevo año sin tutor: asígnalos en la sección Aulas.
            </p>
          )}
        </section>
      )}
    </SetupSection>
  )
}
