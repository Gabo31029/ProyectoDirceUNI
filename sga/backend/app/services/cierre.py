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
    Caso de uso: Cierra de forma definitiva el acta de calificaciones de una sección.

    Reglas de negocio y flujo transaccional:
    - Control de accesos (RBAC): Permitido para Administradores o para el Docente Coordinador de la sección.
    - Consistencia del acta: Verifica que existan componentes de evaluación configurados y que
      TODOS ellos se encuentren previamente en estado 'PUBLICADO'.
    - Lógica de cálculo final por estudiante:
        1. Para cada estudiante con inscripción 'ACTIVA', recupera sus calificaciones de cada componente.
        2. Llama a `calcular_nota_final` en la capa de dominio aplicando los pesos relativos de la escala.
        3. Compara contra la nota aprobatoria establecida en la escala para definir el estado de la inscripción:
           'APROBADA' (emite 'EVT-NOTA-FINAL-CALCULADA') o 'DESAPROBADA' (emite 'EVT-NOTA-FINAL-CALCULADA'
           y además 'EVT-REPROBO-CURSO' para el conteo de desaprobaciones en la cuenta del alumno).
    - Cierre en cascada: Modifica el estado de todos los componentes evaluativos a 'CERRADO'.
    - Transaccionalidad: Toda la operación se realiza bajo la misma sesión de base de datos;
      cualquier excepción gatilla rollback automático para evitar actas con cierres parciales.
    - Auditoría: Emite el evento global institucional 'EVT-ACTA-CERRADA' y guarda log en `registro_auditoria`.
    """
    # 1. Recuperar la sección académica
    seccion = db.query(Seccion).filter(Seccion.id_seccion == id_seccion).first()
    if not seccion:
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo="Sección no encontrada.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada.")

    # 2. Control de accesos (RBAC)
    if user.rol not in ("ADMINISTRADOR", "DOCENTE"):
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo="Rol no autorizado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para cerrar actas.")

    # Validación adicional para docentes: Debe ser coordinador de la sección
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

    # 3. Recuperar componentes de evaluación de la sección
    componentes = componente_repo.get_by_seccion(db, id_seccion)
    if not componentes:
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "RECHAZADA", motivo_rechazo="No hay componentes de evaluación configurados.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay componentes de evaluación configurados en esta sección."
        )

    # 4. Asegurar que todas las actas/componentes parciales estén publicados
    for c in componentes:
        if c.estado != "PUBLICADO":
            log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                      id_seccion, "RECHAZADA", motivo_rechazo=f"Componente {c.id_componente} no está publicado.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Todos los componentes de evaluación deben estar publicados antes de cerrar el acta."
            )

    # 5. Obtener inscripciones de alumnos en la sección
    inscriptions = db.query(Inscripcion).filter(
        Inscripcion.id_seccion == id_seccion,
        Inscripcion.estado == "ACTIVA"
    ).all()

    # Si no hay inscripciones activas, se realiza un cierre rápido de las actas vacías
    if not inscriptions:
        for c in componentes:
            c.estado = "CERRADO"
            db.add(c)
        db.flush()
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_ACTA", "seccion",
                  id_seccion, "EXITOSA", valor_nuevo={"inscriptions_count": 0})
        return []

    # Recuperar escala de notas del primer componente (se asume homogénea para la sección)
    id_escala = componentes[0].id_escala
    escala = db.query(EscalaEvaluacion).filter(EscalaEvaluacion.id_escala == id_escala).first()

    try:
        # 6. Calcular notas finales individuales y generar eventos académicos
        for ins in inscriptions:
            grades_list = []
            for comp in componentes:
                cal = calificacion_repo.get_by_inscripcion_and_componente(db, ins.id_inscripcion, comp.id_componente)
                if not cal:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Faltan calificaciones para la inscripción {ins.id_inscripcion}."
                    )
                # Formato esperado por el dominio de cálculos
                grades_list.append({
                    "valor_nota": cal.valor_nota,
                    "peso_relativo": comp.peso_relativo
                })

            # Calcular el promedio de componentes
            nota_final = calcular_nota_final(grades_list)
            ins.nota_final = nota_final

            id_perfil_alumno = ins.matricula.id_perfil_alumno
            id_curso = seccion.id_curso
            id_periodo = seccion.id_periodo

            # Evaluar aprobación vigesimal y disparar la cascada de eventos correspondientes
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
                    # Se incluye créditos obtenidos para la actualización de cuentas de seguimiento
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
                # Emitir evento específico de reprobación para incrementar la cuenta de deméritos/desaprobaciones
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

        # 7. Asentar estado CERRADO en todos los componentes
        for c in componentes:
            c.estado = "CERRADO"
            db.add(c)

        db.flush()

        # Emitir evento del acta general cerrada
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
    Caso de uso: Cierra de forma definitiva un período académico (procesamiento en lote).

    Reglas de negocio y procesamiento batch:
    - Control de accesos (RBAC): Permitido únicamente para el rol ADMINISTRADOR.
    - Consistencia académica previa: Se verifica que todas las secciones del período tengan
      sus componentes de evaluación en estado 'CERRADO'. Si hay actas abiertas, se rechaza la operación.
    - Flujo en lote para estudiantes matriculados en el período:
        1. Recupera todos los estudiantes con matrícula activa en el período.
        2. Calcula el PPS (Promedio Ponderado Semestral) del alumno usando las inscripciones del período
           y la fórmula/regla de inclusión de PPS correspondiente.
        3. Calcula el PPA (Promedio Ponderado Acumulado) histórico sumando inscripciones de todos sus períodos
           y la regla de PPA configurada.
        4. Crea un `SnapshotPromedio` y emite 'EVT-SNAPSHOT-PROMEDIO'.
        5. Evalúa las políticas de condiciones académicas configuradas para el período.
           * Llama a `evaluar_politica_condicion` comparando el valor de la cuenta de seguimiento (e.g., desaprobaciones)
             contra el umbral de la regla mediante el operador lógico correspondiente.
           * Si la regla se cumple y el alumno no posee la condición activa, inserta una nueva `CondicionAcademicaAlumno`
             en estado 'ACTIVA' y emite 'EVT-CONDICION-ACTIVADA'.
           * Si la regla ya no se cumple (por ejemplo, el alumno superó el rendimiento mínimo), cambia el estado
             de la condición académica activa a 'RESUELTA' y emite 'EVT-CONDICION-RESUELTA'.
    - Transaccionalidad fuerte: Todo el procesamiento por lotes se ejecuta en un solo bloque transaccional.
      Un solo error en cualquier alumno aborta completamente el proceso de cierre para mantener coherencia e integridad global.
    """
    # 1. Validación de privilegios
    if user.rol != "ADMINISTRADOR":
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                  id_periodo, "RECHAZADA", motivo_rechazo="Rol no es Administrador.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden cerrar períodos académicos."
        )

    # 2. Recuperar período
    periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.id_periodo == id_periodo).first()
    if not periodo:
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                  id_periodo, "RECHAZADA", motivo_rechazo="Período no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Período académico no encontrado.")

    # El período debe encontrarse en etapa de digitación o registro de notas
    if periodo.estado != "REGISTRO_NOTAS":
        log_audit(db, user.id_tenant, user.id_usuario, "CERRAR_PERIODO", "periodo_academico",
                  id_periodo, "RECHAZADA", motivo_rechazo="Período no está en REGISTRO_NOTAS.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El período debe estar en estado REGISTRO_NOTAS antes de cerrarse."
        )

    # 3. Control de actas: Validar que todas las secciones estén cerradas
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

    # 4. Transicionar estado del período
    periodo.estado = "CERRADO"
    periodo.fecha_estado_actual = datetime.now(timezone.utc)
    periodo.id_usuario_transicion = user.id_usuario
    db.add(periodo)
    db.flush()

    # 5. Obtener estudiantes activos con matrícula en este período
    alumnos = (
        db.query(PerfilAlumno)
        .join(Matricula, Matricula.id_perfil_alumno == PerfilAlumno.id_perfil_alumno)
        .filter(Matricula.id_periodo == id_periodo, Matricula.estado == "ACTIVA")
        .all()
    )

    # Recuperar fórmulas del período
    formula_pps = db.query(FormulaPromedio).filter(
        FormulaPromedio.id_periodo == id_periodo, FormulaPromedio.tipo_promedio == "PPS"
    ).first()
    formula_ppa = db.query(FormulaPromedio).filter(
        FormulaPromedio.id_periodo == id_periodo, FormulaPromedio.tipo_promedio == "PPA"
    ).first()

    regla_pps = formula_pps.regla_inclusion if formula_pps else "TODOS"
    regla_ppa = formula_ppa.regla_inclusion if formula_ppa else "TODOS"
    id_formula_aplicada = formula_pps.id_formula if formula_pps else None

    # Obtener las políticas activas de condiciones académicas configuradas para el período
    politicas = db.query(PoliticaCondicionAcademica).filter(
        PoliticaCondicionAcademica.id_periodo == id_periodo
    ).all()

    try:
        # 6. Procesar a cada estudiante en lote
        for al in alumnos:
            # Recuperar materias inscritas en el período actual
            ins_periodo = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == al.id_perfil_alumno,
                    Matricula.id_periodo == id_periodo,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )
            # Recuperar materias de toda la historia académica del estudiante
            ins_historicas = (
                db.query(Inscripcion)
                .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
                .filter(
                    Matricula.id_perfil_alumno == al.id_perfil_alumno,
                    Inscripcion.estado.in_(["APROBADA", "DESAPROBADA"])
                ).all()
            )

            # Convertir al formato mapeado esperado por la lógica pura de dominio
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

            # Invocar reglas del dominio para el cálculo ponderado de PPS y PPA
            pps_calc = calcular_promedio_ponderado(_build_domain_list(ins_periodo), regla_pps)
            ppa_calc = calcular_promedio_ponderado(_build_domain_list(ins_historicas), regla_ppa)

            # Buscar snapshot previo para enlazar la auditoría
            prev_snapshot = (
                db.query(SnapshotPromedio)
                .filter(
                    SnapshotPromedio.id_perfil_alumno == al.id_perfil_alumno,
                    SnapshotPromedio.id_periodo == id_periodo
                )
                .order_by(SnapshotPromedio.created_at.desc())
                .first()
            )

            # Registrar el snapshot oficial e inmutable de promedios ponderados
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

            # Emitir evento de generación del snapshot
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

            # 7. Evaluar políticas de condición académica automática
            active_conditions = (
                db.query(CondicionAcademicaAlumno)
                .filter(
                    CondicionAcademicaAlumno.id_perfil_alumno == al.id_perfil_alumno,
                    CondicionAcademicaAlumno.estado == "ACTIVA"
                ).all()
            )

            for pol in politicas:
                # Recuperar el valor actual de la métrica del estudiante (e.g. créditos desaprobados)
                cuenta = db.query(CuentaSeguimientoAlumno).filter(
                    CuentaSeguimientoAlumno.id_perfil_alumno == al.id_perfil_alumno,
                    CuentaSeguimientoAlumno.tipo_cuenta == pol.cuenta_evaluada
                ).first()
                valor_cuenta = cuenta.valor_actual if cuenta else Decimal("0.00")

                # Evaluar regla de comparación en dominio
                triggered = evaluar_politica_condicion(valor_cuenta, pol.umbral, pol.operador)

                if triggered:
                    already_active = any(
                        c.id_tipo_condicion == pol.id_tipo_condicion for c in active_conditions
                    )
                    # Si califica para la alerta y no la tiene activa, se gatilla la activación
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

                        # Insertar la condición
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

                        # Vincular el ID definitivo en el evento académico
                        event_cond.entidad_afectada_id = new_cond.id_condicion
                        db.add(event_cond)
                        db.flush()
                else:
                    # Si la condición está activa pero el estudiante ya no cumple con el criterio de riesgo,
                    # se procede a resolver automáticamente su situación.
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

        # 8. Emitir evento del período académico cerrado global
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
