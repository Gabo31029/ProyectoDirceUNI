import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class EvaluacionAcademica(Base):
    """
    Representa un rubro o criterio de evaluación dentro de una sección académica
    (por ejemplo: Examen Parcial, Prácticas, Trabajo Final).

    Reglas de negocio asociadas:
    - Cada evaluación tiene un peso relativo (%) que define su impacto en la nota final de la sección.
    - La suma de los pesos relativos de todas las evaluaciones de una sección debe sumar exactamente 100%.
    - Estado de flujo del acta:
        * BORRADOR: Permite registrar y modificar calificaciones.
        * PUBLICADO: Las calificaciones son visibles para los alumnos y no son modificables por el docente.
        * CERRADO: Inmutable. Solo se permiten correcciones administrativas aprobadas por un administrador.
    """
    __tablename__ = "evaluacion_academica"
    
    id_evaluacion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_seccion = Column(String(36), ForeignKey("seccion.id_seccion", ondelete="RESTRICT"), nullable=False)
    id_tipo_evaluacion = Column(String(36), ForeignKey("tipo_evaluacion.id_tipo_evaluacion", ondelete="RESTRICT"), nullable=False)
    id_escala = Column(String(36), ForeignKey("escala_evaluacion.id_escala", ondelete="RESTRICT"), nullable=False)
    peso_relativo = Column(Numeric(5, 2), nullable=False)
    orden_presentacion = Column(Integer, nullable=True)
    estado = Column(String(15), nullable=False, default="BORRADOR")  # BORRADOR, PUBLICADO, CERRADO
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones de la evaluación con la sección, el catálogo de tipo de evaluación y la escala de evaluación
    seccion = relationship("Seccion", backref="evaluaciones_academica")
    tipo_evaluacion = relationship("TipoEvaluacion", backref="evaluaciones_academica")
    escala = relationship("EscalaEvaluacion", backref="evaluaciones_academica")
    
    __table_args__ = (
        # Validación de rango: El peso relativo debe estar entre 0% y 100%.
        CheckConstraint("peso_relativo > 0 AND peso_relativo <= 100", name="chk_evaluacion_peso"),
        # Transición de estados permitidos en el flujo de ciclo de vida del acta.
        CheckConstraint("estado IN ('BORRADOR', 'PUBLICADO', 'CERRADO')", name="chk_evaluacion_estado"),
    )

class Calificacion(Base):
    """
    Almacena la calificación obtenida por un estudiante inscrito en una evaluación específica.

    Reglas de negocio asociadas:
    - Existe una sola calificación por cada combinación de inscripción y evaluación.
    - La nota ingresada debe ser mayor o igual a cero (escala no negativa).
    - El estado inicial de la calificación es 'BORRADOR' y se actualiza a 'PUBLICADO' una vez que el
      docente coordinador publica la evaluación asociada.
    """
    __tablename__ = "calificacion"
    
    id_calificacion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_inscripcion = Column(String(36), ForeignKey("inscripcion.id_inscripcion", ondelete="RESTRICT"), nullable=False)
    id_evaluacion = Column(String(36), ForeignKey("evaluacion_academica.id_evaluacion", ondelete="RESTRICT"), nullable=False)
    valor_nota = Column(Numeric(5, 2), nullable=False)
    estado = Column(String(15), nullable=False, default="BORRADOR")  # BORRADOR, PUBLICADO
    fecha_ingreso = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    id_docente_ingreso = Column(String(36), ForeignKey("perfil_docente.id_perfil_docente", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relaciones con la inscripción del estudiante, la evaluación evaluada y el docente que registró la nota
    inscripcion = relationship("Inscripcion", backref="calificaciones")
    evaluacion = relationship("EvaluacionAcademica", backref="calificaciones")
    docente = relationship("PerfilDocente", backref="calificaciones_ingresadas")
    
    __table_args__ = (
        # Unicidad: Impide duplicar calificaciones para un alumno en la misma evaluación.
        UniqueConstraint("id_inscripcion", "id_evaluacion", name="uq_calificacion_inscripcion_evaluacion"),
        # Estados válidos para el registro individual de notas.
        CheckConstraint("estado IN ('BORRADOR', 'PUBLICADO')", name="chk_calificacion_estado"),
        # La calificación no puede ser negativa.
        CheckConstraint("valor_nota >= 0", name="chk_calificacion_nota"),
    )

class CorreccionNota(Base):
    """
    Registro histórico de auditoría e inmutabilidad para correcciones administrativas de notas.

    Reglas de negocio asociadas:
    - Solo aplicable de forma excepcional sobre componentes en estado 'CERRADO'.
    - Requiere la autorización de un administrador (`id_admin_aprobador`) y justificación escrita obligatoria.
    - Almacena las referencias a los eventos académicos (`id_evento_original` e `id_evento_nuevo`)
      para mantener la trazabilidad completa del cambio en la bitácora de auditoría.
    """
    __tablename__ = "correccion_nota"
    
    id_correccion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_calificacion = Column(String(36), ForeignKey("calificacion.id_calificacion", ondelete="RESTRICT"), nullable=False)
    id_evento_original = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=False)
    id_evento_nuevo = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=True)
    valor_anterior = Column(Numeric(5, 2), nullable=False)
    valor_nuevo = Column(Numeric(5, 2), nullable=False)
    justificacion = Column(String(1000), nullable=False)
    id_admin_aprobador = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="RESTRICT"), nullable=False)
    fecha_correccion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relación con la calificación corregida y el administrador que aprobó el cambio
    calificacion = relationship("Calificacion", backref="correcciones")
    admin_aprobador = relationship("Usuario", backref="correcciones_aprobadas")
    
    __table_args__ = (
        # Restricción: La nueva nota corregida no puede ser igual a la anterior.
        CheckConstraint("valor_anterior <> valor_nuevo", name="chk_correccion_valores"),
    )
