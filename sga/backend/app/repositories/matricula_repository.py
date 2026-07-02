from uuid import UUID
from datetime import datetime

import asyncpg


class MatriculaRepository:
    """
    Repositorio de datos para el módulo de matrícula e inscripciones.
    Maneja consultas e inserciones directas a PostgreSQL utilizando asyncpg.
    """
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def get_alumno(self, alumno_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        """Obtiene un alumno activo por su ID y Tenant de la tabla de usuarios."""
        return await self.pool.fetchrow(
            """
            SELECT id, email, nombre, apellido, rol, id_tenant, activo
            FROM usuarios
            WHERE id = $1 AND id_tenant = $2 AND rol = 'ALUMNO'
            """,
            alumno_id,
            tenant_id,
        )

    async def get_periodo(self, periodo_id: UUID, tenant_id: UUID) -> asyncpg.Record | None:
        """Obtiene la información de un período académico específico."""
        return await self.pool.fetchrow(
            "SELECT * FROM periodo_academico WHERE id = $1 AND id_tenant = $2",
            periodo_id,
            tenant_id,
        )

    async def get_matricula_by_id(
        self, matricula_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        return await self.pool.fetchrow(
            "SELECT * FROM matricula WHERE id = $1 AND id_tenant = $2",
            matricula_id,
            tenant_id,
        )

    async def get_matricula_alumno_periodo(
        self, alumno_id: UUID, periodo_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        return await self.pool.fetchrow(
            """
            SELECT * FROM matricula
            WHERE id_alumno = $1 AND id_periodo = $2 AND id_tenant = $3
            """,
            alumno_id,
            periodo_id,
            tenant_id,
        )

    async def list_matriculas_by_alumno(
        self, alumno_id: UUID, tenant_id: UUID
    ) -> list[asyncpg.Record]:
        rows = await self.pool.fetch(
            """
            SELECT * FROM matricula
            WHERE id_alumno = $1 AND id_tenant = $2
            ORDER BY fecha_matricula DESC
            """,
            alumno_id,
            tenant_id,
        )
        return list(rows)

    async def get_max_creditos_turno(self, periodo_id: UUID, numero_turno: int) -> int | None:
        return await self.pool.fetchval(
            """
            SELECT creditos_maximos FROM politica_turno_matricula 
            WHERE id_periodo = $1 AND numero_turno = $2
            """,
            periodo_id,
            numero_turno,
        )

    async def calcular_turno_para_alumno(self, tenant_id: UUID, id_periodo: UUID, alumno_id: UUID) -> tuple[int, datetime | None]:
        # 1. Obtener políticas de turnos
        turn_policies = await self.pool.fetch(
            """
            SELECT numero_turno, fecha_hora_inicio
            FROM politica_turno_matricula
            WHERE id_periodo = $1
            ORDER BY numero_turno ASC
            """,
            id_periodo,
        )
        if not turn_policies:
            return 1, None # Turno 1 por defecto, sin restricciones de horario
            
        # Verificar si el alumno tiene condición activa de RIESGO_ACADEMICO
        in_risk = await self.pool.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM condicion_academica_alumno caa
                JOIN tipo_condicion_academica tca ON caa.id_tipo_condicion = tca.id_tipo_condicion
                JOIN perfil_alumno pa ON pa.id_perfil_alumno = caa.id_perfil_alumno
                WHERE pa.id_usuario = $1
                  AND caa.estado = 'ACTIVA'
                  AND tca.codigo = 'RIESGO_ACADEMICO'
            )
            """,
            alumno_id,
        )
        if in_risk:
            # Los alumnos en riesgo se matriculan siempre en el primer turno
            return 1, turn_policies[0]["fecha_hora_inicio"]

        # 2. Obtener alumnos activos ordenados por PPA desc (excluyendo riesgo académico)
        students = await self.pool.fetch(
            """
            SELECT pa.id_usuario, 
                   COALESCE((SELECT ppa FROM snapshot_promedio WHERE id_perfil_alumno = pa.id_perfil_alumno ORDER BY created_at DESC LIMIT 1), 14.00) as ppa
            FROM perfil_alumno pa
            JOIN usuarios u ON u.id = pa.id_usuario
            WHERE u.id_tenant = $1 AND u.activo = TRUE
              AND NOT EXISTS (
                  SELECT 1
                  FROM condicion_academica_alumno caa
                  JOIN tipo_condicion_academica tca ON caa.id_tipo_condicion = tca.id_tipo_condicion
                  WHERE caa.id_perfil_alumno = pa.id_perfil_alumno
                    AND caa.estado = 'ACTIVA'
                    AND tca.codigo = 'RIESGO_ACADEMICO'
              )
            ORDER BY ppa DESC, pa.codigo_alumno ASC
            """,
            tenant_id,
        )
        
        # 3. Buscar el índice del alumno
        idx = -1
        for i, s in enumerate(students):
            if s["id_usuario"] == alumno_id:
                idx = i
                break
                
        if idx == -1:
            return 1, turn_policies[0]["fecha_hora_inicio"]
            
        # 4. Calcular el turno correspondiente
        import math
        N = len(turn_policies)
        total_students = len(students)
        students_per_turn = math.ceil(total_students / N)
        if students_per_turn <= 0:
            students_per_turn = 1
            
        turn_index = min(idx // students_per_turn, N - 1)
        policy = turn_policies[turn_index]
        return policy["numero_turno"], policy["fecha_hora_inicio"]

    async def actualizar_turnos_matriculas_periodo(self, conn: asyncpg.Connection, tenant_id: UUID, periodo_id: UUID) -> None:
        turn_policies = await conn.fetch(
            """
            SELECT numero_turno, fecha_hora_inicio
            FROM politica_turno_matricula
            WHERE id_periodo = $1
            ORDER BY numero_turno ASC
            """,
            periodo_id,
        )
        if not turn_policies:
            return
            
        # Regular students (excluding risk)
        students_regular = await conn.fetch(
            """
            SELECT pa.id_usuario, 
                   COALESCE((SELECT ppa FROM snapshot_promedio WHERE id_perfil_alumno = pa.id_perfil_alumno ORDER BY created_at DESC LIMIT 1), 14.00) as ppa
            FROM perfil_alumno pa
            JOIN usuarios u ON u.id = pa.id_usuario
            WHERE u.id_tenant = $1 AND u.activo = TRUE
              AND NOT EXISTS (
                  SELECT 1
                  FROM condicion_academica_alumno caa
                  JOIN tipo_condicion_academica tca ON caa.id_tipo_condicion = tca.id_tipo_condicion
                  WHERE caa.id_perfil_alumno = pa.id_perfil_alumno
                    AND caa.estado = 'ACTIVA'
                    AND tca.codigo = 'RIESGO_ACADEMICO'
              )
            ORDER BY ppa DESC, pa.codigo_alumno ASC
            """,
            tenant_id,
        )

        # Risk students (assigned to Turn 1)
        students_risk = await conn.fetch(
            """
            SELECT pa.id_usuario
            FROM perfil_alumno pa
            JOIN usuarios u ON u.id = pa.id_usuario
            WHERE u.id_tenant = $1 AND u.activo = TRUE
              AND EXISTS (
                  SELECT 1
                  FROM condicion_academica_alumno caa
                  JOIN tipo_condicion_academica tca ON caa.id_tipo_condicion = tca.id_tipo_condicion
                  WHERE caa.id_perfil_alumno = pa.id_perfil_alumno
                    AND caa.estado = 'ACTIVA'
                    AND tca.codigo = 'RIESGO_ACADEMICO'
              )
            """,
            tenant_id,
        )
        
        import math
        N = len(turn_policies)
        total_regular = len(students_regular)
        
        # 1. Update regular students using regular division
        if total_regular > 0 and N > 0:
            students_per_turn = math.ceil(total_regular / N)
            if students_per_turn <= 0:
                students_per_turn = 1
                
            for idx, s in enumerate(students_regular):
                turn_index = min(idx // students_per_turn, N - 1)
                policy = turn_policies[turn_index]
                await conn.execute(
                    """
                    UPDATE matricula
                    SET numero_turno = $1, fecha_hora_turno = $2
                    WHERE id_alumno = $3 AND id_periodo = $4 AND id_tenant = $5
                    """,
                    policy["numero_turno"],
                    policy["fecha_hora_inicio"],
                    s["id_usuario"],
                    periodo_id,
                    tenant_id,
                )

        # 2. Update risk students directly to Turn 1
        if len(students_risk) > 0 and N > 0:
            policy_t1 = turn_policies[0]
            for s in students_risk:
                await conn.execute(
                    """
                    UPDATE matricula
                    SET numero_turno = $1, fecha_hora_turno = $2
                    WHERE id_alumno = $3 AND id_periodo = $4 AND id_tenant = $5
                    """,
                    policy_t1["numero_turno"],
                    policy_t1["fecha_hora_inicio"],
                    s["id_usuario"],
                    periodo_id,
                    tenant_id,
                )

    async def create_matricula(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: UUID,
        alumno_id: UUID,
        periodo_id: UUID,
        numero_turno: int = 1,
        fecha_hora_turno: datetime | None = None,
    ) -> asyncpg.Record:
        """Crea la cabecera de la matrícula en la BD dentro de la transacción actual."""
        return await conn.fetchrow(
            """
            INSERT INTO matricula (id_tenant, id_alumno, id_periodo, numero_turno, fecha_hora_turno)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            tenant_id,
            alumno_id,
            periodo_id,
            numero_turno,
            fecha_hora_turno,
        )

    async def update_creditos_matricula(
        self,
        conn: asyncpg.Connection,
        matricula_id: UUID,
        tenant_id: UUID,
        creditos: int,
    ) -> asyncpg.Record | None:
        return await conn.fetchrow(
            """
            UPDATE matricula
            SET creditos_matriculados = $3, updated_at = NOW()
            WHERE id = $1 AND id_tenant = $2
            RETURNING *
            """,
            matricula_id,
            tenant_id,
            creditos,
        )

    async def get_seccion_for_update(
        self, conn: asyncpg.Connection, seccion_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        return await conn.fetchrow(
            """
            SELECT s.*, c.creditos AS curso_creditos
            FROM seccion s
            JOIN curso c ON c.id = s.id_curso
            WHERE s.id = $1 AND s.id_tenant = $2
            FOR UPDATE OF s
            """,
            seccion_id,
            tenant_id,
        )

    async def reservar_vacante(
        self, conn: asyncpg.Connection, seccion_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        """
        Disminuye en 1 las vacantes disponibles de una sección.
        Ejecutado con bloqueos (FOR UPDATE) dentro de una transacción para evitar sobrecupo.
        """
        return await conn.fetchrow(
            """
            UPDATE seccion
            SET vacantes_disponibles = vacantes_disponibles - 1, updated_at = NOW()
            WHERE id = $1 AND id_tenant = $2 AND vacantes_disponibles > 0 AND estado = 'ABIERTA'
            RETURNING *
            """,
            seccion_id,
            tenant_id,
        )

    async def liberar_vacante(
        self, conn: asyncpg.Connection, seccion_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        return await conn.fetchrow(
            """
            UPDATE seccion
            SET vacantes_disponibles = LEAST(vacantes_disponibles + 1, vacantes_maximas),
                updated_at = NOW()
            WHERE id = $1 AND id_tenant = $2
            RETURNING *
            """,
            seccion_id,
            tenant_id,
        )

    async def get_inscripcion_activa_curso(
        self, matricula_id: UUID, curso_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        return await self.pool.fetchrow(
            """
            SELECT * FROM inscripcion
            WHERE id_matricula = $1 AND id_curso = $2 AND id_tenant = $3 AND estado = 'ACTIVA'
            """,
            matricula_id,
            curso_id,
            tenant_id,
        )

    async def get_inscripcion_by_id(
        self, inscripcion_id: UUID, tenant_id: UUID
    ) -> asyncpg.Record | None:
        return await self.pool.fetchrow(
            """
            SELECT i.*, c.nombre_curso, s.codigo_seccion
            FROM inscripcion i
            JOIN seccion s ON i.id_seccion = s.id
            JOIN curso c ON i.id_curso = c.id
            WHERE i.id = $1 AND i.id_tenant = $2
            """,
            inscripcion_id,
            tenant_id,
        )

    async def list_inscripciones_by_matricula(
        self, matricula_id: UUID, tenant_id: UUID
    ) -> list[asyncpg.Record]:
        rows = await self.pool.fetch(
            """
            SELECT i.*, c.nombre_curso, s.codigo_seccion
            FROM inscripcion i
            JOIN seccion s ON i.id_seccion = s.id
            JOIN curso c ON i.id_curso = c.id
            WHERE i.id_matricula = $1 AND i.id_tenant = $2
            ORDER BY i.fecha_inscripcion DESC
            """,
            matricula_id,
            tenant_id,
        )
        return list(rows)

    async def list_inscripciones_by_seccion(
        self, seccion_id: UUID, tenant_id: UUID
    ) -> list[asyncpg.Record]:
        """Lista las inscripciones activas de una sección con datos del alumno."""
        rows = await self.pool.fetch(
            """
            SELECT i.id, i.id_matricula, i.id_curso, i.id_seccion, i.estado,
                   i.creditos, i.fecha_inscripcion,
                   u.id   AS id_alumno,
                   u.nombre, u.apellido, u.email,
                   c.nombre_curso, c.codigo_curso
            FROM inscripcion i
            JOIN matricula m ON i.id_matricula = m.id
            JOIN usuarios u  ON m.id_alumno = u.id
            JOIN curso c     ON i.id_curso = c.id
            WHERE i.id_seccion = $1
              AND i.id_tenant = $2
              AND i.estado = 'ACTIVA'
            ORDER BY u.apellido, u.nombre
            """,
            seccion_id,
            tenant_id,
        )
        return list(rows)

    async def create_inscripcion(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: UUID,
        matricula_id: UUID,
        seccion_id: UUID,
        curso_id: UUID,
        creditos: int,
    ) -> asyncpg.Record:
        return await conn.fetchrow(
            """
            INSERT INTO inscripcion (
                id_tenant, id_matricula, id_seccion, id_curso, creditos
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            tenant_id,
            matricula_id,
            seccion_id,
            curso_id,
            creditos,
        )

    async def retirar_inscripcion(
        self,
        conn: asyncpg.Connection,
        inscripcion_id: UUID,
        tenant_id: UUID,
    ) -> asyncpg.Record | None:
        return await conn.fetchrow(
            """
            UPDATE inscripcion
            SET estado = 'RETIRADA', fecha_retiro = NOW(), updated_at = NOW()
            WHERE id = $1 AND id_tenant = $2 AND estado = 'ACTIVA'
            RETURNING *
            """,
            inscripcion_id,
            tenant_id,
        )

    async def list_prerrequisitos_curso(self, curso_id: UUID) -> list[asyncpg.Record]:
        rows = await self.pool.fetch(
            """
            SELECT id, id_curso, id_curso_requerido, tipo_prereq, valor_min_creditos
            FROM prerrequisito
            WHERE id_curso = $1 AND tipo_prereq = 'APROBACION_CURSO'
            """,
            curso_id,
        )
        return list(rows)

    async def list_cursos_aprobados_alumno(
        self, alumno_id: UUID, tenant_id: UUID, curso_ids: list[UUID]
    ) -> set[UUID]:
        """Obtiene el conjunto de IDs de asignaturas aprobadas por el alumno de la lista especificada."""
        if not curso_ids:
            return set()
        rows = await self.pool.fetch(
            """
            SELECT DISTINCT i.id_curso
            FROM inscripcion i
            JOIN matricula m ON m.id = i.id_matricula
            WHERE m.id_alumno = $1
              AND m.id_tenant = $2
              AND i.id_curso = ANY($3::uuid[])
              AND i.estado = 'APROBADA'
            """,
            alumno_id,
            tenant_id,
            curso_ids,
        )
        return {row["id_curso"] for row in rows}

    async def get_max_creditos_periodo(self, periodo_id: UUID) -> int | None:
        return await self.pool.fetchval(
            """
            SELECT MAX(creditos_maximos) FROM politica_credito WHERE id_periodo = $1
            """,
            periodo_id,
        )

    async def upsert_cuenta_seguimiento_creditos(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: UUID,
        alumno_id: UUID,
        delta_creditos: int,
    ) -> None:
        """
        Actualiza (incrementa o decrementa) el total de créditos inscritos del período
        en la cuenta de seguimiento del estudiante. Si no existe la cuenta, la crea.
        """
        await conn.execute(
            """
            INSERT INTO cuenta_seguimiento_alumno (id_tenant, id_alumno, creditos_inscritos_periodo)
            VALUES ($1, $2, GREATEST($3, 0))
            ON CONFLICT (id_tenant, id_alumno)
            DO UPDATE SET
                creditos_inscritos_periodo = GREATEST(
                    cuenta_seguimiento_alumno.creditos_inscritos_periodo + $3,
                    0
                ),
                updated_at = NOW()
            """,
            tenant_id,
            alumno_id,
            delta_creditos,
        )
