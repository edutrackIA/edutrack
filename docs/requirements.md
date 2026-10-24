# Trazabilidad de requisitos

| Código | Requisito (resumen) | Prioridad | Componente | Endpoints principales |
|---|---|---|---|---|
| RF-01 | Autenticación y acceso por rol | Must | api, web | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| RF-02 | Ficha académica y conductual del estudiante | Must | api, web | `GET/PATCH /students/{id}`, `PUT /students/{id}/grades`, `PUT /students/{id}/behavior` |
| RF-03 | Carga masiva de notas y asistencia (CSV/Excel) | Must | api | `POST /imports`, `GET /imports/{id}` |
| RF-04 | Ejecutar el modelo predictivo | Must | api, ml | `POST /risk-assessments/run` → ML `POST /v1/predict/batch` |
| RF-05 | Dashboard gerencial con semáforos | Must | api, web | `GET /dashboard/summary` |
| RF-06 | Alertas automáticas al tutor | Must | api, web | `GET /alerts`, `PATCH /alerts/{id}` |
| RF-07 | Portal del padre de familia | Must | api, web | `GET /me/children`, `GET /students/{id}/summary`, `POST /students/{id}/surveys` |
| RF-08 | Compromisos y actas con padres | Should | api, web | `GET/POST /students/{id}/commitments` |
| RF-09 | Reportes PDF | Should | api | `GET /reports/risk` |
| RF-10 | Configurar umbrales de riesgo | Must | api, web | `GET/PUT /settings/risk-thresholds` |
| RNF-01 | Respuesta ≤ 2 s | Must | todos | Prueba de rendimiento en la Fase 8 |
| RNF-02 | F1-Score ≥ 0.75 y AUC-ROC > 0.80 | Must | ml | Reporte de entrenamiento en `services/ml` |
| RNF-03 | Cifrado en tránsito y protección de datos | Must | api, infra | HTTPS, hash de contraseñas, RBAC por pertenencia |

Todas las rutas de la API principal llevan el prefijo `/api/v1`.
