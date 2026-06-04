from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.services.cierre import cerrar_acta_seccion, cerrar_periodo_academico

router = APIRouter(prefix="/cierre", tags=["Cierre Académico"])

@router.post("/secciones/{id_seccion}/cerrar-acta")
def api_cerrar_acta(
    id_seccion: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Cierra de forma definitiva el acta de calificaciones de una sección. (Solo Coordinador/Admin)
    Calcula notas finales y estados de aprobación.
    """
    inscriptions = cerrar_acta_seccion(db, id_seccion, user)
    db.commit()
    return {
        "message": "Acta de la sección cerrada correctamente.",
        "seccion_id": id_seccion,
        "alumnos_procesados": len(inscriptions)
    }

@router.post("/periodos/{id_periodo}/cerrar")
def api_cerrar_periodo(
    id_periodo: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Cierra el período académico, calculando PPS/PPA y evaluando políticas de condición académica para todos los alumnos. (Solo Admin)
    """
    periodo = cerrar_periodo_academico(db, id_periodo, user)
    db.commit()
    return {
        "message": "Período académico cerrado de forma definitiva.",
        "id_periodo": periodo.id_periodo,
        "estado": periodo.estado
    }
