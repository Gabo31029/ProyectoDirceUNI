from typing import Union
from decimal import Decimal

class GradeDomainError(Exception):
    """
    Excepción lanzada cuando ocurre un error en las reglas de negocio
    relacionadas con el ingreso o modificación de calificaciones.
    """
    pass

class GradeSheetStatus:
    """
    Define los estados posibles dentro del flujo del acta de calificaciones.
    
    Flujo de ciclo de vida del acta:
    - BORRADOR: Período de ingreso y modificación de notas por parte del docente.
    - PUBLICADO: Las notas se muestran a los estudiantes; se bloquean modificaciones directas.
    - CERRADO: Inmutable. Indica el fin del período de evaluación de este componente.
    """
    BORRADOR = "BORRADOR"
    PUBLICADO = "PUBLICADO"
    CERRADO = "CERRADO"

def validate_grade_value(
    valor: Union[float, Decimal], 
    nota_minima: Union[float, Decimal], 
    nota_maxima: Union[float, Decimal]
) -> None:
    """
    Valida si una calificación numérica ingresada se encuentra dentro del rango
    permitido de la escala de evaluación configurada para el componente.

    Parámetros:
    - valor: La nota a validar.
    - nota_minima: Límite inferior permitido de la escala (e.g., 0.00).
    - nota_maxima: Límite superior permitido de la escala (e.g., 20.00 o 100.00).

    Lanza:
    - GradeDomainError si la calificación está fuera de los límites permitidos.
    """
    val = Decimal(str(valor))
    n_min = Decimal(str(nota_minima))
    n_max = Decimal(str(nota_maxima))
    
    if val < n_min or val > n_max:
        raise GradeDomainError(
            f"La calificación {val} no se encuentra dentro del rango permitido "
            f"por la escala ({n_min} - {n_max})."
        )

def can_modify_grades(estado_evaluacion: str) -> bool:
    """
    Determina si las calificaciones de una evaluación se pueden modificar.
    
    Regla de negocio:
    - Solo se permite el ingreso o modificación de calificaciones si la evaluación se encuentra en estado 'BORRADOR'.
    """
    return estado_evaluacion == GradeSheetStatus.BORRADOR

def can_publish_evaluation(estado_evaluacion: str) -> bool:
    """
    Determina si es posible publicar las calificaciones de una evaluación.
    
    Regla de negocio:
    - Solo se permite realizar la transición a 'PUBLICADO' desde el estado inicial 'BORRADOR'.
    """
    return estado_evaluacion == GradeSheetStatus.BORRADOR

def can_close_evaluation(estado_evaluacion: str) -> bool:
    """
    Determina si es posible cerrar de forma definitiva las calificaciones de una evaluación.
    
    Regla de negocio:
    - Solo se permite cerrar la evaluación si se encuentra actualmente en estado 'PUBLICADO'.
    """
    return estado_evaluacion == GradeSheetStatus.PUBLICADO

def can_correct_grade(estado_evaluacion: str) -> bool:
    """
    Determina si una calificación es elegible para una corrección administrativa.
    
    Regla de negocio:
    - Las correcciones administrativas son excepcionales y solo se aplican sobre evaluaciones en estado 'CERRADO'.
    """
    return estado_evaluacion == GradeSheetStatus.CERRADO
