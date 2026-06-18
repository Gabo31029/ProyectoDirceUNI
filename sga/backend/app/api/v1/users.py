from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import db
from app.core.dependencies import CurrentUser, require_roles, resolve_tenant_id
from app.models.schemas import (
    DesactivarUsuarioRequest,
    DesactivarUsuarioResponse,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _user_service() -> UserService:
    return UserService(db.connection())


@router.get("", response_model=list[UserPublic])
async def listar_usuarios(
    tenant_id: UUID | None = Query(default=None, description="Requerido para ADMIN_CENTRAL"),
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ADMIN_CENTRAL")),
) -> list[UserPublic]:
    effective_tenant = resolve_tenant_id(current_user, tenant_id)
    return await _user_service().list_users(effective_tenant)


@router.post("", response_model=UserPublic, status_code=201)
async def crear_usuario(
    payload: UserCreate,
    tenant_id: UUID | None = Query(default=None, description="Requerido para ADMIN_CENTRAL"),
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ADMIN_CENTRAL")),
) -> UserPublic:
    effective_tenant = resolve_tenant_id(current_user, tenant_id)
    return await _user_service().create_user(
        effective_tenant,
        payload,
        actor_id=current_user.id,
        actor_rol=current_user.rol,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def obtener_usuario(
    user_id: UUID,
    tenant_id: UUID | None = Query(default=None, description="Requerido para ADMIN_CENTRAL"),
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ADMIN_CENTRAL")),
) -> UserPublic:
    effective_tenant = resolve_tenant_id(current_user, tenant_id)
    return await _user_service().get_user(effective_tenant, user_id)


@router.put("/{user_id}", response_model=UserPublic)
async def actualizar_usuario(
    user_id: UUID,
    payload: UserUpdate,
    tenant_id: UUID | None = Query(default=None, description="Requerido para ADMIN_CENTRAL"),
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ADMIN_CENTRAL")),
) -> UserPublic:
    effective_tenant = resolve_tenant_id(current_user, tenant_id)
    return await _user_service().update_user(
        effective_tenant, user_id, payload, actor_id=current_user.id
    )


@router.patch("/{user_id}/desactivar", response_model=DesactivarUsuarioResponse)
async def desactivar_usuario(
    user_id: UUID,
    payload: DesactivarUsuarioRequest,
    tenant_id: UUID | None = Query(default=None, description="Requerido para ADMIN_CENTRAL"),
    current_user: CurrentUser = Depends(require_roles("ADMIN", "ADMIN_CENTRAL")),
) -> DesactivarUsuarioResponse:
    effective_tenant = resolve_tenant_id(current_user, tenant_id)
    return await _user_service().desactivar_usuario(
        effective_tenant,
        user_id,
        actor_id=current_user.id,
        confirmar=payload.confirmar,
    )
