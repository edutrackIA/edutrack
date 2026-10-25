# ADR-0009: Situaciones de contexto en lugar de analizar texto libre

- **Estado:** Aceptado
- **Fecha:** 2026-10-27

## Contexto
Los datos académicos no reflejan situaciones como un duelo, un problema de salud o un posible acoso, y esas situaciones cambian qué conviene recomendar a una familia. Se evaluó que el tutor suba comentarios o informes psicológicos para que un modelo los interprete.

## Decisión
- El tutor marca **situaciones de una lista cerrada** durante el seguimiento semanal, con una nota breve opcional. No se suben informes psicológicos: solo se registra "en seguimiento psicológico".
- Las situaciones **no son variables del modelo ML**. Son entradas del motor de reglas que ajustan el tono, omiten sugerencias o agregan acciones para el equipo.
- Hay dos grupos: `MESSAGE` (ajusta el mensaje a la familia sin nombrar la situación) y `TEAM` (acoso, violencia, consumo, embarazo y otras; nunca generan texto para la familia).
- Solo el tutor del aula y la dirección ven y gestionan las situaciones. Cada cambio queda auditado.
- El tutor confirma cada semana que revisó su aula, por excepción: marca solo los cambios y confirma el resto. Puede editar hasta el sábado (hora de Lima).

## Consecuencias
- No se procesan datos de salud con modelos de lenguaje ni se transfieren fuera del colegio, en línea con la Ley N.° 29733.
- Las situaciones que exigen protocolos (violencia, acoso) quedan en manos de personas, no de mensajes automáticos.
- La lista es configurable en `app/services/situations/catalog.py` y debería validarse con TOE y psicología de cada colegio.
