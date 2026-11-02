# ADR-0010: Motor de reglas declarativo para las recomendaciones

- **Estado:** Aceptado (reemplaza el catálogo de un texto por factor)
- **Fecha:** 2026-10-27

## Contexto
El primer catálogo asociaba un único texto a cada factor del modelo. No distinguía la gravedad (88 % de asistencia frente a 65 %), no combinaba factores, ignoraba el historial y las situaciones de contexto, y repetía el mismo texto cada bimestre.

## Decisión
- Los **hechos** del estudiante se calculan en Python: variables del modelo, cursos desaprobados y destacados, patrón de faltas por día, faltas justificadas, historial de riesgo y situaciones activas.
- Las **reglas** viven en `rules.yaml`: condiciones sobre esos hechos, situaciones que las activan o las anulan, prioridad, textos para la familia (con variantes que rotan entre bimestres) y una acción para el tutor.
- Las reglas que comparten un `slot` compiten y solo gana la de mayor prioridad. Así, por ejemplo, "faltas en lunes y viernes" desplaza a "asistencia baja".
- El mensaje a la familia sigue una estructura fija: empatía, apertura, una fortaleza, hasta tres acciones y el cierre con el tutor.
- Al cargar, las reglas se validan contra los hechos y marcadores conocidos; un error en el YAML impide arrancar en lugar de fallar en silencio.

## Consecuencias
- El catálogo crece editando el YAML, sin tocar código.
- Los textos para la familia nunca mencionan riesgo ni probabilidades (lo verifica un test).
- Ningún mensaje llega a la familia sin la revisión del tutor.
- El siguiente paso posible es mover las reglas a la base de datos para editarlas desde la aplicación.
