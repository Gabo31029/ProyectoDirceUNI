from uuid import UUID

import asyncpg


class TenantRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        *,
        nombre: str,
        dominio: str,
        zona_horaria: str,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO tenants (nombre, dominio, zona_horaria)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                nombre,
                dominio,
                zona_horaria,
            )

    async def list_all(self) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tenants ORDER BY nombre")
            return list(rows)

    async def get_by_id(self, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)

    async def get_by_dominio(self, dominio: str) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM tenants WHERE dominio = $1", dominio)

    async def update(
        self,
        tenant_id: UUID,
        *,
        nombre: str | None,
        zona_horaria: str | None,
        estado: str | None,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE tenants
                SET
                    nombre = COALESCE($2, nombre),
                    zona_horaria = COALESCE($3, zona_horaria),
                    estado = COALESCE($4, estado),
                    updated_at = NOW()
                WHERE id = $1
                RETURNING *
                """,
                tenant_id,
                nombre,
                zona_horaria,
                estado,
            )

    async def create_escala(
        self,
        tenant_id: UUID,
        *,
        nombre_escala: str,
        nota_minima: float,
        nota_maxima: float,
        nota_aprobatoria: float,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO cat_escala_evaluacion (
                    id_tenant, nombre_escala, nota_minima, nota_maxima, nota_aprobatoria
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                tenant_id,
                nombre_escala,
                nota_minima,
                nota_maxima,
                nota_aprobatoria,
            )

    async def list_escalas(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM cat_escala_evaluacion WHERE id_tenant = $1 ORDER BY nombre_escala",
                tenant_id,
            )
            return list(rows)

    async def create_tipo_componente(
        self, tenant_id: UUID, *, codigo: str, nombre: str
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO cat_tipo_componente (id_tenant, codigo, nombre)
                VALUES ($1, $2, $3) RETURNING *
                """,
                tenant_id,
                codigo,
                nombre,
            )

    async def list_tipos_componente(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM cat_tipo_componente WHERE id_tenant = $1 ORDER BY codigo",
                tenant_id,
            )
            return list(rows)

    async def create_tipo_condicion(
        self,
        tenant_id: UUID,
        *,
        codigo: str,
        nombre: str,
        descripcion: str | None,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO cat_tipo_condicion (id_tenant, codigo, nombre, descripcion)
                VALUES ($1, $2, $3, $4) RETURNING *
                """,
                tenant_id,
                codigo,
                nombre,
                descripcion,
            )

    async def list_tipos_condicion(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM cat_tipo_condicion WHERE id_tenant = $1 ORDER BY codigo",
                tenant_id,
            )
            return list(rows)

    async def create_tipo_evento(
        self,
        tenant_id: UUID,
        *,
        codigo: str,
        nombre: str,
        descripcion: str | None,
        cuenta_objetivo: str | None,
        operacion: str | None,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO cat_tipo_evento (
                    id_tenant, codigo, nombre, cuenta_objetivo, operacion
                ) VALUES ($1, $2, $3, $4, $5) RETURNING *
                """,
                tenant_id,
                codigo,
                nombre,
                cuenta_objetivo,
                operacion,
            )

    async def list_tipos_evento(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM cat_tipo_evento WHERE id_tenant = $1 ORDER BY codigo",
                tenant_id,
            )
            return list(rows)
