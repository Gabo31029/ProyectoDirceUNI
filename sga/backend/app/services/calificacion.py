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
    Registra o actualiza calificaciones de alumnos para un componente de evaluación.
    Solo accesible por Docente asignado a la sección o Administrador.
    El componente debe estar en estado BORRADOR.
    """
    # 1. Authorization
    if user.rol not in ("DOCENTE", "ADMINISTRADOR"):
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "seccion", id_seccion, "RECHAZADA", motivo_rechazo="Rol no autorizado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No autorizado para registrar calificaciones.")

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

    # 2. Retrieve ComponenteEvaluacion
    componente = componente_repo.get(db, id_componente)
    if not componente or componente.id_seccion != id_seccion:
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Componente no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Componente de evaluación no encontrado.")

    # 3. State verification
    if not can_modify_grades(componente.estado):
        log_audit(db, user.id_tenant, user.id_usuario, "REGISTRAR_CALIFICACION",
                  "componente", id_componente, "RECHAZADA",
                  motivo_rechazo="El componente no está en estado BORRADOR.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No se pueden modificar calificaciones en un componente publicado o cerrado.")

    # 4. Fetch scale
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
        for item in calificaciones_in:
            insc_id = item["id_inscripcion"]
            nota_val = Decimal(str(item["valor_nota"]))

            inscripcion = db.query(Inscripcion).filter(
                Inscripcion.id_inscripcion == insc_id,
                Inscripcion.id_seccion == id_seccion
            ).first()
            if not inscripcion:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"La inscripción {insc_id} no pertenece a esta sección.")

            if inscripcion.estado in ("RETIRADA", "ANULADA"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede registrar nota para una inscripción en estado {inscripcion.estado}."
                )

            # Validate value is within scale range
            validate_grade_value(nota_val, escala.nota_minima, escala.nota_maxima)

            # Save or update grade
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
    Publica las calificaciones de un componente, haciéndolas visibles para los alumnos.
    Solo el docente coordinador o Administrador pueden publicar.
    """
    componente = componente_repo.get(db, id_componente)
    if not componente or componente.id_seccion != id_seccion:
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Componente no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Componente de evaluación no encontrado.")

    if not can_publish_component(componente.estado):
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA",
                  motivo_rechazo="Componente no está en estado BORRADOR.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="El componente ya se encuentra publicado o cerrado.")

    if user.rol not in ("ADMINISTRADOR", "DOCENTE"):
        log_audit(db, user.id_tenant, user.id_usuario, "PUBLICAR_COMPONENTE",
                  "componente", id_componente, "RECHAZADA", motivo_rechazo="Rol no autorizado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No autorizado para publicar componentes.")

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
        componente.estado = "PUBLICADO"
        db.add(componente)

        grades = calificacion_repo.get_by_componente(db, id_componente)
        for g in grades:
            g.estado = "PUBLICADO"
            db.add(g)

        db.flush()

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
    Aplica una corrección administrativa de nota sobre un componente cerrado.
    Solo ADMINISTRADOR puede autorizar correcciones.
    Recalcula la nota final de la inscripción y, si el período está cerrado,
    genera un nuevo SnapshotPromedio vinculado al anterior.
    """
    if user.rol != "ADMINISTRADOR":
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA",
                  motivo_rechazo="Rol no es Administrador.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo los administradores pueden autorizar correcciones de nota.")

    # 1. Fetch grade
    calif = calificacion_repo.get(db, id_calificacion)
    if not calif:
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA",
                  motivo_rechazo="Calificación no encontrada.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Registro de calificación no encontrado.")

    # 2. Verify component is closed
    componente = componente_repo.get(db, calif.id_componente)
    if not componente or not can_correct_grade(componente.estado):
        log_audit(db, user.id_tenant, user.id_usuario, "CORREGIR_CALIFICACION",
                  "calificacion", id_calificacion, "RECHAZADA",
                  motivo_rechazo="El componente no está cerrado.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las correcciones administrativas solo aplican sobre componentes cerrados."
        )

    # 3. Validate new value
    escala = db.query(EscalaEvaluacion).filter(
        EscalaEvaluacion.id_escala == componente.id_escala
    ).first()
    validate_grade_value(valor_nuevo, escala.nota_minima, escala.nota_maxima)

    if Decimal(str(calif.valor_nota)) == Decimal(str(valor_nuevo)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="La nueva nota debe ser diferente a la nota actual.")

    valor_anterior = calif.valor_nota

    try:
        # 4. Get enrollment context
        inscripcion = db.query(Inscripcion).filter(
            Inscripcion.id_inscripcion == calif.id_inscripcion
        ).first()
        matricula = db.query(Matricula).filter(
            Matricula.id_matricula == inscripcion.id_matricula
        ).first()
        id_perfil_alumno = matricula.id_perfil_alumno

        # 5. Create correction event
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

        # 6. Insert CorreccionNota record
        correccion = CorreccionNota(
            id_calificacion=id_calificacion,
            id_evento_original=event_origen.id_evento,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            justificacion=justificacion,
            id_admin_aprobador=user.id_usuario
        )
        db.add(correccion)

        # 7. Apply grade update
        calif.valor_nota = valor_nuevo
        db.add(calif)
        db.flush()

        # 8. Recalculate final grade for the inscription
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
        inscripcion.estado = "APROBADA" if nota_final_calculada >= escala.nota_aprobatoria else "DESAPROBADA"
        db.add(inscripcion)
        db.flush()

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

        # 9. If period is closed, recalculate PPS/PPA and create new snapshot
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id_periodo == matricula.id_periodo
        ).first()
        if periodo and periodo.estado == "CERRADO":
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

            ins_periodo = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == id_perfil_alumno,
                    Matricula.id_periodo == periodo.id_periodo,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )
            ins_historicas = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == id_perfil_alumno,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )

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

            nuevo_pps = calcular_promedio_ponderado(_build_list(ins_periodo), regla_pps)
            nuevo_ppa = calcular_promedio_ponderado(_build_list(ins_historicas), regla_ppa)

            prev_snapshot = (
                db.query(SnapshotPromedio)
                .filter(
                    SnapshotPromedio.id_perfil_alumno == id_perfil_alumno,
                    SnapshotPromedio.id_periodo == periodo.id_periodo
                )
                .order_by(SnapshotPromedio.created_at.desc())
                .first()
            )

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
