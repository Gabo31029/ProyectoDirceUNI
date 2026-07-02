from uuid import UUID

import asyncpg

from app.core.dependencies import CurrentUser
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.domain.matricula import (
    validar_inscripcion_activa,
    validar_limite_creditos,
    validar_matricula_activa,
    validar_periodo_en_matricula,
    validar_prerrequisitos_cumplidos,
    validar_seccion_con_vacantes,
)
from app.models.schemas import (
    InscripcionCreate,
    InscripcionResponse,
    MatriculaCreate,
    MatriculaResponse,
    RetiroRequest,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.matricula_repository import MatriculaRepository


def _map_matricula(row: asyncpg.Record) -> MatriculaResponse:
    return MatriculaResponse(
        id=row["id"],
        id_tenant=row["id_tenant"],
        id_alumno=row["id_alumno"],
        id_periodo=row["id_periodo"],
        estado=row["estado"],
        creditos_matriculados=row["creditos_matriculados"],
        fecha_matricula=row["fecha_matricula"],
        numero_turno=row.get("numero_turno"),
        fecha_hora_turno=row.get("fecha_hora_turno"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _map_inscripcion(row: asyncpg.Record) -> InscripcionResponse:
    return InscripcionResponse(
        id=row["id"],
        id_tenant=row["id_tenant"],
        id_matricula=row["id_matricula"],
        id_seccion=row["id_seccion"],
        id_curso=row["id_curso"],
        estado=row["estado"],
        creditos=row["creditos"],
        fecha_inscripcion=row["fecha_inscripcion"],
        fecha_retiro=row["fecha_retiro"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        nombre_curso=row.get("nombre_curso"),
        codigo_seccion=row.get("codigo_seccion"),
    )


class MatriculaService:
    """
    Servicio encargado de coordinar la lógica de negocio y las transacciones del proceso de matrícula,
    incluyendo inscripciones de asignaturas, validación de prerrequisitos, límites de créditos y retiros.
    """
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self.repo = MatriculaRepository(pool)
        self.audit_repo = AuditRepository()

    def _resolve_alumno_id(self, current_user: CurrentUser, payload: MatriculaCreate) -> UUID:
        if current_user.rol == "ALUMNO":
            if payload.id_alumno and payload.id_alumno != current_user.id:
                raise ForbiddenError("Un alumno solo puede matricularse a si mismo.")
            return current_user.id
        if current_user.rol in ("ADMIN", "ADMIN_CENTRAL"):
            if payload.id_alumno is None:
                raise ValidationError("Debe indicar el id_alumno para crear la matricula.")
            return payload.id_alumno
        raise ForbiddenError("Rol no autorizado para matricula.")

    async def crear_matricula(
        self,
        tenant_id: UUID,
        payload: MatriculaCreate,
        *,
        current_user: CurrentUser,
    ) -> MatriculaResponse:
        """
        Crea una nueva matrícula (cabecera) y una cuenta de seguimiento de créditos inicial en cero.
        Valida que el período esté abierto para matrícula y que no exista una matrícula previa del alumno.
        Todo el proceso corre dentro de una transacción de base de datos.
        """
        alumno_id = self._resolve_alumno_id(current_user, payload)

        alumno = await self.repo.get_alumno(alumno_id, tenant_id)
        if alumno is None:
            raise NotFoundError("El alumno no existe o no pertenece al tenant.")
        if not alumno["activo"]:
            raise ValidationError("El alumno no esta activo.")

        periodo = await self.repo.get_periodo(payload.id_periodo, tenant_id)
        if periodo is None:
            raise NotFoundError("El periodo academico no existe o no pertenece al tenant.")

        try:
            validar_periodo_en_matricula(periodo["estado"])
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

        existente = await self.repo.get_matricula_alumno_periodo(
            alumno_id, payload.id_periodo, tenant_id
        )
        if existente and existente["estado"] == "ACTIVA":
            raise ConflictError("El alumno ya tiene una matricula activa para este periodo.")

        # Calcular el turno de matrícula para el estudiante
        numero_turno, fecha_hora_turno = await self.repo.calcular_turno_para_alumno(
            tenant_id, payload.id_periodo, alumno_id
        )

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await self.repo.create_matricula(
                    conn,
                    tenant_id=tenant_id,
                    alumno_id=alumno_id,
                    periodo_id=payload.id_periodo,
                    numero_turno=numero_turno,
                    fecha_hora_turno=fecha_hora_turno,
                )
                await self.repo.upsert_cuenta_seguimiento_creditos(
                    conn,
                    tenant_id=tenant_id,
                    alumno_id=alumno_id,
                    delta_creditos=0,
                )
                await self.audit_repo.registrar(
                    conn,
                    id_tenant=tenant_id,
                    id_usuario=current_user.id,
                    tipo_operacion="MATRICULA_CREADA",
                    entidad_afectada="matricula",
                    id_entidad=row["id"],
                    valor_nuevo={
                        "id_alumno": str(alumno_id),
                        "id_periodo": str(payload.id_periodo),
                        "numero_turno": numero_turno,
                    },
                )

        return _map_matricula(row)

    async def list_matriculas(
        self,
        tenant_id: UUID,
        *,
        alumno_id: UUID,
        current_user: CurrentUser,
    ) -> list[MatriculaResponse]:
        """
        Retorna la lista de matrículas realizadas por un alumno en una institución (tenant).
        """
        if current_user.rol == "ALUMNO" and alumno_id != current_user.id:
            raise ForbiddenError("No puede consultar matriculas de otro alumno.")
        rows = await self.repo.list_matriculas_by_alumno(alumno_id, tenant_id)
        return [_map_matricula(row) for row in rows]

    async def inscribir_curso(
        self,
        tenant_id: UUID,
        matricula_id: UUID,
        payload: InscripcionCreate,
        *,
        current_user: CurrentUser,
    ) -> InscripcionResponse:
        """
        Inscribe un curso en la matrícula activa del alumno.
        Lleva a cabo las siguientes validaciones críticas de negocio:
        1. Que la matrícula esté activa y en fase de matrícula.
        2. Que la sección destino esté abierta y cuente con vacantes.
        3. Que no haya duplicidad de curso.
        4. Que se cumplan los prerrequisitos académicos.
        5. Que la suma de créditos no exceda la política de créditos semestral.
        
        La reserva de vacantes, la inserción del registro de inscripción y la actualización
        de créditos se ejecutan en una transacción atómica para evitar concurrencias y sobrecupos.
        """
        matricula = await self.repo.get_matricula_by_id(matricula_id, tenant_id)
        if matricula is None:
            raise NotFoundError("La matricula no existe o no pertenece al tenant.")

        if current_user.rol == "ALUMNO" and matricula["id_alumno"] != current_user.id:
            raise ForbiddenError("No puede inscribir cursos en la matricula de otro alumno.")

        try:
            validar_matricula_activa(matricula["estado"])
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

        periodo = await self.repo.get_periodo(matricula["id_periodo"], tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")

        try:
            validar_periodo_en_matricula(periodo["estado"])
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

        # Validar si es el turno del alumno
        from datetime import datetime, timezone
        if matricula.get("fecha_hora_turno") and datetime.now(timezone.utc) < matricula["fecha_hora_turno"]:
            from_local = matricula["fecha_hora_turno"]
            raise ConflictError(f"Aún no es su turno de matrícula. Su turno inicia el {from_local.strftime('%d/%m/%Y %H:%M:%S')}")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                seccion = await self.repo.get_seccion_for_update(
                    conn, payload.id_seccion, tenant_id
                )
                if seccion is None:
                    raise NotFoundError("La seccion no existe o no pertenece al tenant.")

                if seccion["id_periodo"] != matricula["id_periodo"]:
                    raise ValidationError(
                        "La seccion no pertenece al periodo academico de la matricula."
                    )

                try:
                    validar_seccion_con_vacantes(
                        seccion["vacantes_disponibles"],
                        seccion["estado"],
                    )
                except ValueError as exc:
                    raise ConflictError(str(exc)) from exc

                curso_id = seccion["id_curso"]
                creditos_curso = int(seccion["curso_creditos"])

                duplicada = await self.repo.get_inscripcion_activa_curso(
                    matricula_id, curso_id, tenant_id
                )
                if duplicada:
                    raise ConflictError("El alumno ya esta inscrito en este curso.")

                prerrequisitos = await self.repo.list_prerrequisitos_curso(curso_id)
                requeridos = [
                    p["id_curso_requerido"]
                    for p in prerrequisitos
                    if p["id_curso_requerido"] is not None
                ]
                cumplidos = await self.repo.list_cursos_aprobados_alumno(
                    matricula["id_alumno"], tenant_id, requeridos
                )
                try:
                    validar_prerrequisitos_cumplidos(requeridos, cumplidos)
                except ValueError as exc:
                    raise ValidationError(str(exc)) from exc

                max_creditos = None
                if matricula.get("numero_turno"):
                    max_creditos = await self.repo.get_max_creditos_turno(
                        matricula["id_periodo"], matricula["numero_turno"]
                    )
                if max_creditos is None:
                    max_creditos = await self.repo.get_max_creditos_periodo(matricula["id_periodo"])

                if max_creditos is None:
                    raise ValidationError(
                        "No existe política de créditos o turnos configurada para el periodo."
                    )

                try:
                    validar_limite_creditos(
                        matricula["creditos_matriculados"],
                        creditos_curso,
                        int(max_creditos),
                    )
                except ValueError as exc:
                    raise ValidationError(str(exc)) from exc

                seccion_actualizada = await self.repo.reservar_vacante(
                    conn, payload.id_seccion, tenant_id
                )
                if seccion_actualizada is None:
                    raise ConflictError("No fue posible reservar vacante en la seccion.")

                inscripcion = await self.repo.create_inscripcion(
                    conn,
                    tenant_id=tenant_id,
                    matricula_id=matricula_id,
                    seccion_id=payload.id_seccion,
                    curso_id=curso_id,
                    creditos=creditos_curso,
                )

                nuevos_creditos = matricula["creditos_matriculados"] + creditos_curso
                matricula_actualizada = await self.repo.update_creditos_matricula(
                    conn, matricula_id, tenant_id, nuevos_creditos
                )
                if matricula_actualizada is None:
                    raise ConflictError("No fue posible actualizar creditos de la matricula.")

                await self.repo.upsert_cuenta_seguimiento_creditos(
                    conn,
                    tenant_id=tenant_id,
                    alumno_id=matricula["id_alumno"],
                    delta_creditos=creditos_curso,
                )

                await self.audit_repo.registrar(
                    conn,
                    id_tenant=tenant_id,
                    id_usuario=current_user.id,
                    tipo_operacion="INSCRIPCION_CREADA",
                    entidad_afectada="inscripcion",
                    id_entidad=inscripcion["id"],
                    valor_nuevo={
                        "id_matricula": str(matricula_id),
                        "id_seccion": str(payload.id_seccion),
                        "id_curso": str(curso_id),
                        "creditos": creditos_curso,
                    },
                )

        full_inscripcion = await self.repo.get_inscripcion_by_id(inscripcion["id"], tenant_id)
        return _map_inscripcion(full_inscripcion)

    async def retirar_curso(
        self,
        tenant_id: UUID,
        inscripcion_id: UUID,
        payload: RetiroRequest,
        *,
        current_user: CurrentUser,
    ) -> InscripcionResponse:
        """
        Procesa el retiro voluntario o administrativo de un curso inscrito.
        Transiciona la inscripción a estado 'RETIRADA', libera la vacante de la sección,
        descuenta los créditos de la matrícula y de la cuenta de seguimiento del estudiante,
        y registra el evento con su debida justificación en la auditoría general.
        """
        inscripcion = await self.repo.get_inscripcion_by_id(inscripcion_id, tenant_id)
        if inscripcion is None:
            raise NotFoundError("La inscripcion no existe o no pertenece al tenant.")

        if inscripcion["estado"] == "RETIRADA":
            raise ConflictError("La inscripcion ya fue retirada.")

        matricula = await self.repo.get_matricula_by_id(inscripcion["id_matricula"], tenant_id)
        if matricula is None:
            raise NotFoundError("Matricula asociada no encontrada.")

        if current_user.rol == "ALUMNO" and matricula["id_alumno"] != current_user.id:
            raise ForbiddenError("No puede retirar cursos de otro alumno.")

        try:
            validar_matricula_activa(matricula["estado"])
            validar_inscripcion_activa(inscripcion["estado"])
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

        periodo = await self.repo.get_periodo(matricula["id_periodo"], tenant_id)
        if periodo is None:
            raise NotFoundError("Periodo academico no encontrado.")

        try:
            validar_periodo_en_matricula(periodo["estado"])
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                retirada = await self.repo.retirar_inscripcion(
                    conn, inscripcion_id, tenant_id
                )
                if retirada is None:
                    raise ConflictError("No fue posible retirar la inscripcion.")

                liberada = await self.repo.liberar_vacante(
                    conn, retirada["id_seccion"], tenant_id
                )
                if liberada is None:
                    raise ConflictError("No fue posible liberar vacante en la seccion.")

                nuevos_creditos = matricula["creditos_matriculados"] - retirada["creditos"]
                await self.repo.update_creditos_matricula(
                    conn, matricula["id"], tenant_id, nuevos_creditos
                )

                await self.repo.upsert_cuenta_seguimiento_creditos(
                    conn,
                    tenant_id=tenant_id,
                    alumno_id=matricula["id_alumno"],
                    delta_creditos=-retirada["creditos"],
                )

                await self.audit_repo.registrar(
                    conn,
                    id_tenant=tenant_id,
                    id_usuario=current_user.id,
                    tipo_operacion="INSCRIPCION_RETIRADA",
                    entidad_afectada="inscripcion",
                    id_entidad=inscripcion_id,
                    valor_anterior={"estado": "ACTIVA"},
                    valor_nuevo={
                        "estado": "RETIRADA",
                        "motivo": payload.motivo,
                    },
                )

        full_retirada = await self.repo.get_inscripcion_by_id(inscripcion_id, tenant_id)
        return _map_inscripcion(full_retirada)

    async def list_inscripciones(
        self,
        tenant_id: UUID,
        matricula_id: UUID,
        *,
        current_user: CurrentUser,
    ) -> list[InscripcionResponse]:
        matricula = await self.repo.get_matricula_by_id(matricula_id, tenant_id)
        if matricula is None:
            raise NotFoundError("La matricula no existe o no pertenece al tenant.")

        if current_user.rol == "ALUMNO" and matricula["id_alumno"] != current_user.id:
            raise ForbiddenError("No puede consultar inscripciones de otro alumno.")

        rows = await self.repo.list_inscripciones_by_matricula(matricula_id, tenant_id)
        return [_map_inscripcion(row) for row in rows]
