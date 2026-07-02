import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class FormulaPromedio(Base):
    """
    Define la fórmula matemática y la política de inclusión para el cálculo de promedios de un período.

    Reglas de negocio:
    - Se definen fórmulas específicas para promedios semestrales (PPS) e históricos/acumulados (PPA).
    - Permite configurar diferentes políticas de inclusión de asignaturas (`regla_inclusion`):
        * TODOS: Incluye todas las inscripciones del estudiante en el período (incluso desaprobados).
        * ULTIMO: En caso de múltiples intentos de una asignatura, solo considera el último intento realizado.
        * SOLO_APROBADOS: Solo incluye las asignaturas en estado 'APROBADA'.
    """
    __tablename__ = "formula_promedio"

    id_formula = Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    tipo_promedio = Column(String(10), nullable=False)   # PPS, PPA
    expresion_calculo = Column(String(500), nullable=False)
    regla_inclusion = Column(String(30), nullable=False)  # TODOS, ULTIMO, SOLO_APROBADOS
    version_formula = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relación con el período académico al cual aplica la fórmula
    periodo = relationship("PeriodoAcademico", backref="formulas_promedio")

    __table_args__ = (
        # Unicidad: Solo puede existir una fórmula de PPS y una de PPA por período académico.
        UniqueConstraint("id_periodo", "tipo_promedio", name="uq_formula_periodo_tipo"),
        # Validación de tipos de promedio admitidos.
        CheckConstraint("tipo_promedio IN ('PPS', 'PPA')", name="chk_formula_tipo"),
        # Reglas de selección de asignaturas soportadas.
        CheckConstraint("regla_inclusion IN ('TODOS', 'ULTIMO', 'SOLO_APROBADOS')", name="chk_formula_inclusion"),
    )


class SnapshotPromedio(Base):
    """
    Captura inmutable del promedio ponderado semestral (PPS) y acumulado (PPA)
    de un estudiante al finalizar un período académico o tras una corrección administrativa.

    Reglas de negocio:
    - Los promedios son inmutables una vez generados para garantizar la integridad histórica del récord académico.
    - Si se aprueba una corrección de notas posterior al cierre del período, se genera un nuevo snapshot,
      el cual se encadena al anterior a través de `id_snapshot_anterior`, manteniendo el historial auditable de cambios.
    """
    __tablename__ = "snapshot_promedio"

    id_snapshot = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_perfil_alumno = Column(String(36), ForeignKey("perfil_alumno.id_perfil_alumno", ondelete="RESTRICT"), nullable=False)
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    pps = Column(Numeric(5, 2), nullable=False)
    ppa = Column(Numeric(5, 2), nullable=False)
    id_formula_aplicada = Column(String(36), ForeignKey("formula_promedio.id", ondelete="RESTRICT"), nullable=True)
    fecha_generacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    id_snapshot_anterior = Column(String(36), ForeignKey("snapshot_promedio.id_snapshot", ondelete="RESTRICT"), nullable=True)
    id_evento_correc = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones del snapshot con el estudiante, período académico, inquilino y la fórmula matemática aplicada
    perfil_alumno = relationship("PerfilAlumno", backref="snapshots_promedio")
    periodo = relationship("PeriodoAcademico", backref="snapshots_promedio")
    tenant = relationship("Tenant", backref="snapshots_promedio")
    formula_aplicada = relationship("FormulaPromedio", backref="snapshots_generados")
    snapshot_anterior = relationship("SnapshotPromedio", remote_side=[id_snapshot], backref="snapshots_posteriores")

    __table_args__ = (
        # Unicidad: Asegura el correcto encadenamiento de revisiones de snapshots por alumno y período.
        UniqueConstraint("id_perfil_alumno", "id_periodo", "id_snapshot_anterior", name="uq_snapshot_alumno_periodo_rec"),
    )


class CondicionAcademicaAlumno(Base):
    """
    Registra el estado o condición académica de un estudiante en un determinado período.

    Reglas de negocio:
    - Se gatilla de forma automática mediante la evaluación de políticas de cierre de período.
    - Ejemplos de condiciones: NORMAL, RIESGO_ACADEMICO (por bajo promedio o acumulación de desaprobaciones),
      SUSPENDIDO, RETIRADO_DEFINITIVO.
    - Una condición puede ser resuelta administrativamente o de forma automática cuando el alumno supera el umbral en un período posterior.
    """
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

    # Relaciones con el estudiante, el catálogo de tipos de condición y el período en que se activó
    perfil_alumno = relationship("PerfilAlumno", backref="condiciones_academicas")
    tipo_condicion = relationship("TipoCondicionAcademica", backref="alumnos_afectados")
    periodo = relationship("PeriodoAcademico", backref="condiciones_academicas")

    __table_args__ = (
        # Validación del estado de la condición académica.
        CheckConstraint("estado IN ('ACTIVA', 'RESUELTA')", name="chk_condicion_estado"),
    )


class PoliticaCondicionAcademica(Base):
    """
    Reglas de negocio configurables por período para la activación automática de condiciones académicas.

    Ejemplo de política:
    - Evaluar la cuenta de seguimiento `CTA-DESAPROBACIONES` con operador `MAYOR_IGUAL` y umbral `3`.
    - Si se cumple la condición al cierre del período, se activa la condición correspondiente (e.g. RIESGO_ACADEMICO).
    """
    __tablename__ = "politica_condicion_academica"

    id_politica_condicion = Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    id_tipo_condicion = Column(String(36), ForeignKey("tipo_condicion_academica.id_tipo_condicion", ondelete="RESTRICT"), nullable=False)
    cuenta_evaluada = Column(String(50), nullable=False)
    umbral = Column(Numeric(8, 2), nullable=False)
    operador = Column(String(20), nullable=False)  # MAYOR_QUE, MAYOR_IGUAL, IGUAL, MENOR_IGUAL, MENOR_QUE
    accion_resultante = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relación con el período académico y el tipo de condición académica asociado
    periodo = relationship("PeriodoAcademico", backref="politicas_condicion")
    tipo_condicion = relationship("TipoCondicionAcademica", backref="politicas")

    __table_args__ = (
        # Validación de operadores lógicos permitidos en las reglas de la política.
        CheckConstraint(
            "operador IN ('MAYOR_QUE', 'MAYOR_IGUAL', 'IGUAL', 'MENOR_IGUAL', 'MENOR_QUE')",
            name="chk_politica_operador"
        ),
    )
