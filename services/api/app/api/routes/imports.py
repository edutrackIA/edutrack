from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.api.deps import DbSession, require_roles
from app.domain import ImportKind, Role, User
from app.schemas.imports import ImportJobResponse
from app.services import import_service
from app.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["imports"])

AnalystUser = Annotated[User, Depends(require_roles(Role.ANALYST))]


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=ImportJobResponse)
def create_import(
    user: AnalystUser,
    db: DbSession,
    kind: Annotated[ImportKind, Form()],
    file: Annotated[UploadFile, File()],
    period_id: Annotated[int | None, Form()] = None,
) -> ImportJobResponse:
    content = file.file.read(import_service.MAX_UPLOAD_BYTES + 1)
    job = ImportService(db).run(
        user, kind=kind, filename=file.filename or "", content=content, period_id=period_id
    )
    return ImportJobResponse.model_validate(job)


@router.get("/templates/{kind}")
def download_template(kind: ImportKind, _: AnalystUser) -> Response:
    return Response(
        content=import_service.TEMPLATES[kind],
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{kind.value.lower()}.csv"'},
    )


@router.get("/{import_id}", response_model=ImportJobResponse)
def get_import(import_id: int, user: AnalystUser, db: DbSession) -> ImportJobResponse:
    return ImportJobResponse.model_validate(ImportService(db).get(user, import_id))
