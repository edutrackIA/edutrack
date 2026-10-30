import { lazy, Suspense, type ComponentType, type LazyExoticComponent } from 'react'
import type { RouteObject } from 'react-router-dom'
import { RequireAuth, RequireRole } from '../features/auth/guards'
import LoginPage from '../features/auth/pages/LoginPage'
import AcceptInvitationPage from '../features/auth/pages/AcceptInvitationPage'
import type { Role } from '../features/auth/types'
import { AppLayout } from './layouts/AppLayout'
import { HomeRedirect } from './pages/HomeRedirect'
import { NotFoundPage } from './pages/NotFoundPage'
import { PendingPage } from './pages/PendingPage'
import { LoadingState } from '../shared/ui/Feedback'

// Pages load on demand: each role only downloads the screens it uses.
const DashboardPage = lazy(() => import('../features/dashboard/pages/DashboardPage'))
const ClassroomsPage = lazy(() => import('../features/classrooms/pages/ClassroomsPage'))
const StudentRecordPage = lazy(() => import('../features/students/pages/StudentRecordPage'))
const AlertsPage = lazy(() => import('../features/alerts/pages/AlertsPage'))
const WeeklyFollowUpPage = lazy(
  () => import('../features/situations/pages/WeeklyFollowUpPage'),
)
const ParentPortalPage = lazy(() => import('../features/parent-portal/pages/ParentPortalPage'))
const ImportsPage = lazy(() => import('../features/analyst/pages/ImportsPage'))
const AssessmentsPage = lazy(() => import('../features/analyst/pages/AssessmentsPage'))
const ThresholdsPage = lazy(() => import('../features/analyst/pages/ThresholdsPage'))
const SchoolSetupPage = lazy(() => import('../features/school-setup/pages/SchoolSetupPage'))
const RecommendationsPage = lazy(
  () => import('../features/recommendations/pages/RecommendationsPage'),
)

interface Section {
  path: string
  roles: Role[]
  title: string
  description: string
  page?: LazyExoticComponent<ComponentType>
}

// Each section is replaced by its real page in the following frontend features.
const SECTIONS: Section[] = [
  {
    path: 'resumen',
    roles: ['DIRECTOR', 'ANALYST'],
    title: 'Resumen del colegio',
    description: 'Cómo está cada aula y qué explica el riesgo este bimestre.',
    page: DashboardPage,
  },
  {
    path: 'aulas',
    roles: ['DIRECTOR', 'TEACHER', 'ANALYST'],
    title: 'Aulas',
    description: 'Estudiantes de cada aula con su nivel de riesgo.',
    page: ClassroomsPage,
  },
  {
    path: 'alertas',
    roles: ['TEACHER'],
    title: 'Alertas',
    description: 'Estudiantes que necesitan seguimiento.',
    page: AlertsPage,
  },
  {
    path: 'recomendaciones',
    roles: ['TEACHER', 'DIRECTOR'],
    title: 'Recomendaciones',
    description: 'Revisa y aprueba las sugerencias antes de enviarlas a las familias.',
    page: RecommendationsPage,
  },
  {
    path: 'configuracion',
    roles: ['DIRECTOR'],
    title: 'Configuración del colegio',
    description: 'Bimestres, cursos, personal, aulas y asignaciones.',
    page: SchoolSetupPage,
  },
  {
    path: 'seguimiento',
    roles: ['TEACHER'],
    title: 'Seguimiento semanal',
    description: 'Situaciones de contexto de tus estudiantes.',
    page: WeeklyFollowUpPage,
  },
  {
    path: 'evaluaciones',
    roles: ['ANALYST'],
    title: 'Evaluaciones de riesgo',
    description: 'Ejecuta el análisis de un bimestre o de un aula.',
    page: AssessmentsPage,
  },
  {
    path: 'carga-de-datos',
    roles: ['ANALYST'],
    title: 'Carga de datos',
    description: 'Importa estudiantes, notas y asistencia desde Excel o CSV.',
    page: ImportsPage,
  },
  {
    path: 'umbrales',
    roles: ['ANALYST'],
    title: 'Umbrales de riesgo',
    description: 'Define desde qué probabilidad un caso es moderado o alto.',
    page: ThresholdsPage,
  },
  {
    path: 'mi-hijo',
    roles: ['PARENT'],
    title: 'Mi hijo',
    description: 'Avance del bimestre y sugerencias para acompañarlo en casa.',
    page: ParentPortalPage,
  },
]

export const routes: RouteObject[] = [
  { path: '/login', element: <LoginPage /> },
  // Public: invited guardians have no session yet.
  { path: '/invitacion/:token', element: <AcceptInvitationPage /> },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <HomeRedirect /> },
      ...SECTIONS.map((section) => ({
        path: section.path,
        element: (
          <RequireRole roles={section.roles}>
            {section.page ? (
              <Suspense fallback={<LoadingState />}>
                <section.page />
              </Suspense>
            ) : (
              <PendingPage title={section.title} description={section.description} />
            )}
          </RequireRole>
        ),
      })),
      {
        path: 'estudiantes/:studentId',
        element: (
          <RequireRole roles={['DIRECTOR', 'TEACHER', 'ANALYST']}>
            <Suspense fallback={<LoadingState />}>
              <StudentRecordPage />
            </Suspense>
          </RequireRole>
        ),
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
