from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.dependencies import CurrentUser, require_roles, resolve_tenant_id
from app.models.schemas import (
    EscalaEvaluacionCreate,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
    TipoCatalogoCreate,
    TipoEventoCreate,
)
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def _tenant_service() -> TenantService:
    return TenantService(db.connection())


@router.get("", response_model=list[TenantResponse])
async def listar_tenants(
    _: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> list[TenantResponse]:
    return await _tenant_service().list_tenants()


@router.post("", response_model=TenantResponse, status_code=201)
async def crear_tenant(
    payload: TenantCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> TenantResponse:
    return await _tenant_service().create_tenant(payload, actor_id=current_user.id)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def obtener_tenant(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL", "ADMIN")),
) -> TenantResponse:
    resolve_tenant_id(current_user, tenant_id)
    return await _tenant_service().get_tenant(tenant_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def actualizar_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> TenantResponse:
    return await _tenant_service().update_tenant(
        tenant_id, payload, actor_id=current_user.id
    )


@router.post("/{tenant_id}/catalogos/escalas-evaluacion", status_code=201)
async def crear_escala(
    tenant_id: UUID,
    payload: EscalaEvaluacionCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> dict:
    return await _tenant_service().add_escala(
        tenant_id, payload, actor_id=current_user.id
    )


@router.get("/{tenant_id}/catalogos/escalas-evaluacion")
async def listar_escalas(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL", "ADMIN")),
) -> list[dict]:
    resolve_tenant_id(current_user, tenant_id)
    return await _tenant_service().list_escalas(tenant_id)


@router.post("/{tenant_id}/catalogos/tipos-evaluacion", status_code=201)
async def crear_tipo_evaluacion(
    tenant_id: UUID,
    payload: TipoCatalogoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> dict:
    return await _tenant_service().add_tipo_evaluacion(
        tenant_id, payload, actor_id=current_user.id
    )


@router.get("/{tenant_id}/catalogos/tipos-evaluacion")
async def listar_tipos_evaluacion(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL", "ADMIN")),
) -> list[dict]:
    resolve_tenant_id(current_user, tenant_id)
    return await _tenant_service().list_tipos_evaluacion(tenant_id)


@router.post("/{tenant_id}/catalogos/tipos-condicion", status_code=201)
async def crear_tipo_condicion(
    tenant_id: UUID,
    payload: TipoCatalogoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> dict:
    return await _tenant_service().add_tipo_condicion(
        tenant_id, payload, actor_id=current_user.id
    )


@router.get("/{tenant_id}/catalogos/tipos-condicion")
async def listar_tipos_condicion(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL", "ADMIN")),
) -> list[dict]:
    resolve_tenant_id(current_user, tenant_id)
    return await _tenant_service().list_tipos_condicion(tenant_id)


@router.post("/{tenant_id}/catalogos/tipos-evento", status_code=201)
async def crear_tipo_evento(
    tenant_id: UUID,
    payload: TipoEventoCreate,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL")),
) -> dict:
    return await _tenant_service().add_tipo_evento(
        tenant_id, payload, actor_id=current_user.id
    )


@router.get("/{tenant_id}/catalogos/tipos-evento")
async def listar_tipos_evento(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_roles("ADMIN_CENTRAL", "ADMIN")),
) -> list[dict]:
    resolve_tenant_id(current_user, tenant_id)
    return await _tenant_service().list_tipos_evento(tenant_id)
