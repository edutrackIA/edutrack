from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession, require_roles
from app.domain import Role, User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService
from app.services.report_service import ReportService

router = APIRouter(tags=["dashboard"])

ManagementUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST))]


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    user: ManagementUser, db: DbSession, period_id: Annotated[int | None, Query()] = None
) -> DashboardSummary:
    return DashboardService(db).summary(user, period_id)


@router.get(
    "/reports/risk",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def risk_report(
    user: ManagementUser,
    db: DbSession,
    period_id: Annotated[int | None, Query()] = None,
    classroom_id: Annotated[int | None, Query()] = None,
) -> Response:
    filename, content = ReportService(db).risk_report_pdf(user, period_id, classroom_id)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
