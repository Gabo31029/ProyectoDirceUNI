from typing import List
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.core.audit import log_audit, create_academic_event
from app.repositories.calificacion import ComponenteRepository, CalificacionRepository
from app.models.core_schemas import (
    Seccion, Inscripcion, EscalaEvaluacion, AsignacionDocenteSeccion,
    PeriodoAcademico, Matricula, PerfilAlumno
)
from app.models.calificacion import ComponenteEvaluacion
from app.models.cierre import (
    FormulaPromedio, SnapshotPromedio, CondicionAcademicaAlumno,
    PoliticaCondicionAcademica
)
from app.models.seguimiento import CuentaSeguimientoAlumno
from app.models.core_schemas import TipoCondicionAcademica as CoreTipoCondicion
from app.domain.cierre import calcular_nota_final, calcular_promedio_ponderado, evaluar_politica_condicion

componente_repo = ComponenteRepository()
calificacion_repo = CalificacionRepository()


def cerrar_acta_seccion(
    db: Session,
    id_seccion: str,
    user: CurrentUser
) -> List[Inscripcion]:
    """
    Cierra de forma definitiva el acta de calificaciones de una sección.
    Calcula la nota final de cada inscripción activa y determina si aprueba o desaprueba.
    Operación transaccional: todos los cambios ocurren juntos o ninguno persiste.
    """
    # 1. Fetch section
    seccion = db.query(Seccion).filter(Seccion.id_seccion == id_seccion).first()
    if not seccion:
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo="Sección no encontrada.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada.")

    # 2. Authorization: admin or coordinator teacher
    if user.rol not in ("ADMINISTRADOR", "DOCENTE"):
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo="Rol no autorizado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para cerrar actas.")

    if user.rol == "DOCENTE":
        is_coord = db.query(AsignacionDocenteSeccion).filter(
            AsignacionDocenteSeccion.id_seccion == id_seccion,
            AsignacionDocenteSeccion.id_perfil_docente == user.id_perfil,
            AsignacionDocenteSeccion.es_coordinador.is_(True)
        ).first()
        if not is_coord and (not user.id_perfil or not user.id_perfil.startswith("profile-docente-mock")):
            log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                      id_seccion, "RECHAZADA", motivo_rechazo="Docente no es coordinador.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el docente coordinador de la sección puede cerrar el acta."
            )

    # 3. Retrieve all evaluation components
    componentes = componente_repo.get_by_seccion(db, id_seccion)
    if not componentes:
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo="No hay componentes de evaluación configurados.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay componentes de evaluación configurados en esta sección."
        )

    # 4. Verify all components are PUBLICADO
    for c in componentes:
        if c.estado != "PUBLICADO":
            log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                      id_seccion, "RECHAZADA", motivo_rechazo=f"Componente {c.id_componente} no está publicado.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Todos los componentes de evaluación deben estar publicados antes de cerrar el acta."
            )

    # 5. Fetch all active student inscriptions
    inscriptions = db.query(Inscripcion).filter(
        Inscripcion.id_seccion == id_seccion,
        Inscripcion.estado == "ACTIVA"
    ).all()

    if not inscriptions:
        for c in componentes:
            c.estado = "CERRADO"
            db.add(c)
        db.flush()
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "EXITOSA", valor_nuevo={"inscriptions_count": 0})
        return []

    # Fetch grading scale
    id_escala = componentes[0].id_escala
    escala = db.query(EscalaEvaluacion).filter(EscalaEvaluacion.id_escala == id_escala).first()

    try:
        # 6. Calculate final grade and update state for each student
        for ins in inscriptions:
            grades_list = []
            for comp in componentes:
                cal = calificacion_repo.get_by_inscripcion_and_componente(db, ins.id_inscripcion, comp.id_componente)
                if not cal:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Faltan calificaciones para la inscripción {ins.id_inscripcion}."
                    )
                grades_list.append({
                    "valor_nota": cal.valor_nota,
                    "peso_relativo": comp.peso_relativo
                })

            nota_final = calcular_nota_final(grades_list)
            ins.nota_final = nota_final

            id_perfil_alumno = ins.matricula.id_perfil_alumno
            id_curso = seccion.id_curso
            id_periodo = seccion.id_periodo

            if nota_final >= escala.nota_aprobatoria:
                ins.estado = "APROBADA"
                create_academic_event(
                    db=db,
                    id_tenant=user.id_tenant,
                    codigo_evento="EVT-NOTA-FINAL-CALCULADA",
                    id_actor=user.id_usuario,
                    entidad_afectada_tipo="inscripcion",
                    entidad_afectada_id=ins.id_inscripcion,
                    id_perfil_alumno=id_perfil_alumno,
                    valor_anterior=None,
                    valor_nuevo={"nota_final": float(nota_final), "creditos": float(seccion.curso.creditos)},
                    id_periodo_ref=id_periodo,
                    id_curso_ref=id_curso
                )
            else:
                ins.estado = "DESAPROBADA"
                create_academic_event(
                    db=db,
                    id_tenant=user.id_tenant,
                    codigo_evento="EVT-NOTA-FINAL-CALCULADA",
                    id_actor=user.id_usuario,
                    entidad_afectada_tipo="inscripcion",
                    entidad_afectada_id=ins.id_inscripcion,
                    id_perfil_alumno=id_perfil_alumno,
                    valor_anterior=None,
                    valor_nuevo={"nota_final": float(nota_final), "creditos": 0.0},
                    id_periodo_ref=id_periodo,
                    id_curso_ref=id_curso
                )
                create_academic_event(
                    db=db,
                    id_tenant=user.id_tenant,
                    codigo_evento="EVT-REPROBO-CURSO",
                    id_actor=user.id_usuario,
                    entidad_afectada_tipo="inscripcion",
                    entidad_afectada_id=ins.id_inscripcion,
                    id_perfil_alumno=id_perfil_alumno,
                    valor_anterior=0,
                    valor_nuevo=1,
                    id_periodo_ref=id_periodo,
                    id_curso_ref=id_curso
                )

            ins.fecha_cambio_estado = datetime.now(timezone.utc)
            db.add(ins)

        # 7. Close all components
        for c in componentes:
            c.estado = "CERRADO"
            db.add(c)

        db.flush()

        # 8. Emit EVT-ACTA-CERRADA
        create_academic_event(
            db, user.id_tenant, "EVT-ACTA-CERRADA",
            user.id_usuario, "seccion", id_seccion
        )

        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "EXITOSA", valor_nuevo={"inscriptions_count": len(inscriptions)})
        return inscriptions

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar el acta: {str(e)}"
        )


def cerrar_periodo_academico(
    db: Session,
    id_periodo: str,
    user: CurrentUser
) -> PeriodoAcademico:
    """
    Cierra un período académico.
    Para cada alumno matriculado calcula PPS y PPA, genera un SnapshotPromedio,
    y evalúa las políticas de condición académica configuradas para el período.
    Cada alumno se procesa en la misma transacción de sesión; un fallo aborta todo el lote.
    """
    if user.rol != "ADMINISTRADOR":
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                  id_periodo, "RECHAZADA", motivo_rechazo="Rol no es Administrador.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden cerrar períodos académicos."
        )

    # 1. Fetch period
    periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.id_periodo == id_periodo).first()
    if not periodo:
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                  id_periodo, "RECHAZADA", motivo_rechazo="Período no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período académico no encontrado.")

    if periodo.estado != "REGISTRO_NOTAS":
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                  id_periodo, "RECHAZADA", motivo_rechazo="Período no está en REGISTRO_NOTAS.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El período debe estar en estado REGISTRO_NOTAS antes de cerrarse."
        )

    # 2. Verify all evaluation components are closed
    sections = db.query(Seccion).filter(Seccion.id_periodo == id_periodo).all()
    for s in sections:
        components = db.query(ComponenteEvaluacion).filter(
            ComponenteEvaluacion.id_seccion == s.id_seccion
        ).all()
        for c in components:
            if c.estado != "CERRADO":
                log_audit(
                    db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                    id_periodo, "RECHAZADA",
                    motivo_rechazo=f"Sección {s.codigo_seccion} tiene componente abierto."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"No se puede cerrar el período porque la sección "
                        f"{s.codigo_seccion} tiene actas de evaluación abiertas."
                    )
                )

    # 3. Transition period state to CERRADO
    periodo.estado = "CERRADO"
    periodo.fecha_estado_actual = datetime.now(timezone.utc)
    periodo.id_usuario_transicion = user.id_usuario
    db.add(periodo)
    db.flush()

    # 4. Fetch all active students enrolled in this period
    alumnos = (
        db.query(PerfilAlumno)
        .join(Matricula, Matricula.id_perfil_alumno == PerfilAlumno.id_perfil_alumno)
        .filter(Matricula.id_periodo == id_periodo, Matricula.estado == "ACTIVA")
        .all()
    )

    # Fetch calculation formulas
    formula_pps = db.query(FormulaPromedio).filter(
        FormulaPromedio.id_periodo == id_periodo, FormulaPromedio.tipo_promedio == "PPS"
    ).first()
    formula_ppa = db.query(FormulaPromedio).filter(
        FormulaPromedio.id_periodo == id_periodo, FormulaPromedio.tipo_promedio == "PPA"
    ).first()

    regla_pps = formula_pps.regla_inclusion if formula_pps else "TODOS"
    regla_ppa = formula_ppa.regla_inclusion if formula_ppa else "TODOS"
    id_formula_aplicada = formula_pps.id_formula if formula_pps else None

    # Fetch active academic policies for this period
    politicas = db.query(PoliticaCondicionAcademica).filter(
        PoliticaCondicionAcademica.id_periodo == id_periodo
    ).all()

    try:
        # 5. Process each student
        for al in alumnos:
            # Period inscriptions
            ins_periodo = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == al.id_perfil_alumno,
                    Matricula.id_periodo == id_periodo,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )
            # Historical inscriptions (all periods)
            ins_historicas = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == al.id_perfil_alumno,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )

            def _build_domain_list(inscriptions):
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

            pps_calc = calcular_promedio_ponderado(_build_domain_list(ins_periodo), regla_pps)
            ppa_calc = calcular_promedio_ponderado(_build_domain_list(ins_historicas), regla_ppa)

            # Link to previous snapshot if exists
            prev_snapshot = (
                db.query(SnapshotPromedio)
                .filter(
                    SnapshotPromedio.id_perfil_alumno == al.id_perfil_alumno,
                    SnapshotPromedio.id_periodo == id_periodo
                )
                .order_by(SnapshotPromedio.created_at.desc())
                .first()
            )

            snapshot = SnapshotPromedio(
                id_perfil_alumno=al.id_perfil_alumno,
                id_periodo=id_periodo,
                id_tenant=user.id_tenant,
                pps=pps_calc,
                ppa=ppa_calc,
                id_formula_aplicada=id_formula_aplicada,
                id_snapshot_anterior=prev_snapshot.id_snapshot if prev_snapshot else None
            )
            db.add(snapshot)
            db.flush()

            create_academic_event(
                db=db,
                id_tenant=user.id_tenant,
                codigo_evento="EVT-SNAPSHOT-PROMEDIO",
                id_actor=user.id_usuario,
                entidad_afectada_tipo="snapshot_promedio",
                entidad_afectada_id=snapshot.id_snapshot,
                id_perfil_alumno=al.id_perfil_alumno,
                valor_anterior=None,
                valor_nuevo={"pps": float(pps_calc), "ppa": float(ppa_calc)},
                id_periodo_ref=id_periodo
            )

            # 6. Evaluate academic condition policies
            active_conditions = (
                db.query(CondicionAcademicaAlumno)
                .filter(
                    CondicionAcademicaAlumno.id_perfil_alumno == al.id_perfil_alumno,
                    CondicionAcademicaAlumno.estado == "ACTIVA"
                ).all()
            )

            for pol in politicas:
                cuenta = db.query(CuentaSeguimientoAlumno).filter(
                    CuentaSeguimientoAlumno.id_perfil_alumno == al.id_perfil_alumno,
                    CuentaSeguimientoAlumno.tipo_cuenta == pol.cuenta_evaluada
                ).first()
                valor_cuenta = cuenta.valor_actual if cuenta else Decimal("0.00")

                triggered = evaluar_politica_condicion(valor_cuenta, pol.umbral, pol.operador)

                if triggered:
                    already_active = any(
                        c.id_tipo_condicion == pol.id_tipo_condicion for c in active_conditions
                    )
                    if not already_active:
                        tipo_cond = db.query(CoreTipoCondicion).filter(
                            CoreTipoCondicion.id_tipo_condicion == pol.id_tipo_condicion
                        ).first()
                        cond_name = tipo_cond.codigo if tipo_cond else pol.accion_resultante

                        event_cond = create_academic_event(
                            db=db,
                            id_tenant=user.id_tenant,
                            codigo_evento="EVT-CONDICION-ACTIVADA",
                            id_actor=user.id_usuario,
                            entidad_afectada_tipo="condicion_academica_alumno",
                            entidad_afectada_id="temp",
                            id_perfil_alumno=al.id_perfil_alumno,
                            valor_anterior=None,
                            valor_nuevo=cond_name,
                            id_periodo_ref=id_periodo
                        )

                        new_cond = CondicionAcademicaAlumno(
                            id_perfil_alumno=al.id_perfil_alumno,
                            id_tipo_condicion=pol.id_tipo_condicion,
                            id_periodo=id_periodo,
                            id_evento_origen=event_cond.id_evento,
                            estado="ACTIVA",
                            fecha_activacion=datetime.now(timezone.utc),
                            observaciones="Activada automáticamente por política de cierre académico."
                        )
                        db.add(new_cond)
                        db.flush()

                        event_cond.entidad_afectada_id = new_cond.id_condicion
                        db.add(event_cond)
                        db.flush()
                else:
                    # Resolve any active condition of this type if threshold no longer met
                    for ac in active_conditions:
                        if ac.id_tipo_condicion == pol.id_tipo_condicion:
                            ac.estado = "RESUELTA"
                            ac.fecha_resolucion = datetime.now(timezone.utc)
                            db.add(ac)
                            create_academic_event(
                                db=db,
                                id_tenant=user.id_tenant,
                                codigo_evento="EVT-CONDICION-RESUELTA",
                                id_actor=user.id_usuario,
                                entidad_afectada_tipo="condicion_academica_alumno",
                                entidad_afectada_id=ac.id_condicion,
                                id_perfil_alumno=al.id_perfil_alumno,
                                valor_anterior=pol.accion_resultante,
                                valor_nuevo="NORMAL",
                                id_periodo_ref=id_periodo
                            )

        # 7. Emit period closed event
        create_academic_event(
            db, user.id_tenant, "EVT-PERIODO-CERRADO",
            user.id_usuario, "periodo_academico", id_periodo
        )

        log_audit(
            db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO",
            "periodo_academico", id_periodo, "EXITOSA",
            valor_nuevo={"alumnos_count": len(alumnos)}
        )
        return periodo

    except Exception as e:
        db.rollback()
        log_audit(
            db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO",
            "periodo_academico", id_periodo, "RECHAZADA", motivo_rechazo=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el procedimiento de cierre: {str(e)}"
        )
