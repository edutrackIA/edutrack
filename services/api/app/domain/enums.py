from enum import StrEnum


class Role(StrEnum):
    DIRECTOR = "DIRECTOR"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ANALYST = "ANALYST"


class Sex(StrEnum):
    M = "M"
    F = "F"
