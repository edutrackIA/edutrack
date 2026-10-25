from datetime import UTC, date, datetime, timedelta, timezone

# Peru does not use daylight saving time, so a fixed offset is exact and avoids
# depending on the operating system's time zone database.
SCHOOL_TZ = timezone(timedelta(hours=-5), "America/Lima")


def utcnow() -> datetime:
    """Current UTC time as a naive datetime, matching how timestamps are stored."""
    return datetime.now(UTC).replace(tzinfo=None)


def school_today() -> date:
    """Today's date at the school (Lima)."""
    return datetime.now(SCHOOL_TZ).date()


def week_start(day: date) -> date:
    """Monday of the week that contains `day`."""
    return day - timedelta(days=day.weekday())


def week_deadline(start: date) -> date:
    """Last day a weekly check-in can be edited: Saturday of that week."""
    return start + timedelta(days=5)
