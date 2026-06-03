from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.core_schemas import Usuario, PerfilAlumno, PerfilDocente

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
