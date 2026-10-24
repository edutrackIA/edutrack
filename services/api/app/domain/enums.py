from enum import StrEnum


class Role(StrEnum):
    DIRECTOR = "DIRECTOR"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ANALYST = "ANALYST"


class Sex(StrEnum):
    M = "M"
    F = "F"


class AttendanceStatus(StrEnum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    JUSTIFIED = "JUSTIFIED"


class ImportKind(StrEnum):
    STUDENTS = "STUDENTS"
    GRADES = "GRADES"
    ATTENDANCE = "ATTENDANCE"


class ImportStatus(StrEnum):
    PENDING = "PENDING"
    DONE = "DONE"
    FAILED = "FAILED"


class ParentEducation(StrEnum):
    NONE = "NONE"
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TECHNICAL = "TECHNICAL"
    UNIVERSITY = "UNIVERSITY"


class CommitmentStatus(StrEnum):
    OPEN = "OPEN"
    FULFILLED = "FULFILLED"
    BREACHED = "BREACHED"
