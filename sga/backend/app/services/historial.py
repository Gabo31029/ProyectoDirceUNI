from typing import Dict, Any, List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from fpdf import FPDF
from app.core.security import CurrentUser
from app.core.audit import log_audit
from app.repositories.historial import HistorialRepository
from app.repositories.cierre import CondicionAcademicaRepository
from app.models.core_schemas import PerfilAlumno, PeriodoAcademico
from app.models.cierre import SnapshotPromedio

historial_repo = HistorialRepository()
condicion_repo = CondicionAcademicaRepository()

def obtener_historial_consolidado(
    db: Session,
    id_perfil_alumno: str,
    user: CurrentUser
) -> Dict[str, Any]:
    """
    Caso de uso: Compila y retorna el historial académico consolidado de un estudiante en formato JSON.

    Reglas de negocio y seguridad:
    - Control de accesos (RBAC):
        * Si el rol es ALUMNO, solo se le permite consultar su propio perfil (`id_perfil_alumno`).
        * Los roles DOCENTE y ADMINISTRADOR pueden consultar el historial de cualquier estudiante.
    - Consolidación y procesamiento de datos:
        1. Recupera las inscripciones históricas, snapshots de promedios y condiciones académicas.
        2. Filtrado de snapshots: Agrupa por período y conserva únicamente la versión de promedio más reciente
           (por ejemplo, resolviendo recálculos intermedios tras correcciones de notas).
        3. Agrupación por períodos: Mapea las inscripciones de asignaturas dentro de su respectivo período académico,
           anexando el PPS y PPA correspondiente a dicho período académico.
        4. Ordenamiento cronológico de los períodos académicos de forma ascendente.
    - Auditoría: Registra la operación 'CONSULTAR_HISTORIAL' en la tabla de auditoría.
    """
    # Validar existencia del perfil de alumno (buscando por id_perfil_alumno o id_usuario)
    perfil = db.query(PerfilAlumno).filter(
        (PerfilAlumno.id_perfil_alumno == id_perfil_alumno) | (PerfilAlumno.id_usuario == id_perfil_alumno)
    ).first()
    if not perfil:
        log_audit(db, user.id_tenant, user.id_usuario, "CONSULTAR_HISTORIAL", "perfil_alumno", id_perfil_alumno, "RECHAZADA", motivo_rechazo="Perfil del alumno no encontrado.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil del alumno no encontrado.")

    # Resolver el id_perfil_alumno correcto
    id_perfil_alumno = perfil.id_perfil_alumno

    # Control de accesos
    if user.rol == "ALUMNO" and user.id_perfil != id_perfil_alumno and user.id_usuario != id_perfil_alumno:
        log_audit(db, user.id_tenant, user.id_usuario, "CONSULTAR_HISTORIAL", "perfil_alumno", id_perfil_alumno, "RECHAZADA", motivo_rechazo="Alumno intentando ver otro historial.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver el historial de otro alumno.")

    # 1. Recuperar los datos desde el repositorio optimizado
    inscriptions = historial_repo.get_inscriptions_history(db, id_perfil_alumno)
    snapshots = historial_repo.get_snapshots_history(db, id_perfil_alumno)
    conditions = historial_repo.get_conditions_history(db, id_perfil_alumno)

    # 2. Filtrado: Mantener el último promedio por período (el de mayor fecha de creación)
    latest_snapshots_by_period = {}
    for snap in snapshots:
        latest_snapshots_by_period[snap.id_periodo] = snap

    # 3. Estructurar y agrupar inscripciones de cursos por período académico
    from app.models.calificacion import EvaluacionAcademica, Calificacion
    periods_map = {}
    creditos_aprobados = 0

    for ins, seccion, curso, periodo in inscriptions:
        pid = periodo.id_periodo
        if pid not in periods_map:
            periods_map[pid] = {
                "id_periodo": pid,
                "nombre_periodo": periodo.nombre_periodo,
                "fecha_inicio": periodo.fecha_inicio,
                "inscripciones": [],
                "pps": 0.00,
                "ppa": 0.00
            }
            
        # Obtener evaluaciones y calificaciones correspondientes para este curso
        evaluaciones = db.query(EvaluacionAcademica).filter(
            EvaluacionAcademica.id_seccion == ins.id_seccion
        ).all()
        
        calificaciones = db.query(Calificacion).filter(
            Calificacion.id_inscripcion == ins.id_inscripcion
        ).all()
        
        calif_map = {c.id_evaluacion: c for c in calificaciones}
        
        eval_list = []
        for ev in evaluaciones:
            c = calif_map.get(ev.id_evaluacion)
            eval_list.append({
                "id_evaluacion": ev.id_evaluacion,
                "nombre_tipo_evaluacion": ev.tipo_evaluacion.nombre if ev.tipo_evaluacion else ev.id_tipo_evaluacion,
                "peso_relativo": float(ev.peso_relativo),
                "nota": float(c.valor_nota) if c and c.valor_nota is not None else None,
                "estado_nota": c.estado if c else "PENDIENTE"
            })
            
        # Calcular promedio ponderado del curso dinámicamente si no está asentado
        graded_evals = [e for e in eval_list if e["nota"] is not None]
        if ins.nota_final is not None:
            promedio_curso = float(ins.nota_final)
        elif graded_evals:
            sum_pesos = sum(e["peso_relativo"] for e in graded_evals)
            sum_prod = sum(e["nota"] * e["peso_relativo"] for e in graded_evals)
            promedio_curso = round(sum_prod / sum_pesos, 2) if sum_pesos > 0 else 0.0
        else:
            promedio_curso = None
            
        if ins.estado == "APROBADA":
            creditos_aprobados += curso.creditos
            
        periods_map[pid]["inscripciones"].append({
            "id_inscripcion": ins.id_inscripcion,
            "codigo_curso": curso.codigo_curso,
            "nombre_curso": curso.nombre_curso,
            "creditos": curso.creditos,
            "nota_final": float(ins.nota_final) if ins.nota_final is not None else None,
            "promedio_ponderado_curso": promedio_curso,
            "estado": ins.estado,
            "codigo_seccion": seccion.codigo_seccion,
            "evaluaciones": eval_list
        })

    # Vincular los promedios semestral y acumulado a la estructura de cada período
    for pid, p_data in periods_map.items():
        snap = latest_snapshots_by_period.get(pid)
        if snap:
            p_data["pps"] = float(snap.pps)
            p_data["ppa"] = float(snap.ppa)

    # Ordenar la lista de períodos cronológicamente
    sorted_periods = sorted(periods_map.values(), key=lambda x: x["fecha_inicio"])
    for p in sorted_periods:
        del p["fecha_inicio"]  # Limpiar el objeto date no serializable antes de la respuesta

    # 4. Formatear la lista histórica de condiciones académicas
    formatted_conditions = []
    for cond in conditions:
        formatted_conditions.append({
            "id_condicion": cond.id_condicion,
            "nombre_condicion": cond.tipo_condicion.nombre,
            "codigo_condicion": cond.tipo_condicion.codigo,
            "estado": cond.estado,
            "fecha_activacion": cond.fecha_activacion.isoformat() if cond.fecha_activacion else None,
            "fecha_resolucion": cond.fecha_resolucion.isoformat() if cond.fecha_resolucion else None,
            "observaciones": cond.observaciones
        })

    # Obtener el PPA actual global vigente
    latest_snap = db.query(SnapshotPromedio).join(PeriodoAcademico).filter(
        SnapshotPromedio.id_perfil_alumno == id_perfil_alumno
    ).order_by(PeriodoAcademico.fecha_fin.desc(), SnapshotPromedio.created_at.desc()).first()
    
    ppa_actual = float(latest_snap.ppa) if latest_snap else 0.00

    condicion_academica = "NORMAL"
    active_conds = [c for c in formatted_conditions if c["estado"] == "ACTIVA"]
    if active_conds:
        condicion_academica = active_conds[-1]["nombre_condicion"]

    resumen = {
        "ppa": ppa_actual,
        "creditos_aprobados": creditos_aprobados,
        "condicion_academica": condicion_academica
    }

    log_audit(db, user.id_tenant, user.id_usuario, "CONSULTAR_HISTORIAL", "perfil_alumno", id_perfil_alumno, "EXITOSA")
    
    return {
        "id_perfil_alumno": id_perfil_alumno,
        "codigo_alumno": perfil.codigo_alumno,
        "nombre_completo": perfil.usuario.nombre_completo,
        "carrera": perfil.carrera,
        "ppa_actual": ppa_actual,
        "resumen": resumen,
        "periodos": sorted_periods,
        "condiciones": formatted_conditions
    }

def generar_record_notas_pdf(
    db: Session,
    id_perfil_alumno: str,
    user: CurrentUser
) -> bytes:
    """
    Caso de uso: Genera un documento PDF oficial del récord de notas del estudiante.

    Reglas de negocio y diseño del reporte:
    - Utiliza la librería fpdf2 para la construcción programática y estructurada del PDF.
    - Se reutiliza la lógica del caso de uso `obtener_historial_consolidado` para obtener los datos
      asegurando que se apliquen las mismas validaciones de seguridad y filtrado de versiones de promedios.
    - Estructura visual:
        1. Encabezado institucional y metadatos del estudiante (nombre, código, carrera, PPA global).
        2. Detalle tabular por período académico: lista de asignaturas con sus créditos, nota final obtenida,
           estado (Aprobado/Desaprobado) y resumen del PPS y PPA al finalizar dicho semestre.
        3. Historial de condiciones académicas (alertas de riesgo, resoluciones y observaciones).
        4. Firma y sello digital de seguridad con fecha y hora de generación.
    - Manejo de bytes: Exporta el PDF como cadena de caracteres cruda (latin-1) y la codifica a bytes
      para ser enviada como stream de datos en la respuesta HTTP.
    """
    hist = obtener_historial_consolidado(db, id_perfil_alumno, user)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Título del Reporte
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "SISTEMA DE GESTION ACADEMICA (SGA)", ln=True, align="C")
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "RECORD OFICIAL DE NOTAS", ln=True, align="C")
    pdf.ln(5)
    
    # Encabezado con información académica del estudiante
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(40, 6, "Alumno:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, hist["nombre_completo"], ln=True)
    
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(40, 6, "Codigo:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, hist["codigo_alumno"], ln=True)
    
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(40, 6, "Carrera:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, hist["carrera"], ln=True)
    
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(40, 6, "PPA Actual:")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, f"{hist['ppa_actual']:.2f}", ln=True)
    pdf.ln(10)
    
    # Renderizar tablas agrupadas por período académico
    for per in hist["periodos"]:
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.cell(0, 8, f"Periodo Academico: {per['nombre_periodo']}", ln=True)
        
        # Cabecera de la tabla
        pdf.set_font("Helvetica", style="B", size=9)
        pdf.cell(25, 6, "Codigo", border=1)
        pdf.cell(90, 6, "Curso", border=1)
        pdf.cell(15, 6, "Cred", border=1, align="C")
        pdf.cell(20, 6, "Nota", border=1, align="C")
        pdf.cell(30, 6, "Estado", border=1, align="C")
        pdf.ln()
        
        # Cuerpo de la tabla con los cursos inscritos
        pdf.set_font("Helvetica", size=9)
        for ins in per["inscripciones"]:
            pdf.cell(25, 6, ins["codigo_curso"], border=1)
            pdf.cell(90, 6, ins["nombre_curso"], border=1)
            pdf.cell(15, 6, str(ins["creditos"]), border=1, align="C")
            
            nota_str = f"{ins['nota_final']:.2f}" if ins["nota_final"] is not None else "---"
            pdf.cell(20, 6, nota_str, border=1, align="C")
            pdf.cell(30, 6, ins["estado"], border=1, align="C")
            pdf.ln()
            
        # Promedios del período (Semestral y Acumulado)
        pdf.set_font("Helvetica", style="I", size=9)
        pdf.cell(0, 6, f"Promedio Ponderado Semestral (PPS): {per['pps']:.2f}  |  Promedio Ponderado Acumulado (PPA): {per['ppa']:.2f}", ln=True)
        pdf.ln(5)

    # Historial de alertas de condiciones académicas (si existen)
    if hist["condiciones"]:
        pdf.ln(5)
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.cell(0, 8, "Historial de Condiciones Académicas", ln=True)
        
        pdf.set_font("Helvetica", style="B", size=9)
        pdf.cell(50, 6, "Condicion", border=1)
        pdf.cell(30, 6, "Estado", border=1, align="C")
        pdf.cell(40, 6, "Fecha Activacion", border=1, align="C")
        pdf.cell(70, 6, "Observaciones", border=1)
        pdf.ln()
        
        pdf.set_font("Helvetica", size=9)
        for cond in hist["condiciones"]:
            pdf.cell(50, 6, cond["nombre_condicion"], border=1)
            pdf.cell(30, 6, cond["estado"], border=1, align="C")
            pdf.cell(40, 6, cond["fecha_activacion"][:10], border=1, align="C")
            obs = cond["observaciones"] or ""
            if len(obs) > 40:
                obs = obs[:37] + "..."
            pdf.cell(70, 6, obs, border=1)
            pdf.ln()

    # Pie de página oficial y firma digital
    pdf.ln(15)
    pdf.set_font("Helvetica", style="I", size=8)
    pdf.cell(0, 4, f"Documento generado de forma oficial el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.cell(0, 4, "Sello Digital de Seguridad - Validado por la Oficina de Asuntos Academicos", ln=True, align="C")
    
    # Conversión del PDF generado en memoria a un flujo de bytes
    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1")
    elif isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
        
    log_audit(db, user.id_tenant, user.id_usuario, "DESCARGAR_RECORD_NOTAS", "perfil_alumno", id_perfil_alumno, "EXITOSA")
    return pdf_bytes
