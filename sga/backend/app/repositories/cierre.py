from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.cierre import FormulaPromedio, SnapshotPromedio, CondicionAcademicaAlumno
from app.models.core_schemas import PeriodoAcademico

class FormulaPromedioRepository(BaseRepository[FormulaPromedio]):
    """
    Repositorio encargado del acceso y persistencia de las fórmulas de promedio (FormulaPromedio).
    Hereda del repositorio base genérico (BaseRepository).
    """
    def __init__(self):
        super().__init__(FormulaPromedio)

    def get_by_periodo_and_tipo(
        self, db: Session, id_periodo: str, tipo_promedio: str
    ) -> Optional[FormulaPromedio]:
        """
        Recupera la fórmula de promedio asignada a un período académico y tipo específico (PPS o PPA).
        """
        return (
            db.query(FormulaPromedio)
            .filter(
                FormulaPromedio.id_periodo == id_periodo,
                FormulaPromedio.tipo_promedio == tipo_promedio
            )
            .first()
        )

class SnapshotPromedioRepository(BaseRepository[SnapshotPromedio]):
    """
    Repositorio para el manejo de capturas históricas de promedios (SnapshotPromedio).
    Hereda del repositorio base genérico (BaseRepository).
    """
    def __init__(self):
        super().__init__(SnapshotPromedio)

    def get_by_alumno_and_periodo(
        self, db: Session, id_perfil_alumno: str, id_periodo: str
    ) -> Optional[SnapshotPromedio]:
        """
        Recupera el último snapshot de promedio vigente para un alumno en un período determinado.
        
        Ordena por fecha de creación descendente para retornar la última versión calculada
        (por ejemplo, tras una corrección de nota post-cierre).
        """
        return (
            db.query(SnapshotPromedio)
            .filter(
                SnapshotPromedio.id_perfil_alumno == id_perfil_alumno,
                SnapshotPromedio.id_periodo == id_periodo
            )
            .order_by(SnapshotPromedio.created_at.desc())
            .first()
        )

    def get_latest_snapshot(
        self, db: Session, id_perfil_alumno: str
    ) -> Optional[SnapshotPromedio]:
        """
        Recupera el snapshot histórico más reciente del estudiante (el último período cerrado).
        
        Realiza un JOIN con PeriodoAcademico para ordenar por la fecha de fin del período
        y luego por la fecha de creación del snapshot.
        """
        return (
            db.query(SnapshotPromedio)
            .join(PeriodoAcademico, SnapshotPromedio.id_periodo == PeriodoAcademico.id_periodo)
            .filter(SnapshotPromedio.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_fin.desc(), SnapshotPromedio.created_at.desc())
            .first()
        )

class CondicionAcademicaRepository(BaseRepository[CondicionAcademicaAlumno]):
    """
    Repositorio para la gestión de las condiciones académicas (CondicionAcademicaAlumno).
    Hereda del repositorio base genérico (BaseRepository).
    """
    def __init__(self):
        super().__init__(CondicionAcademicaAlumno)

    def get_active_by_alumno(
        self, db: Session, id_perfil_alumno: str
    ) -> List[CondicionAcademicaAlumno]:
        """
        Recupera la lista de todas las condiciones académicas que se encuentran 'ACTIVAS'
        para un estudiante.
        """
        return (
            db.query(CondicionAcademicaAlumno)
            .filter(
                CondicionAcademicaAlumno.id_perfil_alumno == id_perfil_alumno,
                CondicionAcademicaAlumno.estado == "ACTIVA"
            )
            .all()
        )

    def get_active_by_alumno_and_tipo(
        self, db: Session, id_perfil_alumno: str, id_tipo_condicion: str
    ) -> Optional[CondicionAcademicaAlumno]:
        """
        Busca si el alumno tiene una condición académica activa de un tipo específico.
        Permite validar duplicados antes de gatillar una nueva alerta.
        """
        return (
            db.query(CondicionAcademicaAlumno)
            .filter(
                CondicionAcademicaAlumno.id_perfil_alumno == id_perfil_alumno,
                CondicionAcademicaAlumno.id_tipo_condicion == id_tipo_condicion,
                CondicionAcademicaAlumno.estado == "ACTIVA"
            )
            .first()
        )

    def get_all_by_alumno(
        self, db: Session, id_perfil_alumno: str
    ) -> List[CondicionAcademicaAlumno]:
        """
        Recupera el historial completo de condiciones académicas (tanto activas como resueltas)
        de un estudiante, ordenadas por fecha de activación descendente.
        """
        return (
            db.query(CondicionAcademicaAlumno)
            .filter(CondicionAcademicaAlumno.id_perfil_alumno == id_perfil_alumno)
            .order_by(CondicionAcademicaAlumno.fecha_activacion.desc())
            .all()
        )
