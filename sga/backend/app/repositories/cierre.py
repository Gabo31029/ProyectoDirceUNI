from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.cierre import FormulaPromedio, SnapshotPromedio, CondicionAcademicaAlumno
from app.models.core_schemas import PeriodoAcademico

class FormulaPromedioRepository(BaseRepository[FormulaPromedio]):
    def __init__(self):
        super().__init__(FormulaPromedio)

    def get_by_periodo_and_tipo(
        self, db: Session, id_periodo: str, tipo_promedio: str
    ) -> Optional[FormulaPromedio]:
        return (
            db.query(FormulaPromedio)
            .filter(
                FormulaPromedio.id_periodo == id_periodo,
                FormulaPromedio.tipo_promedio == tipo_promedio
            )
            .first()
        )

class SnapshotPromedioRepository(BaseRepository[SnapshotPromedio]):
    def __init__(self):
        super().__init__(SnapshotPromedio)

    def get_by_alumno_and_periodo(
        self, db: Session, id_perfil_alumno: str, id_periodo: str
    ) -> Optional[SnapshotPromedio]:
        # Return the latest active snapshot (without snapshot_posterior referencing it)
        # to allow recalculations to be linked in a chain.
        # So we look for a snapshot where id_snapshot is NOT present in any other snapshot's id_snapshot_anterior.
        # But for simpler retrieval, we can order by created_at DESC and take the first.
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
        Gets the student's latest snapshot average historically.
        """
        return (
            db.query(SnapshotPromedio)
            .join(PeriodoAcademico, SnapshotPromedio.id_periodo == PeriodoAcademico.id_periodo)
            .filter(SnapshotPromedio.id_perfil_alumno == id_perfil_alumno)
            .order_by(PeriodoAcademico.fecha_fin.desc(), SnapshotPromedio.created_at.desc())
            .first()
        )

class CondicionAcademicaRepository(BaseRepository[CondicionAcademicaAlumno]):
    def __init__(self):
        super().__init__(CondicionAcademicaAlumno)

    def get_active_by_alumno(
        self, db: Session, id_perfil_alumno: str
    ) -> List[CondicionAcademicaAlumno]:
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
        return (
            db.query(CondicionAcademicaAlumno)
            .filter(CondicionAcademicaAlumno.id_perfil_alumno == id_perfil_alumno)
            .order_by(CondicionAcademicaAlumno.fecha_activacion.desc())
            .all()
        )
