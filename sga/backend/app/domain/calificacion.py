from typing import Union
from decimal import Decimal

class GradeDomainError(Exception):
    pass

class GradeSheetStatus:
    BORRADOR = "BORRADOR"
    PUBLICADO = "PUBLICADO"
    CERRADO = "CERRADO"

def validate_grade_value(
    valor: Union[float, Decimal], 
    nota_minima: Union[float, Decimal], 
    nota_maxima: Union[float, Decimal]
) -> None:
    """
    Validates that a grade is between the minimum and maximum permitted values of the scale.
    """
    val = Decimal(str(valor))
    n_min = Decimal(str(nota_minima))
    n_max = Decimal(str(nota_maxima))
    
    if val < n_min or val > n_max:
        raise GradeDomainError(
            f"La calificación {val} no se encuentra dentro del rango permitido "
            f"por la escala ({n_min} - {n_max})."
        )

def can_modify_grades(estado_componente: str) -> bool:
    """
    Grades can only be modified when the component is in BORRADOR state.
    """
    return estado_componente == GradeSheetStatus.BORRADOR

def can_publish_component(estado_componente: str) -> bool:
    """
    Enforces state transition rules. Can only publish if currently BORRADOR.
    """
    return estado_componente == GradeSheetStatus.BORRADOR

def can_close_component(estado_componente: str) -> bool:
    """
    Enforces state transition rules. Can only close if currently PUBLICADO.
    """
    return estado_componente == GradeSheetStatus.PUBLICADO

def can_correct_grade(estado_componente: str) -> bool:
    """
    Grade corrections are only allowed for closed components (CERRADO).
    """
    return estado_componente == GradeSheetStatus.CERRADO
