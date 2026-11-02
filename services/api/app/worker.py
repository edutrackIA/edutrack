"""Scheduled jobs. `python -m app.worker serve` runs the scheduler; `run` executes one job.

Example: python -m app.worker run weekly-attendance --date 2026-10-31
"""

import argparse
import logging
from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.time import SCHOOL_TZ, school_today
from app.services.jobs.family_reports import (
    perfect_attendance,
    period_grades,
    weekly_attendance,
)
from app.services.jobs.tutor_reminders import remind_pending_checkins, report_missed_checkins
from app.services.notifications.email_sender import EmailSender, get_email_sender

logger = logging.getLogger("edutrack.worker")

Job = Callable[[Session, EmailSender, date], int]

# name: (job, cron schedule in Lima time)
JOBS: dict[str, tuple[Job, dict[str, str]]] = {
    "checkin-reminders": (remind_pending_checkins, {"day_of_week": "fri", "hour": "9"}),
    "missed-checkins": (report_missed_checkins, {"day_of_week": "sun", "hour": "20"}),
    "weekly-attendance": (weekly_attendance, {"day_of_week": "sat", "hour": "10"}),
    "perfect-attendance": (perfect_attendance, {"day": "1", "hour": "8"}),
    "period-grades": (period_grades, {"hour": "7"}),
}


def run_job(name: str, today: date | None = None) -> int:
    job, _ = JOBS[name]
    with SessionLocal() as db:
        count = job(db, get_email_sender(), today or school_today())
    logger.info("Job %s finished: %s emails", name, count)
    return count


def serve() -> None:
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler(timezone=SCHOOL_TZ)
    for name, (_, schedule) in JOBS.items():
        scheduler.add_job(run_job, "cron", args=[name], id=name, minute="0", **schedule)
        logger.info("Scheduled %s: %s", name, schedule)
    scheduler.start()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="EduTrack scheduled jobs")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="run the scheduler")
    run = commands.add_parser("run", help="run one job now")
    run.add_argument("job", choices=sorted(JOBS))
    run.add_argument("--date", type=date.fromisoformat, help="pretend today is this date")
    args = parser.parse_args()

    if args.command == "serve":
        serve()
    else:
        run_job(args.job, args.date)


if __name__ == "__main__":
    main()
