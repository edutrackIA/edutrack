"""Rule engine that turns a student's situation into recommendations.

Facts (numbers, flags and lists about the student) are computed in Python; the rules
that read them live in rules.yaml, so the catalog can grow without touching code.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain import RiskLevel, SituationKind

RULES_FILE = Path(__file__).with_name("rules.yaml")

AT_RISK = [RiskLevel.MEDIUM, RiskLevel.HIGH]
MAX_ACTIONS = 3
MAX_TUTOR_ITEMS = 5
# Slots with a fixed place in the family message; any other slot is an action.
LAYOUT_SLOTS = ("empathy", "opening", "strength", "closing")

KNOWN_FACTS = {
    "avg_score",
    "failed_subjects",
    "score_trend",
    "attendance_rate",
    "late_count",
    "behavior_rating",
    "study_hours_week",
    "parent_education",
    "home_internet",
    "has_study_device",
    "family_communication",
    "student_works",
    "household_size",
    "top_factors",
    "failing_subjects",
    "has_best_subject",
    "absences",
    "justified_absences",
    "monday_friday_absence_share",
    "previous_level",
    "previous_avg_score",
    "improved",
    "consecutive_risk_periods",
}

KNOWN_PLACEHOLDERS = {"name", "subjects", "best_subject", "tutor", "risk_periods"}


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact: str
    op: Literal["lt", "lte", "gt", "gte", "eq", "ne", "true", "false", "contains"]
    value: float | str | bool | None = None

    @model_validator(mode="after")
    def known_fact(self) -> "Condition":
        if self.fact not in KNOWN_FACTS:
            raise ValueError(f"Unknown fact '{self.fact}'")
        return self

    def holds(self, values: dict[str, Any]) -> bool:
        actual = values.get(self.fact)
        if actual is None:
            return False
        match self.op:
            case "true":
                return actual is True
            case "false":
                return actual is False
            case "contains":
                return self.value in actual
            case "eq":
                return actual == self.value
            case "ne":
                return actual != self.value
        if not isinstance(actual, int | float) or not isinstance(self.value, int | float):
            return False
        match self.op:
            case "lt":
                return actual < self.value
            case "lte":
                return actual <= self.value
            case "gt":
                return actual > self.value
            case _:
                return actual >= self.value


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slot: str
    priority: int = Field(ge=0, le=100)
    levels: list[RiskLevel] = Field(default_factory=lambda: list(AT_RISK))
    when: list[Condition] = Field(default_factory=list)
    when_any: list[Condition] = Field(default_factory=list)
    if_situations: list[SituationKind] = Field(default_factory=list)
    unless_situations: list[SituationKind] = Field(default_factory=list)
    family: list[str] = Field(default_factory=list)
    tutor: str | None = None

    @model_validator(mode="after")
    def has_output(self) -> "Rule":
        if not self.family and not self.tutor:
            raise ValueError(f"Rule '{self.id}' produces no text")
        return self

    def applies(self, facts: "Facts") -> bool:
        return (
            facts.level in self.levels
            and all(condition.holds(facts.values) for condition in self.when)
            and (not self.when_any or any(c.holds(facts.values) for c in self.when_any))
            and (not self.if_situations or bool(facts.situations & set(self.if_situations)))
            and not facts.situations & set(self.unless_situations)
        )


@dataclass
class Facts:
    level: RiskLevel
    values: dict[str, Any]
    situations: set[SituationKind] = field(default_factory=set)
    placeholders: dict[str, str] = field(default_factory=dict)
    seed: int = 0


@dataclass
class Composition:
    parent_items: list[str]
    teacher_items: list[str]
    rule_ids: list[str]


class _Blank(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return ""


def _render(text: str, facts: Facts) -> str:
    return text.format_map(_Blank(facts.placeholders))


def compose(rules: list[Rule], facts: Facts) -> Composition:
    """Family message: empathy, opening, one strength, up to 3 actions, closing."""
    matched = sorted(
        (rule for rule in rules if rule.applies(facts)), key=lambda rule: -rule.priority
    )
    family_rules = [rule for rule in matched if rule.family]

    def first(slot: str) -> list[Rule]:
        return [rule for rule in family_rules if rule.slot == slot][:1]

    actions: list[Rule] = []
    used_slots: set[str] = set()
    for rule in family_rules:
        if rule.slot in LAYOUT_SLOTS or rule.slot in used_slots:
            continue
        actions.append(rule)
        used_slots.add(rule.slot)
        if len(actions) == MAX_ACTIONS:
            break

    chosen = first("empathy") + first("opening") + first("strength") + actions + first("closing")
    # Rotate between phrasings across periods so families do not read the same text.
    parent_items = list(
        dict.fromkeys(_render(rule.family[facts.seed % len(rule.family)], facts) for rule in chosen)
    )
    teacher_items = list(
        dict.fromkeys(_render(rule.tutor, facts) for rule in matched if rule.tutor)
    )[:MAX_TUTOR_ITEMS]
    return Composition(
        parent_items=parent_items,
        teacher_items=teacher_items,
        rule_ids=[rule.id for rule in chosen],
    )


def parse_rules(document: dict[str, Any]) -> list[Rule]:
    rules = [Rule.model_validate(item) for item in document.get("rules", [])]
    ids = [rule.id for rule in rules]
    duplicated = {rule_id for rule_id in ids if ids.count(rule_id) > 1}
    if duplicated:
        raise ValueError(f"Duplicated rule ids: {sorted(duplicated)}")
    return rules


@lru_cache
def load_rules() -> list[Rule]:
    return parse_rules(yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")))
