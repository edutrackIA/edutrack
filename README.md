# EduTrack

Plataforma web de seguimiento académico y alerta temprana del riesgo de desaprobación y deserción escolar en estudiantes de secundaria, basada en Machine Learning.

> 🚧 Proyecto en desarrollo.

## Descripción

EduTrack centraliza calificaciones, asistencia y variables sociofamiliares de los estudiantes. Con esos datos, un modelo de clasificación supervisada (Random Forest) estima el nivel de riesgo de cada alumno y lo muestra en dashboards con semáforos (bajo, moderado y alto) para directores, docentes, tutores y padres de familia. Además, genera sugerencias pedagógicas preventivas.

## Arquitectura

![Diagrama de contenedores](docs/architecture/images/Containers.png)

| Componente | Tecnología |
|---|---|
| Frontend | React · Vite · TypeScript |
| API principal | FastAPI · SQLAlchemy · Alembic |
| Microservicio ML | FastAPI · scikit-learn · imbalanced-learn |
| Base de datos | MySQL 8 |
| Seguridad | JWT · RBAC |
| Infraestructura | Docker Compose · AWS (EC2 / RDS) |

La documentación completa está en [`docs/`](docs/README.md).

## Estructura del repositorio

```
edutrack/
├── apps/web/        # Frontend
├── services/api/    # API principal
├── services/ml/     # Microservicio de Machine Learning
├── docs/            # Arquitectura, ADRs y contratos de API
└── compose.yaml     # Entorno local
```

## Ejecución local

**Requisitos:** Docker Desktop, Node.js 20 y Python 3.12.

```bash
cp .env.example .env
docker compose up --build        # mysql, api y ml
```

En otra terminal, el frontend con recarga en caliente:

```bash
cd apps/web
npm install
npm run dev
```

| Servicio | URL |
|---|---|
| Web (desarrollo) | http://localhost:5173 |
| API y documentación | http://localhost:8000/api/docs |
| Servicio ML | http://localhost:8001/docs |

### Base de datos

Con los contenedores levantados, aplica las migraciones y crea los usuarios de prueba:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed_dev
```

| Usuario | Rol |
|---|---|
| director@edutrack.dev | Director |
| docente@edutrack.dev | Docente |
| padre@edutrack.dev | Padre de familia |
| analista@edutrack.dev | Analista |

Todos usan la contraseña `Edutrack123!`.

Para levantar también el frontend compilado detrás de Nginx: `docker compose --profile full up --build` y abrir http://localhost:8080.

## Tests

```bash
cd services/api && pip install -r requirements-dev.txt && pytest
cd services/ml  && pip install -r requirements-dev.txt && pytest
cd apps/web     && npm test
```

## Datos

El proyecto usa un **dataset sintético**. No se utilizan datos reales de estudiantes, en cumplimiento de la Ley N.° 29733 de Protección de Datos Personales.

## Flujo de trabajo

Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

[MIT](LICENSE) © 2026 Renzo Alonso Villafuerte Tapia
