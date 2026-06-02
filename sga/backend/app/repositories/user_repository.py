from uuid import UUID

import asyncpg


class UserRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        *,
        tenant_id: UUID,
        email: str,
        password_hash: str,
        nombre: str,
        apellido: str,
        rol: str,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO usuarios (
                    id_tenant, email, password_hash, nombre, apellido, rol, activo
                ) VALUES ($1, $2, $3, $4, $5, $6, TRUE)
                RETURNING *
                """,
                tenant_id,
                email,
                password_hash,
                nombre,
                apellido,
                rol,
            )

    async def list_by_tenant(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, email, nombre, apellido, rol, id_tenant, activo
                FROM usuarios
                WHERE id_tenant = $1
                ORDER BY apellido, nombre
                """,
                tenant_id,
            )
            return list(rows)

    async def get_by_id(self, user_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT id, email, nombre, apellido, rol, id_tenant, activo
                FROM usuarios
                WHERE id = $1 AND id_tenant = $2
                """,
                user_id,
                tenant_id,
            )

    async def update(
        self,
        user_id: UUID,
        tenant_id: UUID,
        *,
        nombre: str | None,
        apellido: str | None,
        password_hash: str | None,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE usuarios
                SET
                    nombre = COALESCE($3, nombre),
                    apellido = COALESCE($4, apellido),
                    password_hash = COALESCE($5, password_hash),
                    updated_at = NOW()
                WHERE id = $1 AND id_tenant = $2
                RETURNING id, email, nombre, apellido, rol, id_tenant, activo
                """,
                user_id,
                tenant_id,
                nombre,
                apellido,
                password_hash,
            )

    async def set_active(
        self,
        user_id: UUID,
        tenant_id: UUID,
        *,
        activo: bool,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE usuarios
                SET activo = $3, updated_at = NOW()
                WHERE id = $1 AND id_tenant = $2
                RETURNING id, email, nombre, apellido, rol, id_tenant, activo
                """,
                user_id,
                tenant_id,
                activo,
            )

    async def email_exists_in_tenant(self, tenant_id: UUID, email: str) -> bool:
        async with self.pool.acquire() as conn:
            val = await conn.fetchval(
                "SELECT 1 FROM usuarios WHERE id_tenant = $1 AND email = $2",
                tenant_id,
                email,
            )
            return val is not None
