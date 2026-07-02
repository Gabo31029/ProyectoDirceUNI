from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from decimal import Decimal
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.services.calificacion import registrar_calificaciones, publicar_evaluacion, corregir_calificacion

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])

# Esquemas de Petición (Request Schemas)
class CalificacionInput(BaseModel):
    """
    Esquema de entrada para el registro individual de calificaciones.
    """
    id_inscripcion: str = Field(..., description="ID de la inscripción del alumno")
    valor_nota: float = Field(..., ge=0.0, description="Valor numérico de la calificación")

class RegistroCalificacionesRequest(BaseModel):
    """
    Esquema de envoltura para procesar un lote de calificaciones en una sola petición.
    """
    calificaciones: List[CalificacionInput]

class CorreccionRequest(BaseModel):
    """
    Esquema de entrada para solicitar una corrección administrativa de nota.
    """
    valor_nuevo: float = Field(..., ge=0.0, description="Nueva calificación corregida")
    justificacion: str = Field(..., min_length=5, max_length=1000, description="Justificación de la corrección")

@router.post("/secciones/{id_seccion}/evaluaciones/{id_evaluacion}", status_code=status.HTTP_201_CREATED)
def api_registrar_calificaciones(
    id_seccion: str,
    id_evaluacion: str,
    payload: RegistroCalificacionesRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint para ingresar o actualizar calificaciones de estudiantes para una evaluación en borrador.

    Seguridad y control:
    - Restringido a Docente asignado a la sección o Administrador.
    - Manejo transaccional: Tras la ejecución exitosa del caso de uso en la capa de servicios,
      se realiza el `db.commit()` para persistir el lote de calificaciones.
    """
    calificaciones_in = [{"id_inscripcion": c.id_inscripcion, "valor_nota": Decimal(str(c.valor_nota))} for c in payload.calificaciones]
    res = registrar_calificaciones(db, id_seccion, id_evaluacion, calificaciones_in, user)
    db.commit()
    return {"message": "Calificaciones registradas correctamente en borrador.", "count": len(res)}

@router.put("/secciones/{id_seccion}/evaluaciones/{id_evaluacion}/publicar")
def api_publicar_evaluacion(
    id_seccion: str,
    id_evaluacion: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint para publicar de forma oficial las calificaciones de una evaluación.

    Seguridad y control:
    - Restringido a Docente Coordinador de la sección o Administrador.
    - Efecto colateral: Las calificaciones cambian a estado PUBLICADO y son visibles para el estudiante.
    - Manejo transaccional: Confirma los cambios mediante `db.commit()`.
    """
    comp = publicar_evaluacion(db, id_seccion, id_evaluacion, user)
    db.commit()
    return {"message": "Evaluación publicada correctamente.", "id_evaluacion": comp.id_evaluacion, "estado": comp.estado}

@router.post("/{id_calificacion}/corregir")
def api_corregir_calificacion(
    id_calificacion: str,
    payload: CorreccionRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint para realizar una corrección administrativa de nota sobre una evaluación cerrada.

    Seguridad y control:
    - Permitido de forma exclusiva para administradores.
    - Lógica colateral: Provoca recálculo de la nota final del curso y regeneración del promedio
      acumulado (PPA) y semestral (PPS) si el período correspondiente ya está cerrado.
    - Manejo transaccional: Garantiza atomicidad persistiendo los cambios mediante `db.commit()`.
    """
    calif = corregir_calificacion(db, id_calificacion, Decimal(str(payload.valor_nuevo)), payload.justificacion, user)
    db.commit()
    return {
        "message": "Corrección de calificación aplicada exitosamente.",
        "id_calificacion": calif.id_calificacion,
        "nuevo_valor": float(calif.valor_nota),
        "id_inscripcion": calif.id_inscripcion
    }
