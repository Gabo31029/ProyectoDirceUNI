import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class ComponenteEvaluacion(Base):
    __tablename__ = "componente_evaluacion"
    
    id_componente = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_seccion = Column(String(36), ForeignKey("seccion.id_seccion", ondelete="RESTRICT"), nullable=False)
    id_tipo_componente = Column(String(36), ForeignKey("tipo_componente.id_tipo_componente", ondelete="RESTRICT"), nullable=False)
    id_escala = Column(String(36), ForeignKey("escala_evaluacion.id_escala", ondelete="RESTRICT"), nullable=False)
    peso_relativo = Column(Numeric(5, 2), nullable=False)
    orden_presentacion = Column(Integer, nullable=True)
    estado = Column(String(15), nullable=False, default="BORRADOR")  # BORRADOR, PUBLICADO, CERRADO
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    seccion = relationship("Seccion", backref="componentes_evaluacion")
    tipo_componente = relationship("TipoComponente", backref="componentes_evaluacion")
    escala = relationship("EscalaEvaluacion", backref="componentes_evaluacion")
    
    __table_args__ = (
        CheckConstraint("peso_relativo > 0 AND peso_relativo <= 100", name="chk_componente_peso"),
        CheckConstraint("estado IN ('BORRADOR', 'PUBLICADO', 'CERRADO')", name="chk_componente_estado"),
    )

class Calificacion(Base):
    __tablename__ = "calificacion"
    
    id_calificacion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_inscripcion = Column(String(36), ForeignKey("inscripcion.id_inscripcion", ondelete="RESTRICT"), nullable=False)
    id_componente = Column(String(36), ForeignKey("componente_evaluacion.id_componente", ondelete="RESTRICT"), nullable=False)
    valor_nota = Column(Numeric(5, 2), nullable=False)
    estado = Column(String(15), nullable=False, default="BORRADOR")  # BORRADOR, PUBLICADO
    fecha_ingreso = Column(DateTime(timezone=True), default=datetime.utcnow)
    id_docente_ingreso = Column(String(36), ForeignKey("perfil_docente.id_perfil_docente", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inscripcion = relationship("Inscripcion", backref="calificaciones")
    componente = relationship("ComponenteEvaluacion", backref="calificaciones")
    docente = relationship("PerfilDocente", backref="calificaciones_ingresadas")
    
    __table_args__ = (
        UniqueConstraint("id_inscripcion", "id_componente", name="uq_calificacion_inscripcion_componente"),
        CheckConstraint("estado IN ('BORRADOR', 'PUBLICADO')", name="chk_calificacion_estado"),
        CheckConstraint("valor_nota >= 0", name="chk_calificacion_nota"),
    )

class CorreccionNota(Base):
    __tablename__ = "correccion_nota"
    
    id_correccion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_calificacion = Column(String(36), ForeignKey("calificacion.id_calificacion", ondelete="RESTRICT"), nullable=False)
    id_evento_original = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=False)
    id_evento_nuevo = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=True)
    valor_anterior = Column(Numeric(5, 2), nullable=False)
    valor_nuevo = Column(Numeric(5, 2), nullable=False)
    justificacion = Column(String(1000), nullable=False)
    id_admin_aprobador = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="RESTRICT"), nullable=False)
    fecha_correccion = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    calificacion = relationship("Calificacion", backref="correcciones")
    admin_aprobador = relationship("Usuario", backref="correcciones_aprobadas")
    
    __table_args__ = (
        CheckConstraint("valor_anterior <> valor_nuevo", name="chk_correccion_valores"),
    )
