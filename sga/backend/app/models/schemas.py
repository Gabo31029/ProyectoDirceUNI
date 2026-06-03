from enum import Enum

from pydantic import BaseModel, Field


class RolUsuario(str, Enum):
    ADMIN_CENTRAL = "ADMIN_CENTRAL"
    ADMIN = "ADMIN"
    DOCENTE = "DOCENTE"
    ALUMNO = "ALUMNO"


class TenantEstado(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    dominio_tenant: str | None = Field(
        default=None,
        description="Dominio del tenant. Obligatorio para usuarios institucionales.",
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    rol: RolUsuario
    tenant_id: str | None = None


class UserPublic(BaseModel):
    id: str
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nombre: str
    apellido: str
    rol: RolUsuario
    tenant_id: str | None
    activo: bool


class TenantCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=255)
    dominio: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    zona_horaria: str = Field(default="America/Lima", max_length=64)


class TenantUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=255)
    zona_horaria: str | None = Field(default=None, max_length=64)
    estado: TenantEstado | None = None


class TenantResponse(BaseModel):
    id: str
    nombre: str
    dominio: str
    zona_horaria: str
    estado: TenantEstado


class EscalaEvaluacionCreate(BaseModel):
    nombre_escala: str
    nota_minima: float
    nota_maxima: float
    nota_aprobatoria: float


class TipoCatalogoCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None


class TipoEventoCreate(TipoCatalogoCreate):
    cuenta_objetivo: str | None = None
    operacion: str | None = Field(default=None, pattern=r"^(INCREMENTO|DECREMENTO|ASIGNACION)$")


class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    nombre: str = Field(min_length=2, max_length=255)
    apellido: str = Field(min_length=2, max_length=255)
    rol: RolUsuario = Field(default=RolUsuario.ALUMNO)


class UserUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=255)
    apellido: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8)


class DesactivarUsuarioRequest(BaseModel):
    confirmar: bool = False


class DesactivarUsuarioResponse(BaseModel):
    id: str
    activo: bool
    advertencias: list[str] = Field(default_factory=list)
