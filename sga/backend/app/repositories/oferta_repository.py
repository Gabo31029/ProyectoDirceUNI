from uuid import UUID
from decimal import Decimal
import asyncpg


class OfertaRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    # --- Plan de Estudios ---
    async def create_plan_estudios(
        self,
        *,
        id_tenant: UUID,
        carrera: str,
        version_plan: str,
        creditos_totales: int,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO plan_estudios (id_tenant, carrera, version_plan, creditos_totales)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_tenant,
                carrera,
                version_plan,
                creditos_totales,
            )

    async def get_plan_estudios_by_id(self, plan_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM plan_estudios WHERE id = $1 AND id_tenant = $2",
                plan_id,
                tenant_id,
            )

    async def update_estado_plan_estudios(
        self,
        plan_id: UUID,
        tenant_id: UUID,
        nuevo_estado: str,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE plan_estudios
                SET estado = $3, updated_at = NOW()
                WHERE id = $1 AND id_tenant = $2
                RETURNING *
                """,
                plan_id,
                tenant_id,
                nuevo_estado,
            )

    async def list_planes_estudio(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM plan_estudios WHERE id_tenant = $1 ORDER BY carrera, version_plan DESC",
                tenant_id,
            )
            return list(rows)

    # --- Cursos ---
    async def create_curso(
        self,
        *,
        id_tenant: UUID,
        codigo_curso: str,
        nombre_curso: str,
        creditos: int,
        tipo_curso: str,
        ciclo_sugerido: int | None,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO curso (id_tenant, codigo_curso, nombre_curso, creditos, tipo_curso, ciclo_sugerido)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                id_tenant,
                codigo_curso,
                nombre_curso,
                creditos,
                tipo_curso,
                ciclo_sugerido,
            )

    async def get_curso_by_id(self, curso_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM curso WHERE id = $1 AND id_tenant = $2",
                curso_id,
                tenant_id,
            )

    async def get_curso_by_codigo(self, codigo_curso: str, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM curso WHERE codigo_curso = $1 AND id_tenant = $2",
                codigo_curso,
                tenant_id,
            )

    async def list_cursos(self, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM curso WHERE id_tenant = $1 AND activo = TRUE ORDER BY codigo_curso",
                tenant_id,
            )
            return list(rows)

    async def asociar_curso_a_plan(
        self,
        *,
        id_plan_estudios: UUID,
        id_curso: UUID,
        ciclo_en_plan: int,
        es_obligatorio: bool,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO plan_estudios_curso (id_plan_estudios, id_curso, ciclo_en_plan, es_obligatorio)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_plan_estudios,
                id_curso,
                ciclo_en_plan,
                es_obligatorio,
            )

    async def get_cursos_por_plan(self, id_plan_estudios: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.*, pc.ciclo_en_plan, pc.es_obligatorio
                FROM plan_estudios_curso pc
                JOIN curso c ON pc.id_curso = c.id
                WHERE pc.id_plan_estudios = $1
                ORDER BY pc.ciclo_en_plan, c.codigo_curso
                """,
                id_plan_estudios,
            )
            return list(rows)

    async def add_prerrequisito(
        self,
        *,
        id_curso: UUID,
        id_curso_requerido: UUID | None,
        tipo_prereq: str,
        valor_min_creditos: int | None,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO prerrequisito (id_curso, id_curso_requerido, tipo_prereq, valor_min_creditos)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_curso,
                id_curso_requerido,
                tipo_prereq,
                valor_min_creditos,
            )

    async def get_prerrequisitos_curso(self, id_curso: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM prerrequisito WHERE id_curso = $1",
                id_curso,
            )
            return list(rows)

    # --- Secciones ---
    async def create_seccion(
        self,
        *,
        id_tenant: UUID,
        id_periodo: UUID,
        id_curso: UUID,
        codigo_seccion: str,
        vacantes_maximas: int,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO seccion (id_tenant, id_periodo, id_curso, codigo_seccion, vacantes_maximas, vacantes_disponibles)
                VALUES ($1, $2, $3, $4, $5, $5)
                RETURNING *
                """,
                id_tenant,
                id_periodo,
                id_curso,
                codigo_seccion,
                vacantes_maximas,
            )

    async def get_seccion_by_id(self, seccion_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM seccion WHERE id = $1 AND id_tenant = $2",
                seccion_id,
                tenant_id,
            )

    async def get_seccion_by_codigo(
        self,
        *,
        id_periodo: UUID,
        id_curso: UUID,
        codigo_seccion: str,
    ) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT * FROM seccion
                WHERE id_periodo = $1 AND id_curso = $2 AND codigo_seccion = $3
                """,
                id_periodo,
                id_curso,
                codigo_seccion,
            )

    async def list_secciones_by_periodo(self, id_periodo: UUID, tenant_id: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT s.*, c.codigo_curso, c.nombre_curso, c.creditos
                FROM seccion s
                JOIN curso c ON s.id_curso = c.id
                WHERE s.id_periodo = $1 AND s.id_tenant = $2
                ORDER BY c.codigo_curso, s.codigo_seccion
                """,
                id_periodo,
                tenant_id,
            )
            return list(rows)

    # --- Asignaciones Docente ---
    async def create_asignacion_docente(
        self,
        *,
        id_seccion: UUID,
        id_usuario_docente: UUID,
        id_tipo_componente: UUID,
        es_coordinador: bool,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO asignacion_docente_seccion (
                    id_seccion, id_usuario_docente, id_tipo_componente, es_coordinador
                ) VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                id_seccion,
                id_usuario_docente,
                id_tipo_componente,
                es_coordinador,
            )

    async def get_docente_by_id_and_tenant(self, docente_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM usuarios WHERE id = $1 AND id_tenant = $2 AND rol = 'DOCENTE'",
                docente_id,
                tenant_id,
            )

    # --- Componentes Evaluacion ---
    async def create_componente_evaluacion(
        self,
        *,
        id_seccion: UUID,
        id_tipo_componente: UUID,
        id_escala: UUID,
        peso_relative: Decimal,
        orden_presentacion: int | None,
    ) -> asyncpg.Record:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """
                INSERT INTO componente_evaluacion (
                    id_seccion, id_tipo_componente, id_escala, peso_relativo, orden_presentacion, estado
                ) VALUES ($1, $2, $3, $4, $5, 'BORRADOR')
                RETURNING *
                """,
                id_seccion,
                id_tipo_componente,
                id_escala,
                peso_relative,
                orden_presentacion,
            )

    async def get_escala_by_id_and_tenant(self, escala_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM cat_escala_evaluacion WHERE id = $1 AND id_tenant = $2",
                escala_id,
                tenant_id,
            )

    async def list_componentes_by_seccion(self, id_seccion: UUID) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM componente_evaluacion WHERE id_seccion = $1 ORDER BY orden_presentacion, created_at",
                id_seccion,
            )
            return list(rows)

    async def desasociar_curso_de_plan(
        self,
        *,
        id_plan_estudios: UUID,
        id_curso: UUID,
    ) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM plan_estudios_curso WHERE id_plan_estudios = $1 AND id_curso = $2",
                id_plan_estudios,
                id_curso,
            )
            return result != "DELETE 0"

