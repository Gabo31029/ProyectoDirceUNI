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
    Endpoint para realizar el cierre definitivo de las calificaciones de una sección.

    Seguridad y transaccionalidad:
    - Restringido a Docente Coordinador de la sección o Administrador.
    - Cierra en cascada las evaluaciones y calcula la nota final promedio de las inscripciones.
    - Manejo transaccional: Llama a `db.commit()` tras confirmar el éxito de la operación.
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
    Endpoint para ejecutar el cierre batch total de un período académico.

    Seguridad y transaccionalidad:
    - Permitido exclusivamente para el rol ADMINISTRADOR.
    - Lógica batch: Calcula PPS/PPA para todos los estudiantes matriculados en el período
      y evalúa las políticas de riesgo/condiciones académicas de forma masiva.
    - Manejo transaccional: Llama a `db.commit()` al finalizar de procesar a todos los estudiantes.
    """
    periodo = cerrar_periodo_academico(db, id_periodo, user)
    db.commit()
    return {
        "message": "Período académico cerrado de forma definitiva.",
        "id_periodo": periodo.id_periodo,
        "estado": periodo.estado
    }
