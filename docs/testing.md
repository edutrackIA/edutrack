# Pruebas

| Nivel | Herramienta | Dónde | Cuándo corre |
|---|---|---|---|
| Unitarias e integración de la API | pytest (SQLite en memoria) | `services/api/tests` | Cada PR (cobertura mínima 70 %) |
| Servicio ML | pytest | `services/ml/tests` | Cada PR |
| Componentes web | Vitest + Testing Library | `apps/web/src/**/*.test.tsx` | Cada PR |
| De punta a punta | Playwright | `apps/web/e2e` | PR hacia `main` y manualmente |
| Accesibilidad | axe-core en Playwright | `apps/web/e2e/accessibility.spec.ts` | Junto con E2E |

## Ejecutar las pruebas E2E en local

Necesitan la aplicación completa con los datos demo:

```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed_dev
cd apps/web
npx playwright install chromium   # solo la primera vez
npm run e2e
```

Playwright inicia el servidor de Vite si no está corriendo. Antes de las pruebas, `global-setup.ts` evalúa el riesgo del último bimestre con notas.

Las pruebas no dejan cambios que afecten a otras: la recuperación de contraseña vuelve a poner la contraseña demo, y la carga de datos se cancela antes de guardar.

**Límites a tener en cuenta:** la recuperación de contraseña acepta 3 solicitudes por correo cada hora. Si corres las E2E más de tres veces en una hora, esa prueba falla hasta que pase el plazo (o reinicia el contenedor de la API, que guarda los contadores en memoria).

## Qué cubren

- Inicio de sesión por rol, contraseña incorrecta, cierre de sesión y recargas rápidas seguidas (ADR-0008).
- Semáforo del director, vista rápida y vuelta desde la ficha.
- Consentimiento del apoderado, portal sin niveles de riesgo y aviso prioritario al tutor por correo.
- Revisión de un archivo de notas con errores sin guardar nada.
- Recuperación de contraseña de punta a punta con el correo de Mailpit.
- Ausencia de problemas graves de accesibilidad (WCAG 2 A/AA) en el login y el resumen.
