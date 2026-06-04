from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import db
from app.core.dependencies import CurrentUser, require_roles, resolve_tenant_id
from app.models.schemas import (
    InscripcionCreate,
    InscripcionResponse,
    MatriculaCreate,
    MatriculaResponse,
    RetiroRequest,
)
from app.services.matricula_service import MatriculaService

router = APIRouter(prefix="/matriculas", tags=["Matricula"])
inscripciones_router = APIRouter(prefix="/inscripciones", tags=["Inscripcion"])


def _matricula_service() -> MatriculaService:
    return MatriculaService(db.connection())


@router.post("", response_model=MatriculaResponse, status_code=201)
async def crear_matricula(
    payload: MatriculaCreate,
    current_user: CurrentUser = Depends(require_roles("ALUMNO", "ADMIN")),
) -> MatriculaResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _matricula_service().crear_matricula(
        tenant_id, payload, current_user=current_user
    )


@router.get("", response_model=list[MatriculaResponse])
async def listar_matriculas(
    alumno_id: UUID = Query(..., description="Identificador del alumno"),
    current_user: CurrentUser = Depends(require_roles("ALUMNO", "ADMIN", "DOCENTE")),
) -> list[MatriculaResponse]:
    tenant_id = resolve_tenant_id(current_user)
    return await _matricula_service().list_matriculas(
        tenant_id, alumno_id=alumno_id, current_user=current_user
    )


@router.post("/{matricula_id}/inscripciones", response_model=InscripcionResponse, status_code=201)
async def inscribir_curso(
    matricula_id: UUID,
    payload: InscripcionCreate,
    current_user: CurrentUser = Depends(require_roles("ALUMNO", "ADMIN")),
) -> InscripcionResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _matricula_service().inscribir_curso(
        tenant_id, matricula_id, payload, current_user=current_user
    )


@router.get("/{matricula_id}/inscripciones", response_model=list[InscripcionResponse])
async def listar_inscripciones(
    matricula_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ALUMNO", "ADMIN", "DOCENTE")),
) -> list[InscripcionResponse]:
    tenant_id = resolve_tenant_id(current_user)
    return await _matricula_service().list_inscripciones(
        tenant_id, matricula_id, current_user=current_user
    )


@inscripciones_router.post("/{inscripcion_id}/retiro", response_model=InscripcionResponse)
async def retirar_curso(
    inscripcion_id: UUID,
    payload: RetiroRequest,
    current_user: CurrentUser = Depends(require_roles("ALUMNO", "ADMIN")),
) -> InscripcionResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _matricula_service().retirar_curso(
        tenant_id, inscripcion_id, payload, current_user=current_user
    )
