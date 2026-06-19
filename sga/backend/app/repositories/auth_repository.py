from datetime import UTC, datetime
from uuid import UUID

import asyncpg


class AuthRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_tenant_by_dominio(self, dominio: str) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM tenants WHERE dominio = $1 AND estado = 'ACTIVO'",
                dominio,
            )

    async def get_user_for_login(
        self,
        *,
        email: str,
        tenant_id: UUID | None,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            if tenant_id is None:
                return await conn.fetchrow(
                    """
                    SELECT * FROM usuarios
                    WHERE email = $1 AND id_tenant IS NULL AND activo = TRUE
                    """,
                    email,
                )
            return await conn.fetchrow(
                """
                SELECT * FROM usuarios
                WHERE email = $1 AND id_tenant = $2 AND activo = TRUE
                """,
                email,
                tenant_id,
            )

    async def get_login_attempts(
        self,
        *,
        email: str,
        tenant_id: UUID | None,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT * FROM intentos_login
                WHERE email = $1
                  AND (
                    (id_tenant IS NULL AND $2::uuid IS NULL)
                    OR id_tenant = $2
                  )
                """,
                email,
                tenant_id,
            )

    async def upsert_failed_attempt(
        self,
        *,
        email: str,
        tenant_id: UUID | None,
        intentos: int,
        bloqueado_hasta: datetime | None,
    ) -> None:
        async with self.pool.acquire() as conn:
            existing = await self.get_login_attempts(email=email, tenant_id=tenant_id)
            if existing:
                await conn.execute(
                    """
                    UPDATE intentos_login
                    SET intentos_fallidos = $2,
                        bloqueado_hasta = $3,
                        updated_at = NOW()
                    WHERE id = $1
                    """,
                    existing["id"],
                    intentos,
                    bloqueado_hasta,
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO intentos_login (email, id_tenant, intentos_fallidos, bloqueado_hasta)
                    VALUES ($1, $2, $3, $4)
                    """,
                    email,
                    tenant_id,
                    intentos,
                    bloqueado_hasta,
                )

    async def reset_login_attempts(self, *, email: str, tenant_id: UUID | None) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM intentos_login
                WHERE email = $1
                  AND (
                    (id_tenant IS NULL AND $2::uuid IS NULL)
                    OR id_tenant = $2
                  )
                """,
                email,
                tenant_id,
            )

    async def blacklist_token(self, *, jti: UUID, expira_en: datetime) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO token_blacklist (jti, expira_en) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                str(jti),
                expira_en,
            )

    async def is_token_blacklisted(self, jti: UUID) -> bool:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM token_blacklist WHERE jti = $1 AND expira_en > NOW()",
                str(jti),
            )
            return row is not None

    async def get_user_by_id(self, user_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM usuarios WHERE id = $1", user_id)
