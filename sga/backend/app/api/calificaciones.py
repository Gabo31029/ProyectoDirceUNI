from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from decimal import Decimal
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.services.calificacion import registrar_calificaciones, publicar_componente, corregir_calificacion

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])

# Request Schemas
class CalificacionInput(BaseModel):
    id_inscripcion: str = Field(..., description="ID de la inscripción del alumno")
    valor_nota: float = Field(..., ge=0.0, description="Valor numérico de la calificación")

class RegistroCalificacionesRequest(BaseModel):
    calificaciones: List[CalificacionInput]

class CorreccionRequest(BaseModel):
    valor_nuevo: float = Field(..., ge=0.0, description="Nueva calificación corregida")
    justificacion: str = Field(..., min_length=5, max_length=1000, description="Justificación de la corrección")

@router.post("/secciones/{id_seccion}/componentes/{id_componente}", status_code=status.HTTP_201_CREATED)
def api_registrar_calificaciones(
    id_seccion: str,
    id_componente: str,
    payload: RegistroCalificacionesRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Ingresa o actualiza calificaciones de alumnos para un componente de evaluación. (Solo Docente/Admin)
    """
    calificaciones_in = [{"id_inscripcion": c.id_inscripcion, "valor_nota": Decimal(str(c.valor_nota))} for c in payload.calificaciones]
    res = registrar_calificaciones(db, id_seccion, id_componente, calificaciones_in, user)
    db.commit()
    return {"message": "Calificaciones registradas correctamente en borrador.", "count": len(res)}

@router.put("/secciones/{id_seccion}/componentes/{id_componente}/publicar")
def api_publicar_componente(
    id_seccion: str,
    id_componente: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Publica las calificaciones de un componente haciéndolas visibles para los alumnos.
    """
    comp = publicar_componente(db, id_seccion, id_componente, user)
    db.commit()
    return {"message": "Componente publicado correctamente.", "id_componente": comp.id_componente, "estado": comp.estado}

@router.post("/{id_calificacion}/corregir")
def api_corregir_calificacion(
    id_calificacion: str,
    payload: CorreccionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Corrige una calificación previamente cerrada en un acta de notas. (Solo Administrador)
    """
    calif = corregir_calificacion(db, id_calificacion, Decimal(str(payload.valor_nuevo)), payload.justificacion, user)
    db.commit()
    return {
        "message": "Corrección de calificación aplicada exitosamente.",
        "id_calificacion": calif.id_calificacion,
        "nuevo_valor": float(calif.valor_nota),
        "id_inscripcion": calif.id_inscripcion
    }
