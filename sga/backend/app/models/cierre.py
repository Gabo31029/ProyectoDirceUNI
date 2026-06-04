import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class FormulaPromedio(Base):
    __tablename__ = "formula_promedio"

    id_formula = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    tipo_promedio = Column(String(10), nullable=False)   # PPS, PPA
    expresion_calculo = Column(String(500), nullable=False)
    regla_inclusion = Column(String(30), nullable=False)  # TODOS, ULTIMO, SOLO_APROBADOS
    version_formula = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    periodo = relationship("PeriodoAcademico", backref="formulas_promedio")

    __table_args__ = (
        UniqueConstraint("id_periodo", "tipo_promedio", name="uq_formula_periodo_tipo"),
        CheckConstraint("tipo_promedio IN ('PPS', 'PPA')", name="chk_formula_tipo"),
        CheckConstraint("regla_inclusion IN ('TODOS', 'ULTIMO', 'SOLO_APROBADOS')", name="chk_formula_inclusion"),
    )


class SnapshotPromedio(Base):
    __tablename__ = "snapshot_promedio"

    id_snapshot = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_perfil_alumno = Column(String(36), ForeignKey("perfil_alumno.id_perfil_alumno", ondelete="RESTRICT"), nullable=False)
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    pps = Column(Numeric(5, 2), nullable=False)
    ppa = Column(Numeric(5, 2), nullable=False)
    id_formula_aplicada = Column(String(36), ForeignKey("formula_promedio.id_formula", ondelete="RESTRICT"), nullable=True)
    fecha_generacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    id_snapshot_anterior = Column(String(36), ForeignKey("snapshot_promedio.id_snapshot", ondelete="RESTRICT"), nullable=True)
    id_evento_correc = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    perfil_alumno = relationship("PerfilAlumno", backref="snapshots_promedio")
    periodo = relationship("PeriodoAcademico", backref="snapshots_promedio")
    tenant = relationship("Tenant", backref="snapshots_promedio")
    formula_aplicada = relationship("FormulaPromedio", backref="snapshots_generados")
    snapshot_anterior = relationship("SnapshotPromedio", remote_side=[id_snapshot], backref="snapshots_posteriores")

    __table_args__ = (
        UniqueConstraint("id_perfil_alumno", "id_periodo", "id_snapshot_anterior", name="uq_snapshot_alumno_periodo_rec"),
    )


class CondicionAcademicaAlumno(Base):
    __tablename__ = "condicion_academica_alumno"

    id_condicion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_perfil_alumno = Column(String(36), ForeignKey("perfil_alumno.id_perfil_alumno", ondelete="RESTRICT"), nullable=False)
    id_tipo_condicion = Column(String(36), ForeignKey("tipo_condicion_academica.id_tipo_condicion", ondelete="RESTRICT"), nullable=False)
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    id_evento_origen = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=False)
    estado = Column(String(10), nullable=False, default="ACTIVA")  # ACTIVA, RESUELTA
    fecha_activacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)
    observaciones = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    perfil_alumno = relationship("PerfilAlumno", backref="condiciones_academicas")
    tipo_condicion = relationship("TipoCondicionAcademica", backref="alumnos_afectados")
    periodo = relationship("PeriodoAcademico", backref="condiciones_academicas")

    __table_args__ = (
        CheckConstraint("estado IN ('ACTIVA', 'RESUELTA')", name="chk_condicion_estado"),
    )


class PoliticaCondicionAcademica(Base):
    """
    Defines automatic threshold rules that trigger academic conditions during period closure.
    For example: if CTA-DESAPROBACIONES >= 3, activate RIESGO_ACADEMICO.
    """
    __tablename__ = "politica_condicion_academica"

    id_politica_condicion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    id_tipo_condicion = Column(String(36), ForeignKey("tipo_condicion_academica.id_tipo_condicion", ondelete="RESTRICT"), nullable=False)
    cuenta_evaluada = Column(String(50), nullable=False)
    umbral = Column(Numeric(8, 2), nullable=False)
    operador = Column(String(20), nullable=False)  # MAYOR_QUE, MAYOR_IGUAL, IGUAL, MENOR_IGUAL, MENOR_QUE
    accion_resultante = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    periodo = relationship("PeriodoAcademico", backref="politicas_condicion")
    tipo_condicion = relationship("TipoCondicionAcademica", backref="politicas")

    __table_args__ = (
        CheckConstraint(
            "operador IN ('MAYOR_QUE', 'MAYOR_IGUAL', 'IGUAL', 'MENOR_IGUAL', 'MENOR_QUE')",
            name="chk_politica_operador"
        ),
    )
