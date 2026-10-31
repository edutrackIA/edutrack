# ADR-0013: Ciclo de vida del modelo con datos reales del colegio

- **Estado:** Aceptado
- **Fecha:** 2026-11-03

## Contexto
El modelo inicial se entrenó con datos sintéticos (ADR-0005). Sirve para empezar, pero su desempeño con estudiantes reales es desconocido y cada colegio es distinto. Con el registro de retiros ya existe la "respuesta correcta" de cada evaluación.

## Decisión
- **Una instalación por colegio cliente:** cada colegio tiene su propia API, base de datos y servicio ML, por lo que el modelo activo es el de ese colegio. Un esquema multi-colegio necesitaría un modelo por institución.
- **Medición:** una evaluación tiene resultado cuando el estudiante se retira (no se traslada) dentro de los 180 días posteriores al bimestre, o cuando ese plazo vence sin retiro. Solo se muestran métricas con 20 resultados y 3 retiros como mínimo.
- **Reentrenamiento:** el servicio ML combina el dataset sintético con los casos reales anonimizados (solo variables del modelo y el resultado; con peso 5). Reserva el 30 % de los casos reales, que no se usan para entrenar, y evalúa en ellos tanto el modelo activo como el candidato. Exige 200 casos con resultado y 20 retiros.
- **Versionado:** cada modelo se guarda como una versión inmutable; un archivo indica cuál está activa. Activar una versión anterior es la vuelta atrás.
- **Separación de funciones:** el área de análisis entrena candidatos; solo la dirección los activa. Cada acción queda registrada con su autor.
- **Seguridad:** las acciones de administración del servicio ML requieren un token compartido solo con la API.

## Consecuencias
- Ningún dato identificable sale de la API hacia el entrenamiento.
- Un candidato nunca reemplaza al modelo vigente sin una decisión humana informada por la comparación.
- Entrenar puede tardar minutos; se hace bajo demanda, no en cada evaluación.
