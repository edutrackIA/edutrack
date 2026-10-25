import string

import pytest
from pydantic import ValidationError

from app.domain import RiskLevel, SituationKind
from app.services.recommendations.engine import (
    KNOWN_PLACEHOLDERS,
    MAX_ACTIONS,
    Facts,
    compose,
    load_rules,
    parse_rules,
)

BASE_VALUES = {
    "avg_score": 13.0,
    "failed_subjects": 0,
    "score_trend": 0.0,
    "attendance_rate": 0.93,
    "late_count": 0,
    "behavior_rating": 3,
    "study_hours_week": 8,
    "home_internet": True,
    "has_study_device": True,
    "family_communication": 4,
    "student_works": False,
    "household_size": 4,
    "top_factors": [],
    "failing_subjects": [],
    "has_best_subject": False,
    "absences": 0,
    "justified_absences": 0,
    "monday_friday_absence_share": 0.0,
    "previous_level": None,
    "previous_avg_score": None,
    "improved": False,
    "consecutive_risk_periods": 1,
}


def facts(
    level: RiskLevel = RiskLevel.HIGH,
    situations: tuple[SituationKind, ...] = (),
    seed: int = 0,
    **values: object,
) -> Facts:
    return Facts(
        level=level,
        values=BASE_VALUES | values,
        situations=set(situations),
        placeholders={
            "name": "Lucía",
            "subjects": "Comunicación, Matemática",
            "best_subject": "Arte",
            "tutor": "Luis Quispe",
            "risk_periods": str(values.get("consecutive_risk_periods", 1)),
        },
        seed=seed,
    )


def message(f: Facts) -> list[str]:
    return compose(load_rules(), f).parent_items


def tutor(f: Facts) -> list[str]:
    return compose(load_rules(), f).teacher_items


# --- Catálogo ---------------------------------------------------------------------


def test_rules_file_is_valid_and_family_texts_never_mention_risk() -> None:
    rules = load_rules()
    formatter = string.Formatter()

    assert len(rules) >= 40
    for rule in rules:
        for text in [*rule.family, rule.tutor or ""]:
            fields = {name for _, name, _, _ in formatter.parse(text) if name}
            assert fields <= KNOWN_PLACEHOLDERS, rule.id
        for text in rule.family:
            assert "riesgo" not in text.lower(), rule.id
            assert "probabilidad" not in text.lower(), rule.id


def test_invalid_rules_are_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_rules(
            {
                "rules": [
                    {
                        "id": "x",
                        "slot": "a",
                        "priority": 1,
                        "tutor": "t",
                        "when": [{"fact": "unknown", "op": "lt", "value": 1}],
                    }
                ]
            }
        )
    with pytest.raises(ValidationError):
        parse_rules({"rules": [{"id": "x", "slot": "a", "priority": 1}]})
    with pytest.raises(ValueError, match="Duplicated"):
        parse_rules({"rules": [{"id": "x", "slot": "a", "priority": 1, "tutor": "t"}] * 2})


# --- Gravedad y especificidad -------------------------------------------------------


def test_severity_picks_the_most_specific_attendance_rule() -> None:
    moderate = message(facts(attendance_rate=0.86))
    severe = message(facts(attendance_rate=0.7))
    pattern = message(
        facts(attendance_rate=0.7, absences=5, monday_friday_absence_share=0.8)
    )

    assert any("asegurar su asistencia" in item or "cada clase cuenta" in item for item in moderate)
    assert any("faltó a muchas clases" in item for item in severe)
    assert any("lunes y viernes" in item for item in pattern)
    assert sum(item.startswith("Asistencia:") for item in pattern) == 1


def test_at_most_three_actions_plus_closing() -> None:
    items = message(
        facts(
            attendance_rate=0.7,
            failed_subjects=3,
            failing_subjects=["Matemática"],
            late_count=8,
            behavior_rating=1,
            student_works=True,
            study_hours_week=2,
        )
    )

    assert len(items) == MAX_ACTIONS + 1
    assert items[-1].startswith("Seguimiento: su tutor, Luis Quispe")


def test_phrasings_rotate_between_periods() -> None:
    first = message(facts(attendance_rate=0.7, seed=0))[0]
    second = message(facts(attendance_rate=0.7, seed=1))[0]

    assert first != second
    assert first.startswith("Asistencia:") and second.startswith("Asistencia:")


# --- Historial y fortalezas -------------------------------------------------------------


def test_sudden_drop_of_a_good_student() -> None:
    items = message(facts(previous_avg_score=16.0, score_trend=-3.0))

    assert any(item.startswith("Cambio reciente: Lucía solía tener muy buenas notas") for item in items)


def test_improvement_is_celebrated_and_persistent_cases_escalate() -> None:
    improved = message(facts(level=RiskLevel.MEDIUM, improved=True))
    persistent = tutor(facts(consecutive_risk_periods=3))

    assert improved[0].startswith("Avance:")
    assert any("3 bimestres seguidos" in item for item in persistent)


def test_low_risk_gets_a_positive_message_without_closing() -> None:
    items = message(facts(level=RiskLevel.LOW, attendance_rate=0.98))

    assert items[0].startswith("Buen desempeño: Lucía")
    assert items[1] == "Fortaleza: Lucía asiste a clases con mucha regularidad."
    assert not any(item.startswith("Seguimiento:") for item in items)


# --- Situaciones de contexto ---------------------------------------------------------


def test_health_replaces_attendance_pressure_with_a_recovery_plan() -> None:
    items = message(facts(attendance_rate=0.7, absences=6, situations=(SituationKind.HEALTH,)))

    assert any(item.startswith("Salud y clases:") for item in items)
    assert not any("faltó a muchas clases" in item for item in items)


def test_grief_comes_first_and_removes_academic_pressure() -> None:
    items = message(
        facts(attendance_rate=0.7, failed_subjects=2, situations=(SituationKind.GRIEF,))
    )

    assert items[0].startswith("Acompañamiento: sabemos que es un momento difícil")
    assert not any(item.startswith(("Cursos a reforzar", "Asistencia")) for item in items)


def test_team_situations_never_reach_the_family() -> None:
    f = facts(
        behavior_rating=1,
        situations=(SituationKind.BULLYING, SituationKind.FAMILY_VIOLENCE),
    )
    family = " ".join(message(f)).lower()
    actions = tutor(f)

    assert "protocolo" not in family
    assert "acoso" not in family
    assert "violencia" not in family
    assert not any(item.startswith("Convivencia:") for item in message(f))
    assert any("protocolo de convivencia" in item for item in actions)
    assert any("No informar a la familia" in item for item in actions)


def test_home_responsibilities_avoid_asking_for_more_study_time_at_home() -> None:
    items = message(
        facts(study_hours_week=2, situations=(SituationKind.HOME_RESPONSIBILITIES,))
    )

    assert any(item.startswith("Tiempo de estudio:") for item in items)
    assert not any(item.startswith("Hábitos de estudio:") for item in items)
