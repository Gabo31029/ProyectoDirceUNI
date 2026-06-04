from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.calificacion import ComponenteEvaluacion, Calificacion, CorreccionNota

class ComponenteRepository(BaseRepository[ComponenteEvaluacion]):
    def __init__(self):
        super().__init__(ComponenteEvaluacion)

    def get_by_seccion(self, db: Session, id_seccion: str) -> List[ComponenteEvaluacion]:
        return (
            db.query(ComponenteEvaluacion)
            .filter(ComponenteEvaluacion.id_seccion == id_seccion)
            .order_by(ComponenteEvaluacion.orden_presentacion, ComponenteEvaluacion.created_at)
            .all()
        )

class CalificacionRepository(BaseRepository[Calificacion]):
    def __init__(self):
        super().__init__(Calificacion)

    def get_by_inscripcion_and_componente(
        self, db: Session, id_inscripcion: str, id_componente: str
    ) -> Optional[Calificacion]:
        return (
            db.query(Calificacion)
            .filter(
                Calificacion.id_inscripcion == id_inscripcion,
                Calificacion.id_componente == id_componente
            )
            .first()
        )

    def get_by_componente(self, db: Session, id_componente: str) -> List[Calificacion]:
        return (
            db.query(Calificacion)
            .filter(Calificacion.id_componente == id_componente)
            .all()
        )

    def get_by_seccion(self, db: Session, id_seccion: str) -> List[Calificacion]:
        return (
            db.query(Calificacion)
            .join(ComponenteEvaluacion)
            .filter(ComponenteEvaluacion.id_seccion == id_seccion)
            .all()
        )

class CorreccionNotaRepository(BaseRepository[CorreccionNota]):
    def __init__(self):
        super().__init__(CorreccionNota)

    def get_by_calificacion(self, db: Session, id_calificacion: str) -> List[CorreccionNota]:
        return (
            db.query(CorreccionNota)
            .filter(CorreccionNota.id_calificacion == id_calificacion)
            .order_by(CorreccionNota.fecha_correccion.desc())
            .all()
        )
