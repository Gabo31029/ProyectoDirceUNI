from decimal import Decimal
from uuid import UUID
import asyncpg

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.periodo import validar_fechas_periodo, validar_transicion_estado_periodo
from app.models.schemas import PeriodoAcademicoCreate, PeriodoAcademicoResponse, PeriodoEstado
from app.repositories.audit_repository import AuditRepository
from app.repositories.periodo_repository import PeriodoRepository


def _map_periodo(row: asyncpg.Record) -> PeriodoAcademicoResponse:
    return PeriodoAcademicoResponse(
        id=row["id"],
        id_tenant=row["id_tenant"],
        nombre_periodo=row["nombre_periodo"],
        fecha_inicio=row["fecha_inicio"],
        fecha_fin=row["fecha_fin"],
        estado=row["estado"],
        fecha_estado_actual=row["fecha_estado_actual"],
        id_usuario_transicion=row["id_usuario_transicion"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PeriodoService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.repo = PeriodoRepository(pool)
        self.audit_repo = AuditRepository()

    async def crear_periodo(
        self, tenant_id: UUID, payload: PeriodoAcademicoCreate, *, actor_id: UUID
    ) -> PeriodoAcademicoResponse:
        try:
            validar_fechas_periodo(payload.fecha_inicio, payload.fecha_fin)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        # Verificar unicidad de nombre_periodo por tenant
        existing = await self.repo.list_by_tenant(tenant_id)
        for p in existing:
            if p["nombre_periodo"].lower() == payload.nombre_periodo.lower():
                raise ConflictError("Ya existe un periodo con este nombre para el tenant.")

        try:
            row = await self.repo.create(
                id_tenant=tenant_id,
                nombre_periodo=payload.nombre_periodo,
                fecha_inicio=payload.fecha_inicio,
                fecha_fin=payload.fecha_fin,
            )
        except asyncpg.UniqueViolationError as exc:
            raise ConflictError("Ya existe un periodo con ese nombre.") from exc

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="PERIODO_ACADEMICO_CREADO",
                entidad_afectada="periodo_academico",
                id_entidad=row["id"],
                valor_nuevo={
                    "nombre_periodo": payload.nombre_periodo,
                    "fecha_inicio": str(payload.fecha_inicio),
                    "fecha_fin": str(payload.fecha_fin),
                },
            )

        return _map_periodo(row)

    async def list_periodos(self, tenant_id: UUID) -> list[PeriodoAcademicoResponse]:
        rows = await self.repo.list_by_tenant(tenant_id)
        return [_map_periodo(row) for row in rows]

    async def get_periodo(self, periodo_id: UUID, tenant_id: UUID) -> PeriodoAcademicoResponse:
        row = await self.repo.get_by_id(periodo_id, tenant_id)
        if row is None:
            raise NotFoundError("Periodo academico no encontrado.")
        return _map_periodo(row)

    async def get_periodo_activo(self, tenant_id: UUID) -> PeriodoAcademicoResponse:
        row = await self.repo.get_activo_by_tenant(tenant_id)
        if row is None:
            raise NotFoundError("No hay un periodo activo (en MATRICULA o REGISTRO_NOTAS).")
        return _map_periodo(row)

    async def transicionar_periodo(
        self,
        tenant_id: UUID,
        periodo_id: UUID,
        estado_nuevo: PeriodoEstado,
        *,
        actor_id: UUID,
    ) -> PeriodoAcademicoResponse:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")

        try:
            validar_transicion_estado_periodo(periodo["estado"], estado_nuevo.value)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        # Validar RF-PER-02: No pueden coexistir dos periodos en MATRICULA o REGISTRO_NOTAS
        if estado_nuevo in (PeriodoEstado.MATRICULA, PeriodoEstado.REGISTRO_NOTAS):
            activo = await self.repo.get_activo_by_tenant(tenant_id)
            if activo and activo["id"] != periodo_id:
                raise ConflictError(
                    f"Ya existe un periodo activo en estado {activo['estado']}. "
                    "Debe cerrarse antes de activar otro."
                )

        # Transición a CERRADO: Ejecutar cierre académico (RF-PER-04)
        if estado_nuevo == PeriodoEstado.CERRADO:
            await self._ejecutar_cierre_academico(tenant_id, periodo_id)

        # Transición a MATRICULA: Asignar/actualizar turnos de matrículas existentes
        if estado_nuevo == PeriodoEstado.MATRICULA:
            from app.repositories.matricula_repository import MatriculaRepository
            async with self.pool.acquire() as conn:
                await MatriculaRepository(self.pool).actualizar_turnos_matriculas_periodo(
                    conn, tenant_id, periodo_id
                )

        row = await self.repo.update_estado(
            periodo_id, tenant_id, estado_nuevo.value, actor_id
        )

        async with self.pool.acquire() as conn:
            await self.audit_repo.registrar(
                conn,
                id_tenant=tenant_id,
                id_usuario=actor_id,
                tipo_operacion="PERIODO_ACADEMICO_TRANSICION",
                entidad_afectada="periodo_academico",
                id_entidad=periodo_id,
                valor_anterior={"estado": periodo["estado"]},
                valor_nuevo={"estado": estado_nuevo.value},
            )

        return _map_periodo(row)

    async def _ejecutar_cierre_academico(self, tenant_id: UUID, periodo_id: UUID) -> None:
        """RF-PER-04: Cierre académico. Calcula PPS y PPA de los alumnos si las tablas existen."""
        async with self.pool.acquire() as conn:
            # Verificar si las tablas requeridas para el cálculo de notas existen
            # (ya que las implementan otros miembros del grupo en sus fases)
            tablas_requeridas = ["matricula", "inscripcion", "calificacion", "snapshot_promedio"]
            todas_existen = True
            for t in tablas_requeridas:
                existe = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    t,
                )
                if not existe:
                    todas_existen = False
                    break

            if not todas_existen:
                # Si no existen, simulamos el cierre (salto seguro sin fallar)
                return

            # Aquí iría el cálculo de promedios para cada alumno con matrícula ACTIVA en el periodo
            # Obtenemos los alumnos matriculados
            alumnos = await conn.fetch(
                "SELECT DISTINCT id_perfil_alumno FROM matricula WHERE id_periodo = $1 AND estado = 'ACTIVA'",
                periodo_id,
            )

            # Para cada alumno calcular su promedio semestral (PPS) y acumulado (PPA)
            for alumno in alumnos:
                alumno_id = alumno["id_perfil_alumno"]

                # Obtener la fórmula asociada al periodo (por defecto sum(nota * peso) / sum(peso))
                # En esta fase asumimos una fórmula ponderada simple
                # 1. Calcular promedio del periodo (PPS)
                pps = await conn.fetchval(
                    """
                    SELECT SUM(c.valor_nota * ce.peso_relativo / 100.00)
                    FROM inscripcion i
                    JOIN calificacion c ON c.id_inscripcion = i.id
                    JOIN componente_evaluacion ce ON c.id_componente = ce.id
                    WHERE i.id_matricula IN (
                        SELECT id FROM matricula WHERE id_perfil_alumno = $1 AND id_periodo = $2
                    ) AND i.estado = 'ACTIVA'
                    """,
                    alumno_id,
                    periodo_id,
                ) or Decimal("0.00")

                # 2. Calcular promedio acumulado (PPA) incluyendo periodos anteriores
                ppa = pps  # En esta fase simplificada

                # 3. Guardar el snapshot
                await conn.execute(
                    """
                    INSERT INTO snapshot_promedio (id_perfil_alumno, id_periodo, id_tenant, pps, ppa)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id_perfil_alumno, id_periodo) DO UPDATE
                    SET pps = EXCLUDED.pps, ppa = EXCLUDED.ppa
                    """,
                    alumno_id,
                    periodo_id,
                    tenant_id,
                    pps,
                    ppa,
                )

    # --- Métodos de CRUD para políticas ---
    async def add_politica_credito(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        row = await self.repo.create_politica_credito(
            id_periodo=periodo_id,
            ppa_minimo=Decimal(str(payload["ppa_minimo"])),
            ppa_maximo=Decimal(str(payload["ppa_maximo"])),
            creditos_maximos=int(payload["creditos_maximos"]),
        )
        return dict(row)

    async def list_politicas_credito(self, tenant_id: UUID, periodo_id: UUID) -> list[dict]:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        rows = await self.repo.get_politicas_credito_by_periodo(periodo_id)
        return [dict(r) for r in rows]

    # --- Politicas Turno Matricula ---
    async def add_politica_turno(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        from datetime import datetime
        dt_str = payload["fecha_hora_inicio"]
        if isinstance(dt_str, str):
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1] + "+00:00"
            fecha_hora_inicio = datetime.fromisoformat(dt_str)
        else:
            fecha_hora_inicio = dt_str

        row = await self.repo.create_politica_turno(
            id_periodo=periodo_id,
            numero_turno=int(payload["numero_turno"]),
            fecha_hora_inicio=fecha_hora_inicio,
            creditos_maximos=int(payload["creditos_maximos"]),
        )
        
        # Recalcular turnos si hubiera matrículas existentes
        from app.repositories.matricula_repository import MatriculaRepository
        async with self.pool.acquire() as conn:
            await MatriculaRepository(self.pool).actualizar_turnos_matriculas_periodo(
                conn, tenant_id, periodo_id
            )

        return dict(row)

    async def list_politicas_turno(self, tenant_id: UUID, periodo_id: UUID) -> list[dict]:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        rows = await self.repo.get_politicas_turno_by_periodo(periodo_id)
        return [dict(r) for r in rows]

    async def clear_politicas_turno(self, tenant_id: UUID, periodo_id: UUID) -> None:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden modificar políticas en estado CONFIGURACION.")
        await self.repo.delete_politicas_turno_by_periodo(periodo_id)

    async def add_politica_condicion(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        id_tipo_condicion = payload["id_tipo_condicion"]
        if not isinstance(id_tipo_condicion, UUID):
            id_tipo_condicion = UUID(str(id_tipo_condicion))

        row = await self.repo.create_politica_condicion(
            id_periodo=periodo_id,
            id_tipo_condicion=id_tipo_condicion,
            cuenta_evaluada=payload["cuenta_evaluada"],
            umbral=Decimal(str(payload["umbral"])),
            operador=payload["operador"],
            accion_resultante=payload["accion_resultante"],
        )
        return dict(row)

    async def list_politicas_condicion(self, tenant_id: UUID, periodo_id: UUID) -> list[dict]:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        rows = await self.repo.get_politicas_condicion_by_periodo(periodo_id)
        return [dict(r) for r in rows]

    async def add_politica_retiro(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        row = await self.repo.create_politica_retiro(
            id_periodo=periodo_id,
            tipo_retiro=payload["tipo_retiro"],
            semana_limite=int(payload["semana_limite"]),
            condiciones_bloqueantes=payload.get("condiciones_bloqueantes"),
        )
        return dict(row)

    async def list_politicas_retiro(self, tenant_id: UUID, periodo_id: UUID) -> list[dict]:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        rows = await self.repo.get_politicas_retiro_by_periodo(periodo_id)
        return [dict(r) for r in rows]

    async def add_politica_reserva(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        row = await self.repo.create_politica_reserva(
            id_periodo=periodo_id,
            max_periodos_consecutivos=int(payload["max_periodos_consecutivos"]),
            max_periodos_alternos=int(payload["max_periodos_alternos"]),
        )
        return dict(row)

    async def get_politica_reserva(self, tenant_id: UUID, periodo_id: UUID) -> dict | None:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        row = await self.repo.get_politica_reserva_by_periodo(periodo_id)
        return dict(row) if row else None

    async def add_formula_promedio(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        row = await self.repo.create_formula_promedio(
            id_periodo=periodo_id,
            tipo_promedio=payload["tipo_promedio"],
            expresion_calculo=payload["expresion_calculo"],
            regla_inclusion=payload["regla_inclusion"],
            version_formula=payload["version_formula"],
        )
        return dict(row)

    async def list_formulas_promedio(self, tenant_id: UUID, periodo_id: UUID) -> list[dict]:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        rows = await self.repo.get_formulas_promedio_by_periodo(periodo_id)
        return [dict(r) for r in rows]

    async def add_politica_dispersion(
        self, tenant_id: UUID, periodo_id: UUID, payload: dict, *, actor_id: UUID
    ) -> dict:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        if periodo["estado"] != PeriodoEstado.CONFIGURACION.value:
            raise ValidationError("Solo se pueden agregar políticas en estado CONFIGURACION.")

        row = await self.repo.create_politica_dispersion(
            id_periodo=periodo_id,
            ciclos_max_dispersion=int(payload["ciclos_max_dispersion"]),
            prioridad_ciclo_atrasado=bool(payload["prioridad_ciclo_atrasado"]),
        )
        return dict(row)

    async def get_politica_dispersion(self, tenant_id: UUID, periodo_id: UUID) -> dict | None:
        periodo = await self.repo.get_by_id(periodo_id, tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")
        row = await self.repo.get_politica_dispersion_by_periodo(periodo_id)
        return dict(row) if row else None
