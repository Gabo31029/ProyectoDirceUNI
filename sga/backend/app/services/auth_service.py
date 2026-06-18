from datetime import UTC
from uuid import UUID

import asyncpg

from app.core.config import get_settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.security import create_access_token, verify_password
from app.domain.auth import calcular_bloqueo, cuenta_bloqueada
from app.domain.users import validar_login_contexto
from app.models.schemas import LoginRequest, RolUsuario, TokenResponse, UserPublic
from app.repositories.audit_repository import AuditRepository
from app.repositories.auth_repository import AuthRepository


class AuthService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.auth_repo = AuthRepository(pool)
        self.audit_repo = AuditRepository()
        self.pool = pool

    async def login(self, payload: LoginRequest) -> TokenResponse:
        tenant_id: UUID | None = None
        if payload.dominio_tenant:
            tenant = await self.auth_repo.get_tenant_by_dominio(payload.dominio_tenant)
            if tenant is None:
                raise UnauthorizedError("Credenciales invalidas.")
            tenant_id = tenant["id"]

        attempts = await self.auth_repo.get_login_attempts(
            email=str(payload.email),
            tenant_id=tenant_id,
        )
        if attempts and cuenta_bloqueada(attempts["bloqueado_hasta"]):
            await self._audit_fallido(
                tenant_id=tenant_id,
                email=str(payload.email),
                motivo="Cuenta bloqueada temporalmente por intentos fallidos.",
            )
            raise ForbiddenError(
                "Cuenta bloqueada temporalmente. Intente nuevamente mas tarde."
            )

        user = await self.auth_repo.get_user_for_login(
            email=str(payload.email),
            tenant_id=tenant_id,
        )
        if user is None:
            await self._registrar_intento_fallido(str(payload.email), tenant_id)
            raise UnauthorizedError("Credenciales invalidas.")

        try:
            validar_login_contexto(
                rol=user["rol"],
                tenant_id_presente=tenant_id is not None,
                dominio_presente=payload.dominio_tenant is not None,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if not verify_password(payload.password, user["password_hash"]):
            await self._registrar_intento_fallido(str(payload.email), tenant_id, user["id"])
            raise UnauthorizedError("Credenciales invalidas.")

        await self.auth_repo.reset_login_attempts(email=str(payload.email), tenant_id=tenant_id)

        settings = get_settings()
        token, _, expires_at = create_access_token(
            user_id=user["id"],
            rol=user["rol"],
            tenant_id=user["id_tenant"],
        )

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=user["id_tenant"],
                id_usuario=user["id"],
                tipo_operacion="LOGIN_EXITOSO",
                entidad_afectada="usuarios",
                id_entidad=user["id"],
            )

        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            rol=RolUsuario(user["rol"]),
            tenant_id=str(user["id_tenant"]) if user["id_tenant"] else None,
        )

    async def logout(self, *, user_id: UUID, tenant_id: UUID | None, jti: UUID, exp: int) -> None:
        from datetime import datetime

        expira_en = datetime.fromtimestamp(exp, tz=UTC)
        await self.auth_repo.blacklist_token(jti=jti, expira_en=expira_en)
        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=user_id,
                tipo_operacion="LOGOUT",
                entidad_afectada="usuarios",
                id_entidad=user_id,
            )

    async def get_me(self, user_id: UUID) -> UserPublic:
        user = await self.auth_repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado.")
        return UserPublic(
            id=str(user["id"]),
            email=user["email"],
            nombre=user["nombre"],
            apellido=user["apellido"],
            rol=RolUsuario(user["rol"]),
            tenant_id=str(user["id_tenant"]) if user["id_tenant"] else None,
            activo=user["activo"],
        )

    async def _registrar_intento_fallido(
        self,
        email: str,
        tenant_id: UUID | None,
        user_id: UUID | None = None,
    ) -> None:
        attempts = await self.auth_repo.get_login_attempts(email=email, tenant_id=tenant_id)
        intentos = (attempts["intentos_fallidos"] if attempts else 0) + 1
        bloqueo = calcular_bloqueo(intentos)
        await self.auth_repo.upsert_failed_attempt(
            email=email,
            tenant_id=tenant_id,
            intentos=intentos,
            bloqueado_hasta=bloqueo,
        )
        motivo = "Credenciales invalidas."
        if bloqueo:
            motivo = "Cuenta bloqueada por exceso de intentos fallidos."
        await self._audit_fallido(
            tenant_id=tenant_id,
            email=email,
            user_id=user_id,
            motivo=motivo,
        )

    async def _audit_fallido(
        self,
        *,
        tenant_id: UUID | None,
        email: str,
        motivo: str,
        user_id: UUID | None = None,
    ) -> None:
        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=user_id,
                tipo_operacion="ACCESO_NO_AUTORIZADO",
                entidad_afectada="auth",
                motivo_rechazo=f"{email}: {motivo}",
            )
