from uuid import UUID
from decimal import Decimal
import asyncpg

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.oferta import validar_prerrequisitos, validar_suma_pesos_componentes, validar_edicion_seccion
from app.models.schemas import (
    PlanEstudiosCreate, PlanEstudiosResponse, PlanEstado,
    CursoCreate, CursoResponse, CursoAsociarPlan,
    PrerrequisitoCreate, PrerrequisitoResponse,
    SeccionCreate, SeccionResponse, SeccionEstado,
    AsignacionDocenteCreate, AsignacionDocenteResponse,
    ComponenteEvaluacionCreate, ComponenteEvaluacionResponse, ComponenteEstado
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.oferta_repository import OfertaRepository
from app.repositories.periodo_repository import PeriodoRepository


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


def _map_componente(row: asyncpg.Record) -> ComponenteEvaluacionResponse:
    return ComponenteEvaluacionResponse(
        id=row["id"],
        id_seccion=row["id_seccion"],
        id_tipo_componente=row["id_tipo_componente"],
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

        row = await self.repo.create_curso(
            id_tenant=tenant_id,
            codigo_curso=payload.codigo_curso,
            nombre_curso=payload.nombre_curso,
            creditos=payload.creditos,
            tipo_curso=payload.tipo_curso,
            ciclo_sugerido=payload.ciclo_sugerido,
        )

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="CURSO_CREADO",
                entidad_afectada="curso",
                id_entidad=row["id"],
                valor_nuevo=dict(row),
            )

        return _map_curso(row)

    async def asociar_curso_a_plan(
        self, tenant_id: UUID, plan_id: UUID, payload: CursoAsociarPlan, *, actor_id: UUID
    ) -> dict:
        plan = await self.repo.get_plan_estudios_by_id(plan_id, tenant_id)
        if plan is None:
            raise NotFoundError("Plan de estudios no encontrado.")
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

    async def list_cursos(self, tenant_id: UUID) -> list[CursoResponse]:
        rows = await self.repo.list_cursos(tenant_id)
        return [_map_curso(row) for row in rows]

    async def list_cursos_plan(self, tenant_id: UUID, plan_id: UUID) -> list[dict]:
        plan = await self.repo.get_plan_estudios_by_id(plan_id, tenant_id)
        if plan is None:
            raise NotFoundError("Plan de estudios no encontrado.")
        rows = await self.repo.get_cursos_por_plan(plan_id)
        return [dict(r) for r in rows]

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

        row = await self.repo.create_seccion(
            id_tenant=tenant_id,
            id_periodo=payload.id_periodo,
            id_curso=payload.id_curso,
            codigo_seccion=payload.codigo_seccion,
            vacantes_maximas=payload.vacantes_maximas,
        )

        async with self.pool.acquire() as conn:
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
        seccion = await self.repo.get_by_id(seccion_id, tenant_id)
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
                WHERE id_seccion = $1 AND id_usuario_docente = $2 AND id_tipo_componente = $3
                """,
                seccion_id,
                payload.id_usuario_docente,
                payload.id_tipo_componente,
            )
            if existing:
                raise ConflictError("El docente ya esta asignado a este componente de la seccion.")

        row = await self.repo.create_asignacion_docente(
            id_seccion=seccion_id,
            id_usuario_docente=payload.id_usuario_docente,
            id_tipo_componente=payload.id_tipo_componente,
            es_coordinador=payload.es_coordinador,
        )

        return AsignacionDocenteResponse(
            id=row["id"],
            id_seccion=row["id_seccion"],
            id_usuario_docente=row["id_usuario_docente"],
            id_tipo_componente=row["id_tipo_componente"],
            es_coordinador=row["es_coordinador"],
            created_at=row["created_at"],
        )

    # --- Componentes de Evaluacion ---
    async def crear_componente_evaluacion(
        self, tenant_id: UUID, seccion_id: UUID, payload: ComponenteEvaluacionCreate, *, actor_id: UUID
    ) -> ComponenteEvaluacionResponse:
        seccion = await self.repo.get_by_id(seccion_id, tenant_id)
        if seccion is None:
            raise NotFoundError("Seccion no encontrada.")

        escala = await self.repo.get_escala_by_id_and_tenant(payload.id_escala, tenant_id)
        if escala is None:
            raise NotFoundError("La escala de evaluacion no existe o no pertenece al tenant.")

        # Validar suma de pesos <= 100
        existentes = await self.repo.list_componentes_by_seccion(seccion_id)
        pesos_list = [Decimal(str(c["peso_relativo"])) for c in existentes]
        try:
            validar_suma_pesos_componentes(pesos_list, payload.peso_relativo)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        row = await self.repo.create_componente_evaluacion(
            id_seccion=seccion_id,
            id_tipo_componente=payload.id_tipo_componente,
            id_escala=payload.id_escala,
            peso_relative=payload.peso_relativo,
            orden_presentacion=payload.orden_presentacion,
        )

        return _map_componente(row)

    async def list_componentes(self, tenant_id: UUID, seccion_id: UUID) -> list[ComponenteEvaluacionResponse]:
        seccion = await self.repo.get_by_id(seccion_id, tenant_id)
        if seccion is None:
            raise NotFoundError("Seccion no encontrada.")
        rows = await self.repo.list_componentes_by_seccion(seccion_id)
        return [_map_componente(r) for r in rows]
