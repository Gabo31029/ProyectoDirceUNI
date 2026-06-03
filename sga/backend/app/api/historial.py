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
    Obtiene el historial académico consolidado del alumno (notas, promedios y condiciones).
    """
    return obtener_historial_consolidado(db, id_perfil_alumno, user)

@router.get("/alumnos/{id_perfil_alumno}/pdf")
def api_descargar_pdf(
    id_perfil_alumno: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Genera y descarga el récord oficial de notas del alumno en formato PDF.
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
