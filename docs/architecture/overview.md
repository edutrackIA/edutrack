# Arquitectura

## Contexto del sistema

```mermaid
flowchart LR
    director([Director])
    teacher([Docente / Tutor])
    parent([Padre de familia])
    analyst([Analista])

    edutrack[["EduTrack<br/>Seguimiento académico y alerta temprana"]]

    director -->|Consulta indicadores y reportes| edutrack
    teacher -->|Registra notas y recibe alertas| edutrack
    parent -->|Consulta el progreso y responde encuestas| edutrack
    analyst -->|Importa datos, ejecuta modelo, ajusta umbrales| edutrack
```

## Contenedores

```mermaid
flowchart TB
    browser([Navegador])

    subgraph edutrack [EduTrack]
        web["Web App<br/><i>React · Vite · TS</i>"]
        api["API principal<br/><i>FastAPI</i>"]
        ml["Servicio ML<br/><i>FastAPI · scikit-learn</i>"]
        db[("MySQL 8")]
        model[/"Modelo entrenado<br/>(.joblib)"/]
    end

    browser -->|HTTPS| web
    web -->|REST + JWT| api
    api -->|SQLAlchemy| db
    api -->|REST interno| ml
    ml -->|carga al iniciar| model
```

| Contenedor | Responsabilidad |
|---|---|
| Web App | Interfaz por rol, dashboards con semáforos, formularios |
| API principal | Autenticación, RBAC, dominio académico, ingesta, alertas, reportes |
| Servicio ML | Inferencia del riesgo y explicación por factores |
| MySQL | Persistencia relacional |

## Flujo de evaluación de riesgo

```mermaid
sequenceDiagram
    actor A as Analista
    participant W as Web
    participant API as API principal
    participant DB as MySQL
    participant ML as Servicio ML

    A->>W: Ejecutar evaluación (periodo, aula)
    W->>API: POST /api/v1/risk-assessments/run
    API->>DB: Leer notas, asistencia, conducta y encuestas
    API->>API: Construir vector de características
    API->>ML: POST /v1/predict/batch
    ML-->>API: probabilidad + factores principales
    API->>DB: Leer umbrales de la institución
    API->>API: Asignar nivel y generar sugerencias
    API->>DB: Guardar evaluaciones y alertas
    API-->>W: Resumen de la ejecución
```

## Estructura interna de los servicios backend

Ambos servicios siguen capas:

```
app/
├── api/           # Routers y dependencias (auth, paginación)
├── core/          # Configuración, seguridad, logging
├── domain/        # Entidades y reglas de negocio
├── repositories/  # Acceso a datos (SQLAlchemy)
├── schemas/       # DTOs Pydantic (request/response)
└── services/      # Casos de uso
```

La dependencia va siempre hacia adentro: `api → services → domain`, y `services → repositories`.
