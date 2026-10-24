# ADR-0005: Dataset sintético

- **Estado:** Aceptado
- **Fecha:** 2026-10-24

## Contexto
Usar datos reales de estudiantes en un repositorio público vulneraría la Ley N.° 29733.

## Decisión
- Un script reproducible (con semilla fija) genera estudiantes con distribuciones realistas y una clase minoritaria de riesgo (entre 15 % y 20 %).
- El mismo generador alimenta el entrenamiento del modelo y los datos de prueba (seed) de la base de datos.

## Consecuencias
- Las métricas del modelo reflejan la lógica del generador, no un colegio real. Esto se declara en el README.
