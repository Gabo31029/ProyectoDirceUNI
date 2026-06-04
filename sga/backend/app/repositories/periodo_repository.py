from uuid import UUID
from datetime import date
from decimal import Decimal
import asyncpg


class PeriodoRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        *,
        id_tenant: UUID,
        nombre_periodo: str,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO periodo_academico (id_tenant, nombre_periodo, fecha_inicio, fecha_fin)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_tenant,
                nombre_periodo,
                fecha_inicio,
                fecha_fin,
            )

    async def get_by_id(self, periodo_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM periodo_academico WHERE id = $1 AND id_tenant = $2",
                periodo_id,
                tenant_id,
            )

    async def get_activo_by_tenant(self, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT * FROM periodo_academico
                WHERE id_tenant = $1 AND estado IN ('MATRICULA', 'REGISTRO_NOTAS')
                """,
                tenant_id,
            )

    async def list_by_tenant(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM periodo_academico WHERE id_tenant = $1 ORDER BY fecha_inicio DESC",
                tenant_id,
            )
            return list(rows)

    async def update_estado(
        self,
        periodo_id: UUID,
        tenant_id: UUID,
        nuevo_estado: str,
        actor_id: UUID,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE periodo_academico
                SET
                    estado = $3,
                    fecha_estado_actual = NOW(),
                    id_usuario_transicion = $4,
                    updated_at = NOW()
                WHERE id = $1 AND id_tenant = $2
                RETURNING *
                """,
                periodo_id,
                tenant_id,
                nuevo_estado,
                actor_id,
            )

    # --- Politicas Credito ---
    async def create_politica_credito(
        self,
        *,
        id_periodo: UUID,
        ppa_minimo: Decimal,
        ppa_maximo: Decimal,
        creditos_maximos: int,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO politica_credito (id_periodo, ppa_minimo, ppa_maximo, creditos_maximos)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_periodo,
                ppa_minimo,
                ppa_maximo,
                creditos_maximos,
            )

    async def get_politicas_credito_by_periodo(self, id_periodo: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM politica_credito WHERE id_periodo = $1 ORDER BY ppa_minimo",
                id_periodo,
            )
            return list(rows)

    # --- Politicas Condicion Academica ---
    async def create_politica_condicion(
        self,
        *,
        id_periodo: UUID,
        id_tipo_condicion: UUID,
        cuenta_evaluada: str,
        umbral: Decimal,
        operador: str,
        accion_resultante: str,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO politica_condicion_academica (
                    id_periodo, id_tipo_condicion, cuenta_evaluada, umbral, operador, accion_resultante
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                id_periodo,
                id_tipo_condicion,
                cuenta_evaluada,
                umbral,
                operador,
                accion_resultante,
            )

    async def get_politicas_condicion_by_periodo(self, id_periodo: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM politica_condicion_academica WHERE id_periodo = $1",
                id_periodo,
            )
            return list(rows)

    # --- Politicas Retiro ---
    async def create_politica_retiro(
        self,
        *,
        id_periodo: UUID,
        tipo_retiro: str,
        semana_limite: int,
        condiciones_bloqueantes: str | None,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO politica_retiro (id_periodo, tipo_retiro, semana_limite, condiciones_bloqueantes)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_periodo,
                tipo_retiro,
                semana_limite,
                condiciones_bloqueantes,
            )

    async def get_politicas_retiro_by_periodo(self, id_periodo: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM politica_retiro WHERE id_periodo = $1",
                id_periodo,
            )
            return list(rows)

    # --- Politicas Reserva ---
    async def create_politica_reserva(
        self,
        *,
        id_periodo: UUID,
        max_periodos_consecutivos: int,
        max_periodos_alternos: int,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO politica_reserva (id_periodo, max_periodos_consecutivos, max_periodos_alternos)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                id_periodo,
                max_periodos_consecutivos,
                max_periodos_alternos,
            )

    async def get_politica_reserva_by_periodo(self, id_periodo: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM politica_reserva WHERE id_periodo = $1",
                id_periodo,
            )

    # --- Formula Promedio ---
    async def create_formula_promedio(
        self,
        *,
        id_periodo: UUID,
        tipo_promedio: str,
        expresion_calculo: str,
        regla_inclusion: str,
        version_formula: str,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO formula_promedio (
                    id_periodo, tipo_promedio, expresion_calculo, regla_inclusion, version_formula
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                id_periodo,
                tipo_promedio,
                expresion_calculo,
                regla_inclusion,
                version_formula,
            )

    async def get_formulas_promedio_by_periodo(self, id_periodo: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM formula_promedio WHERE id_periodo = $1",
                id_periodo,
            )
            return list(rows)

    # --- Politicas Dispersion ---
    async def create_politica_dispersion(
        self,
        *,
        id_periodo: UUID,
        ciclos_max_dispersion: int,
        prioridad_ciclo_atrasado: bool,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO politica_dispersion (id_periodo, ciclos_max_dispersion, prioridad_ciclo_atrasado)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                id_periodo,
                ciclos_max_dispersion,
                prioridad_ciclo_atrasado,
            )

    async def get_politica_dispersion_by_periodo(self, id_periodo: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM politica_dispersion WHERE id_periodo = $1",
                id_periodo,
            )
