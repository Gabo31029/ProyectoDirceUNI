from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.core_schemas import Inscripcion, Seccion, Curso, PeriodoAcademico, Matricula, PerfilAlumno
from app.models.cierre import SnapshotPromedio, CondicionAcademicaAlumno

class HistorialRepository:
    """
    Optimized repository for academic history and records consolidation.
    Provides aggregated queries linking multi-table academic history objects.
    """
    
    def get_inscriptions_history(self, db: Session, id_perfil_alumno: str) -> List[Inscripcion]:
        """
        Retrieves all student inscriptions with course, section, and period details.
        """
        return (
            db.query(Inscripcion)
            .join(Matricula, Inscripcion.id_matricula == Matricula.id_matricula)
            .join(Seccion, Inscripcion.id_seccion == Seccion.id_seccion)
            .join(Curso, Seccion.id_curso == Curso.id_curso)
            .join(PeriodoAcademico, Seccion.id_periodo == PeriodoAcademico.id_periodo)
            .filter(Matricula.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_inicio.asc(), Curso.codigo_curso.asc())
            .all()
        )

    def get_snapshots_history(self, db: Session, id_perfil_alumno: str) -> List[SnapshotPromedio]:
        """
        Retrieves all official snapshots of averages for the student, sorted by period date.
        """
        # We need only the latest version of snapshot for each period (i.e. those that do not have a snapshot_posterior).
        # We can fetch all and keep only the latest in Python, or select them with a SQL subquery.
        # For simplicity and robust auditing, we retrieve all and can display active ones or all versions.
        # The service layer will filter out intermediate snapshots (where id_snapshot is in id_snapshot_anterior).
        return (
            db.query(SnapshotPromedio)
            .join(PeriodoAcademico, SnapshotPromedio.id_periodo == PeriodoAcademico.id_periodo)
            .filter(SnapshotPromedio.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_inicio.asc(), SnapshotPromedio.created_at.asc())
            .all()
        )

    def get_conditions_history(self, db: Session, id_perfil_alumno: str) -> List[CondicionAcademicaAlumno]:
        """
        Retrieves all academic conditions recorded for the student.
        """
        return (
            db.query(CondicionAcademicaAlumno)
            .join(PeriodoAcademico, CondicionAcademicaAlumno.id_periodo == PeriodoAcademico.id_periodo)
            .filter(CondicionAcademicaAlumno.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_inicio.asc(), CondicionAcademicaAlumno.fecha_activacion.asc())
            .all()
        )
