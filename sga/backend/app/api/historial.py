from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.services.historial import obtener_historial_consolidado, generar_record_notas_pdf

router = APIRouter(prefix="/historial", tags=["Historial Académico"])

@router.get("/alumnos/{id_perfil_alumno}")
def api_obtener_historial(
    id_perfil_alumno: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint para obtener el historial académico consolidado en formato JSON.

    Seguridad y acceso:
    - Si el usuario logueado es ALUMNO, solo puede consultar su propio ID.
    - Docentes y Administradores tienen acceso irrestricto de consulta.
    - Muestra detalle de materias agrupadas por períodos, PPS/PPA históricos y alertas activas.
    """
    return obtener_historial_consolidado(db, id_perfil_alumno, user)

@router.get("/alumnos/{id_perfil_alumno}/pdf")
def api_descargar_pdf(
    id_perfil_alumno: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint para generar y descargar en formato PDF el récord oficial de notas del estudiante.

    Seguridad y respuesta HTTP:
    - Comparte la misma política de control de accesos que la consulta JSON.
    - Retorna una respuesta de tipo streaming / bytes con la cabecera `Content-Disposition`
      configurada como adjunto (attachment) para forzar la descarga en el navegador.
    """
    pdf_content = generar_record_notas_pdf(db, id_perfil_alumno, user)
    
    headers = {
        "Content-Disposition": f"attachment; filename=record_notas_{id_perfil_alumno}.pdf"
    }
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers=headers
    )
