from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.core_schemas import Inscripcion, Seccion, Curso, PeriodoAcademico, Matricula, PerfilAlumno
from app.models.cierre import SnapshotPromedio, CondicionAcademicaAlumno

class HistorialRepository:
    """
    Repositorio optimizado para la consolidación de récords académicos e historial del alumno.
    
    Esta clase realiza consultas de solo lectura con JOINs complejos para unificar
    el historial de inscripciones, snapshots de promedios ponderados y condiciones del alumno.
    Decisión de diseño: Al ser una vista agregada y de solo lectura, no cuenta con un modelo
    OR asociativo propio y se agrupa de manera limpia en esta clase.
    """
    
    def get_inscriptions_history(self, db: Session, id_perfil_alumno: str) -> List[tuple]:
        """
        Recupera el historial de asignaturas en las que se ha inscrito el alumno.
        
        Realiza JOINs para traer los detalles del curso, sección y período correspondiente.
        Ordena cronológicamente los resultados por la fecha de inicio del período académico,
        y secundariamente de forma alfabética por el código del curso.
        """
        return (
            db.query(Inscripcion, Seccion, Curso, PeriodoAcademico)
            .join(Matricula, (Inscripcion.id_matricula == Matricula.id_matricula) | (Inscripcion.id_matricula == Matricula.id))
            .join(Seccion, (Inscripcion.id_seccion == Seccion.id_seccion) | (Inscripcion.id_seccion == Seccion.id))
            .join(Curso, (Seccion.id_curso == Curso.id_curso) | (Seccion.id_curso == Curso.id))
            .join(PeriodoAcademico, (Seccion.id_periodo == PeriodoAcademico.id_periodo) | (Seccion.id_periodo == PeriodoAcademico.id))
            .filter(Matricula.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_inicio.asc(), Curso.codigo_curso.asc())
            .all()
        )

    def get_snapshots_history(self, db: Session, id_perfil_alumno: str) -> List[SnapshotPromedio]:
        """
        Recupera el historial de promedios ponderados (PPS/PPA) registrados para el alumno.
        
        La capa de servicios se encargará de realizar el filtrado de versiones intermedias
        (aquellas que tengan un snapshot_posterior referenciándolas) para presentar el récord oficial.
        Ordena cronológicamente los snapshots por fecha de inicio del período.
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
        Recupera el historial completo de condiciones académicas que ha tenido el estudiante.
        
        Realiza un JOIN con PeriodoAcademico para ordenar los resultados cronológicamente
        por período y luego por la fecha específica de activación de la condición.
        """
        return (
            db.query(CondicionAcademicaAlumno)
            .join(PeriodoAcademico, CondicionAcademicaAlumno.id_periodo == PeriodoAcademico.id_periodo)
            .filter(CondicionAcademicaAlumno.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_inicio.asc(), CondicionAcademicaAlumno.fecha_activacion.asc())
            .all()
        )
