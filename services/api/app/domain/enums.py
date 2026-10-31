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
    GUARDIANS = "GUARDIANS"


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


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RecommendationStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    DISCARDED = "DISCARDED"


class SituationKind(StrEnum):
    GRIEF = "GRIEF"
    HEALTH = "HEALTH"
    RELOCATION = "RELOCATION"
    ECONOMIC_HARDSHIP = "ECONOMIC_HARDSHIP"
    PSYCHOLOGY_FOLLOW_UP = "PSYCHOLOGY_FOLLOW_UP"
    PARENTS_SEPARATION = "PARENTS_SEPARATION"
    PARENTS_AWAY = "PARENTS_AWAY"
    HOME_RESPONSIBILITIES = "HOME_RESPONSIBILITIES"
    MIGRANT = "MIGRANT"
    SPECIAL_NEEDS = "SPECIAL_NEEDS"
    HIGH_ACHIEVER = "HIGH_ACHIEVER"
    BULLYING = "BULLYING"
    PREGNANCY = "PREGNANCY"
    FAMILY_VIOLENCE = "FAMILY_VIOLENCE"
    SUBSTANCE_USE = "SUBSTANCE_USE"
    OTHER = "OTHER"


class SituationAction(StrEnum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"


class FamilyMessageKind(StrEnum):
    WEEKLY_ATTENDANCE = "WEEKLY_ATTENDANCE"
    PERFECT_ATTENDANCE = "PERFECT_ATTENDANCE"
    PERIOD_GRADES = "PERIOD_GRADES"


class FamilyMessageStatus(StrEnum):
    SENT = "SENT"
    HELD = "HELD"
    FAILED = "FAILED"
    DISCARDED = "DISCARDED"


class FamilyMood(StrEnum):
    GOOD = "GOOD"
    OK = "OK"
    WORRIED = "WORRIED"


class HomeChange(StrEnum):
    MOVING = "MOVING"
    HEALTH = "HEALTH"
    PARENTS_WORK = "PARENTS_WORK"
    CARING_FAMILY = "CARING_FAMILY"
    ECONOMIC = "ECONOMIC"
    OTHER = "OTHER"


class TokenPurpose(StrEnum):
    INVITATION = "INVITATION"
    PASSWORD_RESET = "PASSWORD_RESET"


class StudentStatus(StrEnum):
    ENROLLED = "ENROLLED"
    # Left the education system: the outcome the risk model tries to anticipate.
    WITHDRAWN = "WITHDRAWN"
    # Moved to another school: not a dropout.
    TRANSFERRED = "TRANSFERRED"
    GRADUATED = "GRADUATED"


class ExitReason(StrEnum):
    TRANSFER = "TRANSFER"
    WORK = "WORK"
    ECONOMIC = "ECONOMIC"
    FAMILY = "FAMILY"
    HEALTH = "HEALTH"
    PREGNANCY = "PREGNANCY"
    DISTANCE = "DISTANCE"
    DISENGAGEMENT = "DISENGAGEMENT"
    UNKNOWN = "UNKNOWN"
    GRADUATION = "GRADUATION"


class ModelAction(StrEnum):
    TRAINED = "TRAINED"
    ACTIVATED = "ACTIVATED"


class DataRequestKind(StrEnum):
    ACCESS = "ACCESS"
    RECTIFICATION = "RECTIFICATION"
    CANCELLATION = "CANCELLATION"
    OPPOSITION = "OPPOSITION"


class DataRequestStatus(StrEnum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
