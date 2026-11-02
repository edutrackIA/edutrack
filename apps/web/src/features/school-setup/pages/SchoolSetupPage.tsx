import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '../../../shared/ui/PageHeader'
import { AssignmentsSection } from '../components/AssignmentsSection'
import { ClassroomsSection } from '../components/ClassroomsSection'
import { PeriodsSection } from '../components/PeriodsSection'
import { StaffSection } from '../components/StaffSection'
import { SubjectsSection } from '../components/SubjectsSection'
import { YearClosingSection } from '../components/YearClosingSection'

// In the order a new school fills them in.
const SECTIONS = [
  { id: 'bimestres', label: 'Bimestres', Component: PeriodsSection },
  { id: 'cursos', label: 'Cursos', Component: SubjectsSection },
  { id: 'personal', label: 'Personal', Component: StaffSection },
  { id: 'aulas', label: 'Aulas', Component: ClassroomsSection },
  { id: 'asignaciones', label: 'Asignaciones', Component: AssignmentsSection },
  { id: 'cierre', label: 'Cierre de año', Component: YearClosingSection },
] as const

export default function SchoolSetupPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const current = SECTIONS.find((item) => item.id === searchParams.get('seccion')) ?? SECTIONS[0]
  const Section = current.Component

  return (
    <>
      <PageHeader
        title="Configuración del colegio"
        description="Bimestres, cursos, personal, aulas, asignaciones y cierre de año."
      />
      <nav aria-label="Secciones de la configuración" className="mb-8 flex flex-wrap gap-1">
        {SECTIONS.map((item, index) => (
          <button
            key={item.id}
            type="button"
            aria-current={item.id === current.id ? 'page' : undefined}
            onClick={() => setSearchParams({ seccion: item.id }, { replace: true })}
            className={`rounded-md px-3 py-2 ${
              item.id === current.id
                ? 'bg-accent-tint font-bold text-accent-strong'
                : 'text-ink-soft hover:text-ink'
            }`}
          >
            <span className="mr-1.5 tabular-nums text-ink-soft">{index + 1}.</span>
            {item.label}
          </button>
        ))}
      </nav>
      <Section />
    </>
  )
}
