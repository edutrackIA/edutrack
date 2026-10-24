# ADR-0006: Umbrales de riesgo configurados en la API principal

- **Estado:** Aceptado
- **Fecha:** 2026-10-24

## Contexto
RF-10 pide que cada institución pueda ajustar la sensibilidad de las alertas sin reentrenar el modelo.

## Decisión
- El servicio ML devuelve solo la probabilidad de riesgo (de 0 a 1).
- La API principal la convierte en `LOW`, `MEDIUM` o `HIGH` con los umbrales guardados por institución. Los valores por defecto son 0.40 y 0.70.

## Consecuencias
- Cambiar umbrales no exige redesplegar el modelo.
- Cada evaluación guarda la probabilidad y el nivel calculado, para mantener la trazabilidad histórica.
