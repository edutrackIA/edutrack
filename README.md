# EduTrack

Plataforma web de seguimiento académico y alerta temprana del riesgo de desaprobación y deserción escolar en estudiantes de secundaria, basada en Machine Learning.

> 🚧 Proyecto en desarrollo.

## Descripción

EduTrack centraliza calificaciones, asistencia y variables sociofamiliares de los estudiantes. Con esos datos, un modelo de clasificación supervisada (Random Forest) estima el nivel de riesgo de cada alumno y lo muestra en dashboards con semáforos (bajo, moderado y alto) para directores, docentes, tutores y padres de familia. Además, genera sugerencias pedagógicas preventivas.

## Arquitectura

| Componente | Tecnología |
|---|---|
| Frontend | React · Vite · TypeScript |
| API principal | FastAPI · SQLAlchemy · Alembic |
| Microservicio ML | FastAPI · scikit-learn · imbalanced-learn |
| Base de datos | MySQL 8 |
| Seguridad | JWT · RBAC |
| Infraestructura | Docker Compose · AWS (EC2 / RDS) |

## Estructura del repositorio

```
edutrack/
├── apps/web/        # Frontend
├── services/api/    # API principal
├── services/ml/     # Microservicio de Machine Learning
├── infra/           # Docker Compose y despliegue
└── docs/            # Arquitectura, ADRs y contratos de API
```

## Datos

El proyecto usa un **dataset sintético**. No se utilizan datos reales de estudiantes, en cumplimiento de la Ley N.° 29733 de Protección de Datos Personales.

## Flujo de trabajo

Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

[MIT](LICENSE) © 2026 Renzo Alonso Villafuerte Tapia
