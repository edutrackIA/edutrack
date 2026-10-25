"""Situations a tutor can mark. The rules engine reads `group` to decide how they act.

MESSAGE: adjusts what the family receives, without ever naming the situation.
TEAM: never reaches the family; it only creates actions for the school team.
"""

from dataclasses import dataclass
from typing import Literal

from app.domain import SituationKind

Group = Literal["MESSAGE", "TEAM"]


@dataclass(frozen=True)
class SituationInfo:
    label: str
    group: Group
    description: str


SITUATIONS: dict[SituationKind, SituationInfo] = {
    SituationKind.GRIEF: SituationInfo(
        "Duelo familiar", "MESSAGE", "Pérdida de un familiar o persona cercana."
    ),
    SituationKind.HEALTH: SituationInfo(
        "Problema de salud", "MESSAGE", "Enfermedad, tratamiento u hospitalización."
    ),
    SituationKind.RELOCATION: SituationInfo(
        "Cambio de domicilio o de colegio", "MESSAGE", "Mudanza o llegada reciente al colegio."
    ),
    SituationKind.ECONOMIC_HARDSHIP: SituationInfo(
        "Situación económica difícil", "MESSAGE", "Pérdida de empleo u otras dificultades."
    ),
    SituationKind.PSYCHOLOGY_FOLLOW_UP: SituationInfo(
        "En seguimiento psicológico", "MESSAGE", "Atendido por psicología o TOE."
    ),
    SituationKind.PARENTS_SEPARATION: SituationInfo(
        "Separación o divorcio de los padres", "MESSAGE", "Cambio reciente en la familia."
    ),
    SituationKind.PARENTS_AWAY: SituationInfo(
        "Padres que trabajan lejos o en el extranjero",
        "MESSAGE",
        "El cuidado lo asume otro familiar.",
    ),
    SituationKind.HOME_RESPONSIBILITIES: SituationInfo(
        "Responsabilidades en casa", "MESSAGE", "Cuida hermanos o a un familiar."
    ),
    SituationKind.MIGRANT: SituationInfo(
        "Estudiante migrante", "MESSAGE", "Llegó de otro país o región."
    ),
    SituationKind.SPECIAL_NEEDS: SituationInfo(
        "Necesidades educativas especiales", "MESSAGE", "Requiere adaptaciones."
    ),
    SituationKind.HIGH_ACHIEVER: SituationInfo(
        "Alto rendimiento o talento", "MESSAGE", "Necesita retos adicionales."
    ),
    SituationKind.BULLYING: SituationInfo(
        "Convivencia escolar (posible acoso)",
        "TEAM",
        "Activa el protocolo de convivencia. Nunca se informa en mensajes automáticos.",
    ),
    SituationKind.PREGNANCY: SituationInfo(
        "Embarazo o paternidad adolescente", "TEAM", "Requiere un plan flexible con TOE."
    ),
    SituationKind.FAMILY_VIOLENCE: SituationInfo(
        "Sospecha de violencia familiar",
        "TEAM",
        "Activa el protocolo y el reporte correspondiente. Nunca se comunica a la familia.",
    ),
    SituationKind.SUBSTANCE_USE: SituationInfo(
        "Sospecha de consumo de sustancias", "TEAM", "Derivación a TOE o psicología."
    ),
    SituationKind.OTHER: SituationInfo(
        "Otra situación", "TEAM", "Registro para el equipo; no cambia las recomendaciones."
    ),
}
