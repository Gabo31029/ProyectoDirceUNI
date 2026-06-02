from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import db
from app.core.exceptions import ForbiddenError
from app.core.security import decode_access_token
from app.repositories.auth_repository import AuthRepository

bearer_scheme = HTTPBearer(auto_error=False)

ROLES_ADMIN_CENTRAL = {"ADMIN_CENTRAL"}
ROLES_ADMIN = {"ADMIN", "ADMIN_CENTRAL"}
ROLES_GESTION_USUARIOS = {"ADMIN", "ADMIN_CENTRAL"}


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    rol: str
    tenant_id: UUID | None
    jti: UUID


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticacion requeridas.",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    auth_repo = AuthRepository(db.connection())
    if await auth_repo.is_token_blacklisted(UUID(payload["jti"])):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesion ha sido cerrada.",
        )

    return CurrentUser(
        id=UUID(payload["sub"]),
        rol=payload["rol"],
        tenant_id=UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
        jti=UUID(payload["jti"]),
    )


def require_roles(*roles: str):
    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para esta operacion.",
            )
        return current_user

    return _checker


def require_tenant_context(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.tenant_id is None and current_user.rol != "ADMIN_CENTRAL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contexto institucional no disponible.",
        )
    return current_user


def resolve_tenant_id(current_user: CurrentUser, requested_tenant_id: UUID | None = None) -> UUID:
    """RF-TNT-03: el tenant viene del JWT, no del request."""
    if current_user.rol == "ADMIN_CENTRAL":
        if requested_tenant_id is None:
            raise ForbiddenError("Debe indicar el tenant objetivo.")
        return requested_tenant_id
    if current_user.tenant_id is None:
        raise ForbiddenError("Contexto institucional invalido.")
    if requested_tenant_id and requested_tenant_id != current_user.tenant_id:
        raise ForbiddenError("No puede acceder a datos de otro tenant.")
    return current_user.tenant_id
