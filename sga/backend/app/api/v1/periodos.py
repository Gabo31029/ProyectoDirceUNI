from uuid import UUID
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.dependencies import CurrentUser, require_roles, resolve_tenant_id
from app.models.schemas import (
    PeriodoAcademicoCreate,
    PeriodoAcademicoResponse,
    PeriodoAcademicoTransition,
    PoliticaCreditoCreate,
    PoliticaCondicionCreate,
    PoliticaRetiroCreate,
    PoliticaReservaCreate,
    FormulaPromedioCreate,
    PoliticaDispersionCreate,
    PoliticaTurnoCreate,
    PoliticaTurnoResponse,
)
from app.services.periodo_service import PeriodoService

router = APIRouter(prefix="/periodos", tags=["Periodos Académicos"])


def _periodo_service() -> PeriodoService:
    return PeriodoService(db.connection())


@router.post("", response_model=PeriodoAcademicoResponse, status_code=201)
async def crear_periodo(
    payload: PeriodoAcademicoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> PeriodoAcademicoResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().crear_periodo(tenant_id, payload, actor_id=current_user.id)


@router.get("", response_model=list[PeriodoAcademicoResponse])
async def listar_periodos(
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> list[PeriodoAcademicoResponse]:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().list_periodos(tenant_id)


@router.get("/activo", response_model=PeriodoAcademicoResponse)
async def obtener_periodo_activo(
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> PeriodoAcademicoResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().get_periodo_activo(tenant_id)


@router.get("/{periodo_id}", response_model=PeriodoAcademicoResponse)
async def obtener_periodo(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "DOCENTE", "ALUMNO")),
) -> PeriodoAcademicoResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().get_periodo(periodo_id, tenant_id)


@router.post("/{periodo_id}/transicion", response_model=PeriodoAcademicoResponse)
async def transicionar_periodo(
    periodo_id: UUID,
    payload: PeriodoAcademicoTransition,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> PeriodoAcademicoResponse:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().transicionar_periodo(
        tenant_id, periodo_id, payload.estado_nuevo, actor_id=current_user.id
    )


# --- Politicas Credito ---
@router.post("/{periodo_id}/politicas-credito", status_code=201)
async def crear_politica_credito(
    periodo_id: UUID,
    payload: PoliticaCreditoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_politica_credito(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/politicas-credito")
async def listar_politicas_credito(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ALUMNO")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().list_politicas_credito(tenant_id, periodo_id)


# --- Politicas Condicion ---
@router.post("/{periodo_id}/politicas-condicion", status_code=201)
async def crear_politica_condicion(
    periodo_id: UUID,
    payload: PoliticaCondicionCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_politica_condicion(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/politicas-condicion")
async def listar_politicas_condicion(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ALUMNO")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().list_politicas_condicion(tenant_id, periodo_id)


# --- Politicas Retiro ---
@router.post("/{periodo_id}/politicas-retiro", status_code=201)
async def crear_politica_retiro(
    periodo_id: UUID,
    payload: PoliticaRetiroCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_politica_retiro(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/politicas-retiro")
async def listar_politicas_retiro(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ALUMNO")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().list_politicas_retiro(tenant_id, periodo_id)


# --- Politicas Reserva ---
@router.post("/{periodo_id}/politicas-reserva", status_code=201)
async def crear_politica_reserva(
    periodo_id: UUID,
    payload: PoliticaReservaCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_politica_reserva(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/politicas-reserva")
async def obtener_politica_reserva(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ALUMNO")),
) -> dict | None:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().get_politica_reserva(tenant_id, periodo_id)


# --- Formula Promedio ---
@router.post("/{periodo_id}/formulas-promedio", status_code=201)
async def crear_formula_promedio(
    periodo_id: UUID,
    payload: FormulaPromedioCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_formula_promedio(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/formulas-promedio")
async def listar_formulas_promedio(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().list_formulas_promedio(tenant_id, periodo_id)


# --- Politicas Dispersion ---
@router.post("/{periodo_id}/politicas-dispersion", status_code=201)
async def crear_politica_dispersion(
    periodo_id: UUID,
    payload: PoliticaDispersionCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_politica_dispersion(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/politicas-dispersion")
async def obtener_politica_dispersion(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ALUMNO")),
) -> dict | None:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().get_politica_dispersion(tenant_id, periodo_id)


# --- Politicas Turno Matricula ---
@router.post("/{periodo_id}/politicas-turno", status_code=201)
async def crear_politica_turno(
    periodo_id: UUID,
    payload: PoliticaTurnoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().add_politica_turno(
        tenant_id, periodo_id, payload.model_dump(), actor_id=current_user.id
    )


@router.get("/{periodo_id}/politicas-turno")
async def listar_politicas_turno(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ALUMNO")),
) -> list[dict]:
    tenant_id = resolve_tenant_id(current_user)
    return await _periodo_service().list_politicas_turno(tenant_id, periodo_id)


@router.delete("/{periodo_id}/politicas-turno", status_code=204)
async def limpiar_politicas_turno(
    periodo_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN")),
) -> None:
    tenant_id = resolve_tenant_id(current_user)
    await _periodo_service().clear_politicas_turno(tenant_id, periodo_id)
