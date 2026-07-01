from uuid import UUID

import asyncpg

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.domain.users import validar_rol_usuario_creacion
from app.interfaces.oferta_academica import OfertaAcademicaStub
from app.models.schemas import (
    DesactivarUsuarioResponse,
    RolUsuario,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository


def _map_user(row: asyncpg.Record) -> UserPublic:
    return UserPublic(
        id=str(row["id"]),
        email=row["email"],
        nombre=row["nombre"],
        apellido=row["apellido"],
        rol=RolUsuario(row["rol"]),
        tenant_id=str(row["id_tenant"]) if row["id_tenant"] else None,
        activo=row["activo"],
    )


class UserService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.repo = UserRepository(pool)
        self.audit_repo = AuditRepository()
        self.oferta = OfertaAcademicaStub()
        self.pool = pool

    async def create_user(
        self,
        tenant_id: UUID,
        payload: UserCreate,
        *,
        actor_id: UUID,
        actor_rol: str,
    ) -> UserPublic:
        try:
            validar_rol_usuario_creacion(rol_creador=actor_rol, rol_nuevo=payload.rol.value)
        except ValueError as exc:
            raise ForbiddenError(str(exc)) from exc

        if await self.repo.email_exists_in_tenant(tenant_id, str(payload.email)):
            raise ConflictError("Ya existe un usuario con ese correo en el tenant.")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 1. Si es ALUMNO, validar datos de perfil primero
                if payload.rol == RolUsuario.ALUMNO:
                    if not payload.id_plan_estudios or not payload.codigo_alumno or not payload.periodo_ingreso:
                        raise ValidationError("Los campos codigo_alumno, id_plan_estudios y periodo_ingreso son obligatorios para alumnos.")

                    plan_row = await conn.fetchrow(
                        "SELECT id_plan_estudios, carrera FROM plan_estudios WHERE id = $1 AND id_tenant = $2",
                        payload.id_plan_estudios,
                        tenant_id,
                    )
                    if not plan_row:
                        raise ValidationError("El plan de estudios especificado no existe o no pertenece a este tenant.")

                    carrera = plan_row["carrera"]
                    id_plan_estudios_legacy = plan_row["id_plan_estudios"]

                    codigo_exists = await conn.fetchval(
                        "SELECT 1 FROM perfil_alumno WHERE codigo_alumno = $1",
                        payload.codigo_alumno,
                    )
                    if codigo_exists:
                        raise ConflictError(f"Ya existe un alumno registrado con el código '{payload.codigo_alumno}'.")

                # 2. Crear el usuario
                row = await conn.fetchrow(
                    """
                    INSERT INTO usuarios (
                        id_tenant, email, password_hash, nombre, apellido, rol, activo
                    ) VALUES ($1, $2, $3, $4, $5, $6, TRUE)
                    RETURNING *
                    """,
                    tenant_id,
                    str(payload.email),
                    hash_password(payload.password),
                    payload.nombre,
                    payload.apellido,
                    payload.rol.value,
                )

                # 3. Si es ALUMNO, crear su perfil
                if payload.rol == RolUsuario.ALUMNO:
                    await conn.execute(
                        """
                        INSERT INTO perfil_alumno (
                            id_perfil_alumno,
                            id_usuario,
                            id_plan_estudios,
                            codigo_alumno,
                            carrera,
                            ciclo_actual,
                            periodo_ingreso
                        ) VALUES (gen_random_uuid(), $1, $2, $3, $4, 1, $5)
                        """,
                        row["id"],
                        id_plan_estudios_legacy,
                        payload.codigo_alumno,
                        carrera,
                        payload.periodo_ingreso,
                    )

                # 4. Registrar auditoría
                await self.audit_repo.registrar(
                    conn,
                    id_tenant=tenant_id,
                    id_usuario=actor_id,
                    tipo_operacion="USUARIO_CREADO",
                    entidad_afectada="usuarios",
                    id_entidad=row["id"],
                    valor_nuevo={"email": payload.email, "rol": payload.rol.value},
                )

        return _map_user(row)

    async def list_users(self, tenant_id: UUID) -> list[UserPublic]:
        rows = await self.repo.list_by_tenant(tenant_id)
        return [_map_user(row) for row in rows]

    async def get_user(self, tenant_id: UUID, user_id: UUID) -> UserPublic:
        row = await self.repo.get_by_id(user_id, tenant_id)
        if row is None:
            raise NotFoundError("Usuario no encontrado.")
        return _map_user(row)

    async def update_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        payload: UserUpdate,
        *,
        actor_id: UUID,
    ) -> UserPublic:
        existing = await self.repo.get_by_id(user_id, tenant_id)
        if existing is None:
            raise NotFoundError("Usuario no encontrado.")

        password_hash = hash_password(payload.password) if payload.password else None
        row = await self.repo.update(
            user_id,
            tenant_id,
            nombre=payload.nombre,
            apellido=payload.apellido,
            password_hash=password_hash,
        )
        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="USUARIO_ACTUALIZADO",
                entidad_afectada="usuarios",
                id_entidad=user_id,
                valor_anterior=dict(existing),
                valor_nuevo=dict(row),
            )
        return _map_user(row)

    async def desactivar_usuario(
        self,
        tenant_id: UUID,
        user_id: UUID,
        *,
        actor_id: UUID,
        confirmar: bool,
    ) -> DesactivarUsuarioResponse:
        user = await self.repo.get_by_id(user_id, tenant_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado.")
        if not user["activo"]:
            raise ConflictError("El usuario ya esta desactivado.")

        advertencias: list[str] = []
        if user["rol"] == "DOCENTE":
            async with self.pool.acquire() as conn:
                componentes = await self.oferta.obtener_componentes_activos_docente(
                    conn,
                    id_tenant=tenant_id,
                    docente_id=user_id,
                )
            if componentes:
                secciones = ", ".join(
                    c.get("codigo_seccion", str(c.get("seccion_id", "?"))) for c in componentes
                )
                advertencias.append(
                    f"El docente tiene componentes activos en las secciones: {secciones}."
                )
                if not confirmar:
                    raise ValidationError(
                        "Debe confirmar la desactivacion porque existen secciones afectadas."
                    )

        row = await self.repo.set_active(user_id, tenant_id, activo=False)
        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="USUARIO_DESACTIVADO",
                entidad_afectada="usuarios",
                id_entidad=user_id,
                valor_anterior={"activo": True},
                valor_nuevo={"activo": False},
            )

        return DesactivarUsuarioResponse(
            id=str(row["id"]),
            activo=row["activo"],
            advertencias=advertencias,
        )
