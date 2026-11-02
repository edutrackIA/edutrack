import { useId, useState, type FormEvent, type ReactNode } from 'react'
import { messageFor } from '../../../shared/api/errors'
import { Button } from '../../../shared/ui/Button'
import { ErrorMessage } from '../../../shared/ui/Feedback'
import { useSubmitSurvey } from '../api'

const EDUCATION = [
  ['NONE', 'Sin estudios'],
  ['PRIMARY', 'Primaria'],
  ['SECONDARY', 'Secundaria'],
  ['TECHNICAL', 'Técnica'],
  ['UNIVERSITY', 'Universitaria'],
] as const

function Field({ label, children }: { label: string; children: (id: string) => ReactNode }) {
  const id = useId()
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="font-bold text-ink">
        {label}
      </label>
      {children(id)}
    </div>
  )
}

const inputClass = 'rounded-md border border-rule bg-surface px-3 py-2 text-ink'

function YesNo({ id, value, onChange }: { id: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <select
      id={id}
      value={value ? 'yes' : 'no'}
      onChange={(event) => onChange(event.target.value === 'yes')}
      className={inputClass}
    >
      <option value="yes">Sí</option>
      <option value="no">No</option>
    </select>
  )
}

/** Socio-family survey of the period: the context the risk model uses. */
export function FamilySurveyForm({ studentId, periodId }: { studentId: number; periodId: number }) {
  const submit = useSubmitSurvey(studentId)
  const [studyHours, setStudyHours] = useState(6)
  const [education, setEducation] = useState('SECONDARY')
  const [internet, setInternet] = useState(true)
  const [device, setDevice] = useState(true)
  const [communication, setCommunication] = useState(3)
  const [works, setWorks] = useState(false)
  const [household, setHousehold] = useState(4)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submit.mutate({
      period_id: periodId,
      study_hours_week: studyHours,
      parent_education: education,
      home_internet: internet,
      has_study_device: device,
      family_communication: communication,
      student_works: works,
      household_size: household,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
      <Field label="Horas de estudio en casa por semana">
        {(id) => (
          <input
            id={id}
            type="number"
            min={0}
            max={60}
            value={studyHours}
            onChange={(event) => setStudyHours(Number(event.target.value))}
            className={inputClass}
          />
        )}
      </Field>
      <Field label="Nivel educativo de los padres">
        {(id) => (
          <select
            id={id}
            value={education}
            onChange={(event) => setEducation(event.target.value)}
            className={inputClass}
          >
            {EDUCATION.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        )}
      </Field>
      <Field label="¿Tienen internet en casa?">
        {(id) => <YesNo id={id} value={internet} onChange={setInternet} />}
      </Field>
      <Field label="¿Tiene un dispositivo para estudiar?">
        {(id) => <YesNo id={id} value={device} onChange={setDevice} />}
      </Field>
      <Field label="Comunicación en familia (1 = poca, 5 = mucha)">
        {(id) => (
          <select
            id={id}
            value={communication}
            onChange={(event) => setCommunication(Number(event.target.value))}
            className={inputClass}
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        )}
      </Field>
      <Field label="¿El estudiante trabaja?">
        {(id) => <YesNo id={id} value={works} onChange={setWorks} />}
      </Field>
      <Field label="Personas que viven en el hogar">
        {(id) => (
          <input
            id={id}
            type="number"
            min={1}
            max={20}
            value={household}
            onChange={(event) => setHousehold(Number(event.target.value))}
            className={inputClass}
          />
        )}
      </Field>
      <div className="flex flex-col gap-3 sm:col-span-2">
        {submit.isError && <ErrorMessage>{messageFor(submit.error)}</ErrorMessage>}
        <div>
          <Button type="submit" pending={submit.isPending}>
            Enviar encuesta
          </Button>
        </div>
      </div>
    </form>
  )
}
