# ADR-0003: Python y FastAPI para los servicios backend

- **Estado:** Aceptado
- **Fecha:** 2026-10-24

## Contexto
El microservicio ML requiere Python. Mantener un único lenguaje en el backend reduce la carga de mantenimiento.

## Decisión
- La API principal y el servicio ML usan FastAPI.
- La persistencia usa SQLAlchemy 2 con migraciones Alembic sobre MySQL 8.
- La validación usa Pydantic v2.

## Consecuencias
- FastAPI genera la documentación OpenAPI automáticamente, lo que permite contrastarla con los contratos de `docs/api`.
- Todo el backend comparte herramientas: pytest, ruff y coverage.
