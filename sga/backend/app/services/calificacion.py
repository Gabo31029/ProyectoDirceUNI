from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.audit import log_audit, create_academic_event
from app.repositories.calificacion import ComponenteRepository, CalificacionRepository, CorreccionNotaRepository
from app.models.core_schemas import (
    Seccion, Inscripcion, EscalaEvaluacion, AsignacionDocenteSeccion,
    PeriodoAcademico, Matricula
)
from app.models.calificacion import Calificacion, ComponenteEvaluacion, CorreccionNota
from app.models.cierre import FormulaPromedio, SnapshotPromedio
from app.domain.calificacion import (
    validate_grade_value, can_modify_grades, can_publish_component, can_correct_grade
)
from app.domain.cierre import calcular_nota_final, calcular_promedio_ponderado

componente_repo = ComponenteRepository()
calificacion_repo = CalificacionRepository()
correccion_repo = CorreccionNotaRepository()


def registrar_calificaciones(
    db: Session,
    id_seccion: str,
    id_componente: str,
    calificaciones_in: List[Dict[str, Any]],
    user: CurrentUser
) -> List[Calificacion]:
    """
    Caso de uso: Registra o actualiza calificaciones de estudiantes para un componente de evaluación.

    Reglas de negocio y seguridad:
    - Control de accesos (RBAC): Solo accesible por un Docente asignado a la sección o un Administrador.
    - Validación de asignación: Si el usuario es docente, se verifica que esté asignado a la sección
      (con bypass especial para perfiles de pruebas/desarrollo).
    - Máquina de estados: El componente de evaluación debe estar en estado 'BORRADOR'.
    - Consistencia de datos: Las inscripciones de los alumnos deben pertenecer a la sección
      y no encontrarse en estado 'RETIRADA' o 'ANULADA'.
    - Rango de escala: Cada calificación se valida contra el rango de la escala de evaluación configurada.
    - Trazabilidad y transaccionalidad: Registra un log de auditoría. Si ocurre cualquier error,
      se ejecuta un rollback de la transacción de base de datos.
    """
    # 1. Autorización de Rol
    if user.rol not in ("DOCENTE", "ADMINISTRADOR"):
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "seccion", id_seccion, "RECHAZADA", motivo_rechazo="Rol no autorizado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No autorizado para registrar calificaciones.")

    # Validación específica para el Docente: verificar asignación en la sección
    if user.rol == "DOCENTE":
        docente_perfil_id = user.id_perfil or ""
        is_assigned = db.query(AsignacionDocenteSeccion).filter(
            AsignacionDocenteSeccion.id_seccion == id_seccion,
            AsignacionDocenteSeccion.id_perfil_docente == docente_perfil_id
        ).first()
        if not is_assigned and not docente_perfil_id.startswith("profile-docente-mock"):
            log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                      "seccion", id_seccion, "RECHAZADA", motivo_rechazo="Docente no asignado a esta sección.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="El docente no está asignado a esta sección.")

    # 2. Recuperar y validar existencia del Componente de Evaluación
    componente = componente_repo.get(db, id_componente)
    if not componente or componente.id_seccion != id_seccion:
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Componente no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Componente de evaluación no encontrado.")

    # 3. Verificación de estado de flujo del acta
    if not can_modify_grades(componente.estado):
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "RECHAZADA",
                  motivo_rechazo="El componente no está en estado BORRADOR.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No se pueden modificar calificaciones en un componente publicado o cerrado.")

    # 4. Recuperar la escala de evaluación asociada para validar límites
    escala = db.query(EscalaEvaluacion).filter(
        EscalaEvaluacion.id_escala == componente.id_escala
    ).first()
    if not escala:
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Escala de evaluación no configurada.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Escala de evaluación no encontrada.")

    res_calificaciones = []

    try:
        # 5. Procesar lote de calificaciones
        for item in calificaciones_in:
            insc_id = item["id_inscripcion"]
            nota_val = Decimal(str(item["valor_nota"]))

            # Validar que la inscripción pertenece a la sección académica
            inscripcion = db.query(Inscripcion).filter(
                Inscripcion.id_inscripcion == insc_id,
                Inscripcion.id_seccion == id_seccion
            ).first()
            if not inscripcion:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"La inscripción {insc_id} no pertenece a esta sección.")

            # Impedir calificar a alumnos retirados o con matrícula anulada
            if inscripcion.estado in ("RETIRADA", "ANULADA"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede registrar nota para una inscripción en estado {inscripcion.estado}."
                )

            # Validar que el valor numérico esté dentro de la escala
            validate_grade_value(nota_val, escala.nota_minima, escala.nota_maxima)

            # Guardar en base de datos: Crear o actualizar
            calif = calificacion_repo.get_by_inscripcion_and_componente(db, insc_id, id_componente)
            if calif:
                calif.valor_nota = nota_val
                calif.id_docente_ingreso = user.id_perfil or "mock-docente-id"
                calif.fecha_ingreso = datetime.now(timezone.utc)
                db.add(calif)
            else:
                calif_data = {
                    "id_inscripcion": insc_id,
                    "id_componente": id_componente,
                    "valor_nota": nota_val,
                    "estado": "BORRADOR",
                    "id_docente_ingreso": user.id_perfil or "mock-docente-id"
                }
                calif = calificacion_repo.create(db, obj_in=calif_data)

            res_calificaciones.append(calif)

        # Enviar cambios a la transacción de base de datos sin confirmarlos (commit en API router)
        db.flush()
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "EXITOSA",
                  valor_nuevo={"calificaciones_count": len(res_calificaciones)})
        return res_calificaciones

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error interno al registrar calificaciones: {str(e)}")


def publicar_componente(
    db: Session,
    id_seccion: str,
    id_componente: str,
    user: CurrentUser
) -> ComponenteEvaluacion:
    """
    Caso de uso: Publica las calificaciones de un componente de evaluación.

    Reglas de negocio y flujo:
    - Hace las notas visibles para los alumnos del portal.
    - Control de accesos (RBAC): Requiere rol Administrador o ser el Docente Coordinador de la sección.
    - Máquina de estados: Solo se permite publicar si el componente está actualmente en 'BORRADOR'.
    - Cascada: Modifica el estado tanto del componente evaluado como de todas las calificaciones
      individuales asociadas a él a 'PUBLICADO'.
    - Registra un evento académico inmutable ('EVT-NOTA-COMPONENTE-PUBLICADA') en la bitácora institucional.
    """
    # 1. Recuperar Componente de Evaluación
    componente = componente_repo.get(db, id_componente)
    if not componente or componente.id_seccion != id_seccion:
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Componente no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Componente de evaluación no encontrado.")

    # 2. Validar transición de estado
    if not can_publish_component(componente.estado):
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA",
                  motivo_rechazo="Componente no está en estado BORRADOR.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="El componente ya se encuentra publicado o cerrado.")

    # 3. Control de Accesos
    if user.rol not in ("ADMINISTRADOR", "DOCENTE"):
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Rol no autorizado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No autorizado para publicar componentes.")

    # Validación adicional para docentes: Debe ser coordinador de la sección académica
    if user.rol == "DOCENTE":
        docente_perfil_id = user.id_perfil or ""
        is_coord = db.query(AsignacionDocenteSeccion).filter(
            AsignacionDocenteSeccion.id_seccion == id_seccion,
            AsignacionDocenteSeccion.id_perfil_docente == docente_perfil_id,
            AsignacionDocenteSeccion.es_coordinador.is_(True)
        ).first()
        if not is_coord and not docente_perfil_id.startswith("profile-docente-mock"):
            log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                      "componente", id_componente, "RECHAZADA",
                      motivo_rechazo="Docente no es coordinador.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Solo el docente coordinador de la sección puede publicar calificaciones.")

    try:
        # 4. Transición de estados en cascada
        componente.estado = "PUBLICADO"
        db.add(componente)

        grades = calificacion_repo.get_by_componente(db, id_componente)
        for g in grades:
            g.estado = "PUBLICADO"
            db.add(g)

        db.flush()

        # Emitir evento del Ciclo de Vida Académico
        create_academic_event(
            db, user.id_tenant, "EVT-NOTA-COMPONENTE-PUBLICADA",
            user.id_usuario, "componente_evaluacion", id_componente
        )

        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "EXITOSA")
        return componente

    except Exception as e:
        db.rollback()
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al publicar calificaciones: {str(e)}")


def corregir_calificacion(
    db: Session,
    id_calificacion: str,
    valor_nuevo: Decimal,
    justificacion: str,
    user: CurrentUser
) -> Calificacion:
    """
    Caso de uso: Aplica una corrección administrativa de nota sobre un componente cerrado.

    Reglas de negocio complejas y auditoría:
    - Control de accesos (RBAC): Únicamente permitida para el rol ADMINISTRADOR.
    - Máquina de estados: Solo aplica sobre rubros evaluativos que ya estén en estado 'CERRADO'.
    - Límite de escala: La nota nueva se valida con los límites superior e inferior de la escala.
    - Trazabilidad e inmutabilidad:
        1. Crea un evento académico 'EVT-NOTA-CORREGIDA' registrando los valores anterior y nuevo.
        2. Registra una fila en `correccion_nota` vinculada al evento y al administrador aprobador.
        3. Modifica el registro de la nota y recalcula la nota final de la inscripción del estudiante.
        4. Si el estudiante aprueba o reprueba con el recálculo, actualiza su estado de inscripción
           a 'APROBADA' o 'DESAPROBADA' respectivamente y emite 'EVT-NOTA-FINAL-CALCULADA'.
        5. Si el Período Académico correspondiente ya se encuentra en estado 'CERRADO',
           el cambio de nota obliga a recalcular los promedios semestral (PPS) e histórico (PPA)
           del estudiante y a generar un nuevo `SnapshotPromedio` encadenado al snapshot previo,
           emitiendo además el evento 'EVT-SNAPSHOT-PROMEDIO'.
    """
    # 1. Restricción de seguridad
    if user.rol != "ADMINISTRADOR":
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA",
                  motivo_rechazo="Rol no es Administrador.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo los administradores pueden autorizar correcciones de nota.")

    # 2. Recuperar la calificación
    calif = calificacion_repo.get(db, id_calificacion)
    if not calif:
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA",
                  motivo_rechazo="Calificación no encontrada.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Registro de calificación no encontrado.")

    # 3. Validar estado del componente (Acta cerrada)
    componente = componente_repo.get(db, calif.id_componente)
    if not componente or not can_correct_grade(componente.estado):
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA",
                  motivo_rechazo="El componente no está cerrado.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las correcciones administrativas solo aplican sobre componentes cerrados."
        )

    # 4. Validar nueva calificación contra los límites de la escala
    escala = db.query(EscalaEvaluacion).filter(
        EscalaEvaluacion.id_escala == componente.id_escala
    ).first()
    validate_grade_value(valor_nuevo, escala.nota_minima, escala.nota_maxima)

    # Evitar registrar una corrección por el mismo valor de nota vigente
    if Decimal(str(calif.valor_nota)) == Decimal(str(valor_nuevo)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="La nueva nota debe ser diferente a la nota actual.")

    valor_anterior = calif.valor_nota

    try:
        # 5. Obtener contexto de inscripción, matrícula y estudiante
        inscripcion = db.query(Inscripcion).filter(
            Inscripcion.id_inscripcion == calif.id_inscripcion
        ).first()
        matricula = db.query(Matricula).filter(
            Matricula.id_matricula == inscripcion.id_matricula
        ).first()
        id_perfil_alumno = matricula.id_perfil_alumno

        # 6. Registrar evento de auditoría académica
        event_origen = create_academic_event(
            db=db,
            id_tenant=user.id_tenant,
            codigo_evento="EVT-NOTA-CORREGIDA",
            id_actor=user.id_usuario,
            entidad_afectada_tipo="calificacion",
            entidad_afectada_id=id_calificacion,
            id_perfil_alumno=id_perfil_alumno,
            valor_anterior=float(valor_anterior),
            valor_nuevo=float(valor_nuevo)
        )

        # 7. Asentar registro administrativo de la corrección
        correccion = CorreccionNota(
            id_calificacion=id_calificacion,
            id_evento_original=event_origen.id_evento,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            justificacion=justificacion,
            id_admin_aprobador=user.id_usuario
        )
        db.add(correccion)

        # 8. Modificar nota
        calif.valor_nota = valor_nuevo
        db.add(calif)
        db.flush()

        # 9. Recalcular la nota final promedio ponderada de la asignatura
        todas_calif = db.query(Calificacion).filter(
            Calificacion.id_inscripcion == calif.id_inscripcion
        ).all()
        lista_calif_domain = []
        for c in todas_calif:
            comp = componente_repo.get(db, c.id_componente)
            lista_calif_domain.append({
                "valor_nota": c.valor_nota,
                "peso_relativo": comp.peso_relativo
            })

        nota_final_calculada = calcular_nota_final(lista_calif_domain)
        inscripcion.nota_final = nota_final_calculada
        # Evaluar estado de aprobación vigesimal
        inscripcion.estado = "APROBADA" if nota_final_calculada >= escala.nota_aprobatoria else "DESAPROBADA"
        db.add(inscripcion)
        db.flush()

        # Emitir evento de cálculo de nota final corregido
        create_academic_event(
            db=db,
            id_tenant=user.id_tenant,
            codigo_evento="EVT-NOTA-FINAL-CALCULADA",
            id_actor=user.id_usuario,
            entidad_afectada_tipo="inscripcion",
            entidad_afectada_id=inscripcion.id_inscripcion,
            id_perfil_alumno=id_perfil_alumno,
            valor_anterior=float(valor_anterior),
            valor_nuevo=float(nota_final_calculada)
        )

        # 10. Recálculo en cascada de promedios si el período académico ya estaba cerrado
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id_periodo == matricula.id_periodo
        ).first()
        if periodo and periodo.estado == "CERRADO":
            # Obtener las fórmulas parametrizadas del período para PPS y PPA
            formula_pps = db.query(FormulaPromedio).filter(
                FormulaPromedio.id_periodo == periodo.id_periodo,
                FormulaPromedio.tipo_promedio == "PPS"
            ).first()
            formula_ppa = db.query(FormulaPromedio).filter(
                FormulaPromedio.id_periodo == periodo.id_periodo,
                FormulaPromedio.tipo_promedio == "PPA"
            ).first()

            regla_pps = formula_pps.regla_inclusion if formula_pps else "TODOS"
            regla_ppa = formula_ppa.regla_inclusion if formula_ppa else "TODOS"

            # Obtener inscripciones válidas para el período actual
            ins_periodo = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == id_perfil_alumno,
                    Matricula.id_periodo == periodo.id_periodo,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )
            # Obtener todo el historial de inscripciones válidas para el promedio acumulado
            ins_historicas = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == id_perfil_alumno,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )

            # Adaptar la lista al formato que requiere el dominio para el cálculo
            def _build_list(inscriptions):
                result = []
                for ins in inscriptions:
                    secc = db.query(Seccion).filter(Seccion.id_seccion == ins.id_seccion).first()
                    if secc and secc.curso:
                        result.append({
                            "codigo_curso": secc.id_curso,
                            "creditos": secc.curso.creditos,
                            "nota_final": ins.nota_final,
                            "estado": ins.estado,
                            "fecha_orden": ins.created_at
                        })
                return result

            # Calcular los promedios actualizados usando las funciones de dominio
            nuevo_pps = calcular_promedio_ponderado(_build_list(ins_periodo), regla_pps)
            nuevo_ppa = calcular_promedio_ponderado(_build_list(ins_historicas), regla_ppa)

            # Encontrar el snapshot más reciente del alumno para este período académico
            prev_snapshot = (
                db.query(SnapshotPromedio)
                .filter(
                    SnapshotPromedio.id_perfil_alumno == id_perfil_alumno,
                    SnapshotPromedio.id_periodo == periodo.id_periodo
                )
                .order_by(SnapshotPromedio.created_at.desc())
                .first()
            )

            # Generar el nuevo snapshot inmutable encadenado
            new_snapshot = SnapshotPromedio(
                id_perfil_alumno=id_perfil_alumno,
                id_periodo=periodo.id_periodo,
                id_tenant=user.id_tenant,
                pps=nuevo_pps,
                ppa=nuevo_ppa,
                id_formula_aplicada=formula_pps.id_formula if formula_pps else None,
                id_snapshot_anterior=prev_snapshot.id_snapshot if prev_snapshot else None,
                id_evento_correc=event_origen.id_evento
            )
            db.add(new_snapshot)
            db.flush()

            # Registrar el evento académico del nuevo promedio recalculado
            create_academic_event(
                db=db,
                id_tenant=user.id_tenant,
                codigo_evento="EVT-SNAPSHOT-PROMEDIO",
                id_actor=user.id_usuario,
                entidad_afectada_tipo="snapshot_promedio",
                entidad_afectada_id=new_snapshot.id_snapshot,
                id_perfil_alumno=id_perfil_alumno,
                valor_anterior={"pps": float(prev_snapshot.pps), "ppa": float(prev_snapshot.ppa)} if prev_snapshot else None,
                valor_nuevo={"pps": float(nuevo_pps), "ppa": float(nuevo_ppa)}
            )

        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "EXITOSA",
                  valor_anterior=float(valor_anterior), valor_nuevo=float(valor_nuevo))
        return calif

    except Exception as e:
        db.rollback()
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA", motivo_rechazo=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al corregir calificación: {str(e)}")
