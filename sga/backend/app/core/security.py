from datetime import UTC, datetime, timedelta
from typing import Any, Optional, List
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core_schemas import Usuario, PerfilAlumno, PerfilDocente

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *,
    user_id: UUID,
    rol: str,
    tenant_id: UUID | None,
    expires_minutes: int | None = None,
) -> tuple[str, UUID, datetime]:
    settings = get_settings()
    expire_delta = timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expire_minutes
    )
    expires_at = datetime.now(UTC) + expire_delta
    jti = uuid4()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "rol": rol,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "jti": str(jti),
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token invalido o expirado.") from exc


class CurrentUser(BaseModel):
    id_usuario: str
    id_tenant: str
    rol: str
    nombre_completo: str
    id_perfil: Optional[str] = None  # id_perfil_alumno or id_perfil_docente depending on role


def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> CurrentUser:
    """
    FastAPI dependency to extract current authenticated user context.
    For development/testing, it can read headers, or default to a mock.
    """
    # If no headers provided, fallback to a default mock (e.g. for testing)
    user_id = x_user_id or "mock-user-id"
    tenant_id = x_tenant_id or "mock-tenant-id"
    role = x_user_role or "ADMINISTRADOR"  # default
    
    # We will assume a mock context if headers are not set, otherwise we construct it.
    # We will look up or stub the profile ID.
    profile_id = None
    if role == "ALUMNO":
        profile_id = f"profile-alumno-{user_id}"
    elif role == "DOCENTE":
        profile_id = f"profile-docente-{user_id}"
        
    return CurrentUser(
        id_usuario=user_id,
        id_tenant=tenant_id,
        rol=role,
        nombre_completo="Usuario Mock SGA",
        id_perfil=profile_id
    )


def require_role(roles: List[str]):
    """
    Dependency generator to check if the current user has one of the allowed roles.
    """
    def dependency(current_user: CurrentUser = Header(None)) -> CurrentUser:
        # In FastAPI route, we'll inject current_user: CurrentUser = Depends(get_current_user)
        # and manually verify inside the route or route dependency.
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(roles)}."
            )
        return current_user
    return dependency

