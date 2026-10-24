# ADR-0001: Monorepo

- **Estado:** Aceptado
- **Fecha:** 2026-10-24

## Contexto
El sistema tiene tres componentes desplegables (frontend, API principal y microservicio ML) que comparten contratos y evolucionan juntos.

## Decisión
Todos los componentes viven en un único repositorio: `apps/web`, `services/api`, `services/ml`, `infra` y `docs`.

## Consecuencias
- Un cambio de contrato y sus consumidores se revisan en un solo Pull Request.
- El CI debe filtrar por rutas para no ejecutar todos los pipelines en cada cambio.
