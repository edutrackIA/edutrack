# ADR-0007: Explicación de predicciones por oclusión

- **Estado:** Aceptado
- **Fecha:** 2026-10-25

## Contexto
Docentes y padres necesitan saber **por qué** un estudiante aparece en riesgo para actuar sobre ello. La importancia global de variables del Random Forest no explica casos individuales. SHAP daría una explicación más rigurosa, pero añade una dependencia pesada al servicio de inferencia.

## Decisión
- La contribución de cada variable se mide reemplazándola por el valor mediano del conjunto de entrenamiento (la "línea base") y observando cuánto baja la probabilidad de riesgo.
- Se devuelven hasta 5 factores con contribución positiva, ordenados de mayor a menor.
- La línea base se guarda junto al modelo en `model.json`.

## Consecuencias
- La explicación se calcula con el mismo modelo y sin dependencias adicionales: una sola llamada vectorizada a `predict_proba` por lote.
- Es una aproximación local: no captura bien las interacciones entre variables. Si se requiere mayor rigor, se puede reemplazar por SHAP sin cambiar el contrato de la API.
