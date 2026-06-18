from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.calificacion import ComponenteEvaluacion, Calificacion, CorreccionNota

class ComponenteRepository(BaseRepository[ComponenteEvaluacion]):
    """
    Repositorio encargado del acceso y persistencia de datos para ComponenteEvaluacion.
    Hereda del repositorio base genérico (BaseRepository).
    """
    def __init__(self):
        super().__init__(ComponenteEvaluacion)

    def get_by_seccion(self, db: Session, id_seccion: str) -> List[ComponenteEvaluacion]:
        """
        Recupera la lista de todos los componentes de evaluación asociados a una sección.
        
        Ordena los resultados primero por el orden de presentación configurado y luego por
        su fecha de creación.
        """
        return (
            db.query(ComponenteEvaluacion)
            .filter(ComponenteEvaluacion.id_seccion == id_seccion)
            .order_by(ComponenteEvaluacion.orden_presentacion, ComponenteEvaluacion.created_at)
            .all()
        )

class CalificacionRepository(BaseRepository[Calificacion]):
    """
    Repositorio encargado del acceso y persistencia de calificaciones (Calificacion).
    Hereda del repositorio base genérico (BaseRepository).
    """
    def __init__(self):
        super().__init__(Calificacion)

    def get_by_inscripcion_and_componente(
        self, db: Session, id_inscripcion: str, id_componente: str
    ) -> Optional[Calificacion]:
        """
        Busca y retorna el registro de calificación de un estudiante en un componente específico.
        
        Garantiza el cumplimiento de la restricción de unicidad de combinación.
        """
        return (
            db.query(Calificacion)
            .filter(
                Calificacion.id_inscripcion == id_inscripcion,
                Calificacion.id_componente == id_componente
            )
            .first()
        )

    def get_by_componente(self, db: Session, id_componente: str) -> List[Calificacion]:
        """
        Recupera el listado completo de calificaciones asentadas para un componente de evaluación.
        """
        return (
            db.query(Calificacion)
            .filter(Calificacion.id_componente == id_componente)
            .all()
        )

    def get_by_seccion(self, db: Session, id_seccion: str) -> List[Calificacion]:
        """
        Recupera todas las calificaciones de los estudiantes inscritos en una sección.
        Realiza un JOIN implícito con la tabla ComponenteEvaluacion.
        """
        return (
            db.query(Calificacion)
            .join(ComponenteEvaluacion)
            .filter(ComponenteEvaluacion.id_seccion == id_seccion)
            .all()
        )

class CorreccionNotaRepository(BaseRepository[CorreccionNota]):
    """
    Repositorio para la persistencia e historial de correcciones administrativas (CorreccionNota).
    Hereda del repositorio base genérico (BaseRepository).
    """
    def __init__(self):
        super().__init__(CorreccionNota)

    def get_by_calificacion(self, db: Session, id_calificacion: str) -> List[CorreccionNota]:
        """
        Retorna la lista histórica de correcciones aplicadas sobre una calificación específica,
        ordenadas cronológicamente de forma descendente (la última corrección primero).
        """
        return (
            db.query(CorreccionNota)
            .filter(CorreccionNota.id_calificacion == id_calificacion)
            .order_by(CorreccionNota.fecha_correccion.desc())
            .all()
        )
