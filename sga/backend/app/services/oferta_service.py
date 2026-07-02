from uuid import UUID
from decimal import Decimal
import asyncpg

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.oferta import validar_prerrequisitos, validar_suma_pesos_evaluaciones, validar_edicion_seccion
from app.models.schemas import (
    PlanEstudiosCreate, PlanEstudiosResponse, PlanEstado,
    CursoCreate, CursoResponse, CursoAsociarPlan,
    CursoEvaluacionConfigResponse,
    PrerrequisitoCreate, PrerrequisitoResponse,
    SeccionCreate, SeccionResponse, SeccionEstado,
    AsignacionDocenteCreate, AsignacionDocenteResponse,
    EvaluacionAcademicaCreate, EvaluacionAcademicaResponse, EvaluacionEstado
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.oferta_repository import OfertaRepository
from app.repositories.periodo_repository import PeriodoRepository
from app.repositories.matricula_repository import MatriculaRepository


def _map_plan(row: asyncpg.Record) -> PlanEstudiosResponse:
    return PlanEstudiosResponse(
        id=row["id"],
        id_tenant=row["id_tenant"],
        carrera=row["carrera"],
        version_plan=row["version_plan"],
        creditos_totales=row["creditos_totales"],
        estado=row["estado"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _map_curso(row: asyncpg.Record) -> CursoResponse:
    return CursoResponse(
        id=row["id"],
        id_tenant=row["id_tenant"],
        codigo_curso=row["codigo_curso"],
        nombre_curso=row["nombre_curso"],
        creditos=row["creditos"],
        tipo_curso=row["tipo_curso"],
        ciclo_sugerido=row["ciclo_sugerido"],
        activo=row["activo"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _map_seccion(row: asyncpg.Record) -> SeccionResponse:
    return SeccionResponse(
        id=row["id"],
        id_tenant=row["id_tenant"],
        id_periodo=row["id_periodo"],
        id_curso=row["id_curso"],
        codigo_seccion=row["codigo_seccion"],
        vacantes_maximas=row["vacantes_maximas"],
        vacantes_disponibles=row["vacantes_disponibles"],
        estado=row["estado"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _map_evaluacion(row: asyncpg.Record) -> EvaluacionAcademicaResponse:
    return EvaluacionAcademicaResponse(
        id=row["id"],
        id_seccion=row["id_seccion"],
        id_tipo_evaluacion=row["id_tipo_evaluacion"],
        id_escala=row["id_escala"],
        peso_relativo=row["peso_relativo"],
        orden_presentacion=row["orden_presentacion"],
        estado=row["estado"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class OfertaService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.repo = OfertaRepository(pool)
        self.periodo_repo = PeriodoRepository(pool)
        self.audit_repo = AuditRepository()
        self.matricula_repo = MatriculaRepository(pool)

    # --- Plan de Estudios ---
    async def crear_plan_estudios(
        self, tenant_id: UUID, payload: PlanEstudiosCreate, *, actor_id: UUID
    ) -> PlanEstudiosResponse:
        # Verificar unicidad por tenant, carrera, version_plan
        planes = await self.repo.list_planes_estudio(tenant_id)
        for p in planes:
            if p["carrera"].lower() == payload.carrera.lower() and p["version_plan"].lower() == payload.version_plan.lower():
                raise ConflictError("Ya existe una version de este plan para esta carrera.")

        row = await self.repo.create_plan_estudios(
            id_tenant=tenant_id,
            carrera=payload.carrera,
            version_plan=payload.version_plan,
            creditos_totales=payload.creditos_totales,
        )

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="PLAN_ESTUDIOS_CREADO",
                entidad_afectada="plan_estudios",
                id_entidad=row["id"],
                valor_nuevo=dict(row),
            )

        return _map_plan(row)

    async def activar_plan_estudios(
        self, tenant_id: UUID, plan_id: UUID, *, actor_id: UUID
    ) -> PlanEstudiosResponse:
        plan = await self.repo.get_plan_estudios_by_id(plan_id, tenant_id)
        if plan is None:
            raise NotFoundError("Plan de estudios no encontrado.")

        row = await self.repo.update_estado_plan_estudios(plan_id, tenant_id, PlanEstado.ACTIVO.value)

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="PLAN_ESTUDIOS_ACTIVADO",
                entidad_afectada="plan_estudios",
                id_entidad=plan_id,
                valor_anterior={"estado": plan["estado"]},
                valor_nuevo={"estado": PlanEstado.ACTIVO.value},
            )

        return _map_plan(row)

    async def list_planes(self, tenant_id: UUID) -> list[PlanEstudiosResponse]:
        rows = await self.repo.list_planes_estudio(tenant_id)
        return [_map_plan(row) for row in rows]

    # --- Cursos ---
    async def crear_curso(
        self, tenant_id: UUID, payload: CursoCreate, *, actor_id: UUID
    ) -> CursoResponse:
        if await self.repo.get_curso_by_codigo(payload.codigo_curso, tenant_id):
            raise ConflictError("Ya existe un curso con ese codigo en la institucion.")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO curso (id_tenant, codigo_curso, nombre_curso, creditos, tipo_curso, ciclo_sugerido)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                    """,
                    tenant_id,
                    payload.codigo_curso,
                    payload.nombre_curso,
                    payload.creditos,
                    payload.tipo_curso,
                    payload.ciclo_sugerido,
                )

                for prereq_id in payload.prerrequisitos:
                    if prereq_id == row["id"]:
                        raise ValidationError("Un curso no puede ser prerrequisito de si mismo.")
                    prereq_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM curso WHERE id = $1 AND id_tenant = $2)",
                        prereq_id,
                        tenant_id,
                    )
                    if not prereq_exists:
                        raise NotFoundError(f"Curso prerrequisito con ID {prereq_id} no encontrado.")
                    
                    await conn.execute(
                        """
                        INSERT INTO prerrequisito (id_curso, id_curso_requerido, tipo_prereq)
                        VALUES ($1, $2, 'APROBACION_CURSO')
                        """,
                        row["id"],
                        prereq_id,
                    )

                # Insertar configuración de evaluaciones si viene en el payload
                eval_config_rows = []
                for idx, item in enumerate(payload.evaluaciones_config):
                    tipo_exists = await conn.fetchval(
                        """
                        SELECT EXISTS(
                            SELECT 1 
                            FROM tipo_evaluacion te
                            JOIN tenants t ON te.id_tenant = t.id_tenant
                            WHERE te.id_tipo_evaluacion = $1 AND t.id = $2
                        )
                        """,
                        item.id_tipo_evaluacion,
                        tenant_id,
                    )

                    if not tipo_exists:
                        raise NotFoundError(
                            f"Tipo de evaluación con ID {item.id_tipo_evaluacion} no encontrado en este tenant."
                        )
                    orden = item.orden if item.orden else (idx + 1)
                    cfg_row = await self.repo.create_curso_evaluacion_config(
                        conn,
                        id_curso=row["id"],
                        id_tipo_evaluacion=item.id_tipo_evaluacion,
                        peso=item.peso,
                        orden=orden,
                    )
                    eval_config_rows.append(cfg_row)

                await self.audit_repo.registrar(
                    conn,
                    id_tenant=tenant_id,
                    id_usuario=actor_id,
                    tipo_operacion="CURSO_CREADO",
                    entidad_afectada="curso",
                    id_entidad=row["id"],
                    valor_nuevo=dict(row),
                )

        res = _map_curso(row)
        res.prerrequisitos = payload.prerrequisitos
        res.evaluaciones_config = [
            CursoEvaluacionConfigResponse(
                id=cfg["id"],
                id_curso=cfg["id_curso"],
                id_tipo_evaluacion=cfg["id_tipo_evaluacion"],
                peso=cfg["peso"],
                orden=cfg["orden"],
                nombre_tipo_evaluacion=None,
                created_at=cfg["created_at"],
            )
            for cfg in eval_config_rows
        ]
        return res

    async def asociar_curso_a_plan(
        self, tenant_id: UUID, plan_id: UUID, payload: CursoAsociarPlan, *, actor_id: UUID
    ) -> dict:
        plan = await self.repo.get_plan_estudios_by_id(plan_id, tenant_id)
        if plan is None:
            raise NotFoundError("Plan de estudios no encontrado.")
        if plan["estado"] == PlanEstado.ACTIVO.value:
            raise ValidationError("No se puede asociar cursos a un plan de estudios ACTIVO.")

        curso = await self.repo.get_curso_by_id(payload.id_curso, tenant_id)
        if curso is None:
            raise NotFoundError("Curso no encontrado.")

        # Verificar si ya está asociado
        asociados = await self.repo.get_cursos_por_plan(plan_id)
        for a in asociados:
            if a["id"] == payload.id_curso:
                raise ConflictError("El curso ya esta asociado a este plan de estudios.")

        row = await self.repo.asociar_curso_a_plan(
            id_plan_estudios=plan_id,
            id_curso=payload.id_curso,
            ciclo_en_plan=payload.ciclo_en_plan,
            es_obligatorio=payload.es_obligatorio,
        )
        return dict(row)

    async def desasociar_curso_de_plan(
        self, tenant_id: UUID, plan_id: UUID, curso_id: UUID, *, actor_id: UUID
    ) -> None:
        plan = await self.repo.get_plan_estudios_by_id(plan_id, tenant_id)
        if plan is None:
            raise NotFoundError("Plan de estudios no encontrado.")
        if plan["estado"] == PlanEstado.ACTIVO.value:
            raise ValidationError("No se puede desasociar cursos de un plan de estudios ACTIVO.")

        curso = await self.repo.get_curso_by_id(curso_id, tenant_id)
        if curso is None:
            raise NotFoundError("Curso no encontrado.")

        # Verificar si está asociado
        asociados = await self.repo.get_cursos_por_plan(plan_id)
        asociado = False
        for a in asociados:
            if a["id"] == curso_id:
                asociado = True
                break
        if not asociado:
            raise NotFoundError("El curso no esta asociado a este plan de estudios.")

        deleted = await self.repo.desasociar_curso_de_plan(
            id_plan_estudios=plan_id,
            id_curso=curso_id,
        )
        if not deleted:
            raise ConflictError("No se pudo desasociar el curso del plan.")

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="CURSO_DESASOCIADO_DE_PLAN",
                entidad_afectada="plan_estudios_curso",
                id_entidad=plan_id,
                valor_anterior={"id_plan_estudios": str(plan_id), "id_curso": str(curso_id)},
            )

    async def list_cursos(self, tenant_id: UUID) -> list[CursoResponse]:
        rows = await self.repo.list_cursos(tenant_id)
        
        # Consultar masivamente los prerrequisitos para el tenant
        async with self.pool.acquire() as conn:
            prereqs = await conn.fetch(
                """
                SELECT p.id_curso, p.id_curso_requerido
                FROM prerrequisito p
                JOIN curso c ON p.id_curso = c.id
                WHERE c.id_tenant = $1 AND c.activo = TRUE AND p.id_curso_requerido IS NOT NULL
                """,
                tenant_id,
            )
            # Consultar configuraciones de evaluaciones para todos los cursos del tenant
            eval_configs = await conn.fetch(
                """
                SELECT cec.*, te.nombre AS nombre_tipo_evaluacion
                FROM curso_evaluacion_config cec
                JOIN curso c ON cec.id_curso = c.id
                LEFT JOIN tipo_evaluacion te ON cec.id_tipo_evaluacion = te.id_tipo_evaluacion
                WHERE c.id_tenant = $1
                ORDER BY cec.id_curso, cec.orden, cec.created_at
                """,
                tenant_id,
            )
            
        prereq_map = {}
        for r in prereqs:
            c_id = r["id_curso"]
            req_id = r["id_curso_requerido"]
            if c_id not in prereq_map:
                prereq_map[c_id] = []
            prereq_map[c_id].append(req_id)

        eval_config_map = {}
        for r in eval_configs:
            c_id = r["id_curso"]
            if c_id not in eval_config_map:
                eval_config_map[c_id] = []
            eval_config_map[c_id].append(
                CursoEvaluacionConfigResponse(
                    id=r["id"],
                    id_curso=r["id_curso"],
                    id_tipo_evaluacion=r["id_tipo_evaluacion"],
                    peso=r["peso"],
                    orden=r["orden"],
                    nombre_tipo_evaluacion=r["nombre_tipo_evaluacion"],
                    created_at=r["created_at"],
                )
            )

        cursos_res = []
        for row in rows:
            curso_dto = _map_curso(row)
            curso_dto.prerrequisitos = prereq_map.get(curso_dto.id, [])
            curso_dto.evaluaciones_config = eval_config_map.get(curso_dto.id, [])
            cursos_res.append(curso_dto)
            
        return cursos_res

    async def list_cursos_plan(self, tenant_id: UUID, plan_id: UUID) -> list[dict]:
        plan = await self.repo.get_plan_estudios_by_id(plan_id, tenant_id)
        if plan is None:
            raise NotFoundError("Plan de estudios no encontrado.")
        rows = await self.repo.get_cursos_por_plan(plan_id)
        
        if not rows:
            return []
            
        curso_ids = [r["id"] for r in rows]
        
        async with self.pool.acquire() as conn:
            prereqs = await conn.fetch(
                """
                SELECT id_curso, id_curso_requerido
                FROM prerrequisito
                WHERE id_curso = ANY($1) AND id_curso_requerido IS NOT NULL
                """,
                curso_ids,
            )
            
        prereq_map = {}
        for r in prereqs:
            c_id = r["id_curso"]
            req_id = r["id_curso_requerido"]
            if c_id not in prereq_map:
                prereq_map[c_id] = []
            prereq_map[c_id].append(req_id)
            
        res = []
        for r in rows:
            d = dict(r)
            d["prerrequisitos"] = prereq_map.get(r["id"], [])
            res.append(d)
            
        return res

    async def configurar_prerrequisitos(
        self, tenant_id: UUID, curso_id: UUID, payload: PrerrequisitoCreate, *, actor_id: UUID
    ) -> PrerrequisitoResponse:
        curso = await self.repo.get_curso_by_id(curso_id, tenant_id)
        if curso is None:
            raise NotFoundError("Curso principal no encontrado.")

        if payload.id_curso_requerido:
            curso_req = await self.repo.get_curso_by_id(payload.id_curso_requerido, tenant_id)
            if curso_req is None:
                raise NotFoundError("Curso prerrequisito requerido no encontrado.")

        try:
            validar_prerrequisitos(payload.tipo_prereq, payload.id_curso_requerido, payload.valor_min_creditos)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        # Un curso no puede ser prerrequisito de si mismo
        if curso_id == payload.id_curso_requerido:
            raise ValidationError("Un curso no puede ser prerrequisito de si mismo.")

        # Verificar si ya existe esa regla
        existing = await self.repo.get_prerrequisitos_curso(curso_id)
        for req in existing:
            if req["id_curso_requerido"] == payload.id_curso_requerido and req["tipo_prereq"] == payload.tipo_prereq:
                raise ConflictError("Ya existe este prerrequisito para el curso.")

        row = await self.repo.add_prerrequisito(
            id_curso=curso_id,
            id_curso_requerido=payload.id_curso_requerido,
            tipo_prereq=payload.tipo_prereq,
            valor_min_creditos=payload.valor_min_creditos,
        )

        return PrerrequisitoResponse(
            id=row["id"],
            id_curso=row["id_curso"],
            id_curso_requerido=row["id_curso_requerido"],
            tipo_prereq=row["tipo_prereq"],
            valor_min_creditos=row["valor_min_creditos"],
            created_at=row["created_at"],
        )

    # --- Secciones ---
    async def crear_seccion(
        self, tenant_id: UUID, payload: SeccionCreate, *, actor_id: UUID
    ) -> SeccionResponse:
        # Verificar periodo
        periodo = await self.periodo_repo.get_by_id(payload.id_periodo, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")

        # Validar RF-OFR-03: Crear secciones sólo en CONFIGURACION
        try:
            validar_edicion_seccion(periodo["estado"])
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        # Verificar curso
        curso = await self.repo.get_curso_by_id(payload.id_curso, tenant_id)
        if curso is None:
            raise NotFoundError("Curso no encontrado.")

        # Verificar si la sección ya existe
        if await self.repo.get_seccion_by_codigo(
            id_periodo=payload.id_periodo,
            id_curso=payload.id_curso,
            codigo_seccion=payload.codigo_seccion,
        ):
            raise ConflictError("Ya existe una seccion con ese codigo para este curso en el periodo.")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO seccion (id_tenant, id_periodo, id_curso, codigo_seccion, vacantes_maximas, vacantes_disponibles)
                    VALUES ($1, $2, $3, $4, $5, $5)
                    RETURNING *
                    """,
                    tenant_id,
                    payload.id_periodo,
                    payload.id_curso,
                    payload.codigo_seccion,
                    payload.vacantes_maximas,
                )

                # Propagar evaluaciones del curso a la sección si hay configuración definida
                eval_configs = await conn.fetch(
                    "SELECT COUNT(*) AS cnt FROM curso_evaluacion_config WHERE id_curso = $1",
                    payload.id_curso,
                )
                config_count = eval_configs[0]["cnt"] if eval_configs else 0

                if config_count > 0:
                    # Obtener escala default del tenant
                    escala = await self.repo.get_escala_default_by_tenant(tenant_id)
                    if escala:
                        await self.repo.propagar_evaluaciones_config_a_seccion(
                            conn,
                            id_seccion=row["id"],
                            id_curso=payload.id_curso,
                            id_escala_default=escala["id"],
                        )

                # Asignar profesores si se especificaron
                for d in payload.docentes:
                    docente = await self.repo.get_docente_by_id_and_tenant(d.id_usuario_docente, tenant_id)
                    if docente is None:
                        raise NotFoundError(f"El docente con ID {d.id_usuario_docente} no existe o no pertenece a esta institución.")

                    await conn.execute(
                        """
                        INSERT INTO asignacion_docente_seccion (id_seccion, id_usuario_docente, id_tipo_evaluacion, es_coordinador)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT DO NOTHING
                        """,
                        row["id"],
                        d.id_usuario_docente,
                        d.id_tipo_evaluacion,
                        d.es_coordinador,
                    )

                await self.audit_repo.registrar(
                    conn,
                    id_tenant=tenant_id,
                    id_usuario=actor_id,
                    tipo_operacion="SECCION_CREADA",
                    entidad_afectada="seccion",
                    id_entidad=row["id"],
                    valor_nuevo=dict(row),
                )

        return _map_seccion(row)

    async def list_secciones(self, tenant_id: UUID, periodo_id: UUID) -> list[dict]:
        periodo = await self.periodo_repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        rows = await self.repo.list_secciones_by_periodo(periodo_id, tenant_id)
        return [dict(r) for r in rows]

    # --- Asignaciones Docente ---
    async def asignar_docente(
        self, tenant_id: UUID, seccion_id: UUID, payload: AsignacionDocenteCreate, *, actor_id: UUID
    ) -> AsignacionDocenteResponse:
        seccion = await self.repo.get_seccion_by_id(seccion_id, tenant_id)
        if seccion is None:
            raise NotFoundError("Seccion no encontrada.")

        docente = await self.repo.get_docente_by_id_and_tenant(payload.id_usuario_docente, tenant_id)
        if docente is None:
            raise NotFoundError("El usuario especificado no es un docente registrado en este tenant.")

        # Verificar si ya está asignado
        async with self.pool.acquire() as conn:
            existing = await conn.fetchrow(
                """
                SELECT 1 FROM asignacion_docente_seccion
                WHERE id_seccion = $1 AND id_usuario_docente = $2 AND id_tipo_evaluacion = $3
                """,
                seccion_id,
                payload.id_usuario_docente,
                payload.id_tipo_evaluacion,
            )
            if existing:
                raise ConflictError("El docente ya esta asignado a este componente de la seccion.")

        row = await self.repo.create_asignacion_docente(
            id_seccion=seccion_id,
            id_usuario_docente=payload.id_usuario_docente,
            id_tipo_evaluacion=payload.id_tipo_evaluacion,
            es_coordinador=payload.es_coordinador,
        )

        return AsignacionDocenteResponse(
            id=row["id"],
            id_seccion=row["id_seccion"],
            id_usuario_docente=row["id_usuario_docente"],
            id_tipo_evaluacion=row["id_tipo_evaluacion"],
            es_coordinador=row["es_coordinador"],
            created_at=row["created_at"],
        )

    # --- Evaluaciones Académicas ---
    async def crear_evaluacion_academica(
        self, tenant_id: UUID, seccion_id: UUID, payload: EvaluacionAcademicaCreate, *, actor_id: UUID
    ) -> EvaluacionAcademicaResponse:
        seccion = await self.repo.get_seccion_by_id(seccion_id, tenant_id)
        if seccion is None:
            raise NotFoundError("Seccion no encontrada.")

        escala = await self.repo.get_escala_by_id_and_tenant(payload.id_escala, tenant_id)
        if escala is None:
            raise NotFoundError("La escala de evaluacion no existe o no pertenece al tenant.")

        # Validar suma de pesos <= 100
        existentes = await self.repo.list_evaluaciones_by_seccion(seccion_id)
        pesos_list = [Decimal(str(c["peso_relativo"])) for c in existentes]
        try:
            validar_suma_pesos_evaluaciones(pesos_list, payload.peso_relativo)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        row = await self.repo.create_evaluacion_academica(
            id_seccion=seccion_id,
            id_tipo_evaluacion=payload.id_tipo_evaluacion,
            id_escala=payload.id_escala,
            peso_relative=payload.peso_relativo,
            orden_presentacion=payload.orden_presentacion,
        )

        return _map_evaluacion(row)

    async def list_evaluaciones(self, tenant_id: UUID, seccion_id: UUID) -> list[EvaluacionAcademicaResponse]:
        seccion = await self.repo.get_seccion_by_id(seccion_id, tenant_id)
        if seccion is None:
            raise NotFoundError("Seccion no encontrada.")
        rows = await self.repo.list_evaluaciones_by_seccion(seccion_id)
        return [_map_evaluacion(r) for r in rows]

    async def list_inscripciones_seccion(self, tenant_id: UUID, seccion_id: UUID) -> list[dict]:
        """Lista los alumnos inscritos activos en una sección con sus datos."""
        seccion = await self.repo.get_seccion_by_id(seccion_id, tenant_id)
        if seccion is None:
            raise NotFoundError("Seccion no encontrada.")
        rows = await self.matricula_repo.list_inscripciones_by_seccion(seccion_id, tenant_id)
        return [dict(r) for r in rows]
