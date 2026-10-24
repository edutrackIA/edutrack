# ADR-0002: Microservicio independiente para Machine Learning

- **Estado:** Aceptado
- **Fecha:** 2026-10-24

## Contexto
La inferencia del modelo carga dependencias pesadas (scikit-learn, pandas) y tiene un ciclo de vida distinto al de la lógica de negocio: reentrenamiento, versionado de modelos y métricas.

## Decisión
- El modelo se expone como un servicio FastAPI separado (`services/ml`).
- El servicio ML es **stateless** y no accede a la base de datos: recibe un vector de características y devuelve una probabilidad y los factores principales.
- La API principal construye las características a partir de MySQL, llama al servicio ML y persiste el resultado.

## Consecuencias
- El modelo se puede reemplazar o reentrenar sin tocar la API principal.
- La comunicación es una llamada HTTP interna, que agrega latencia. Se mitiga con el endpoint de predicción por lotes.
