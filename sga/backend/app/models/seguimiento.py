import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class CuentaSeguimientoAlumno(Base):
    __tablename__ = "cuenta_seguimiento_alumno"
    
    id_cuenta = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_perfil_alumno = Column(String(36), ForeignKey("perfil_alumno.id_perfil_alumno", ondelete="RESTRICT"), nullable=False)
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    tipo_cuenta = Column(String(40), nullable=False)
    id_periodo_ref = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=True)
    id_curso_ref = Column(String(36), ForeignKey("curso.id_curso", ondelete="RESTRICT"), nullable=True)
    valor_actual = Column(Numeric(10, 2), nullable=False, default=0)
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    perfil_alumno = relationship("PerfilAlumno", backref="cuentas_seguimiento")
    tenant = relationship("Tenant", backref="cuentas_seguimiento")
    periodo_ref = relationship("PeriodoAcademico", backref="cuentas_seguimiento")
    curso_ref = relationship("Curso", backref="cuentas_seguimiento")
    
    __table_args__ = (
        UniqueConstraint("id_perfil_alumno", "tipo_cuenta", "id_periodo_ref", "id_curso_ref", name="uq_cuenta_seguimiento_unique"),
        CheckConstraint(
            "tipo_cuenta IN ("
            "'CTA-DESAPROBACIONES', "
            "'CTA-CREDITOS-APROBADOS', "
            "'CTA-CREDITOS-INSCRITOS', "
            "'CTA-RESERVAS-MATRICULA', "
            "'CTA-CONDICION-ACADEMICA', "
            "'CTA-PROMEDIO-SNAPSHOT'"
            ")", 
            name="chk_cuenta_tipo"
        ),
        CheckConstraint("valor_actual >= 0", name="chk_cuenta_valor"),
    )

class EventoAcademico(Base):
    __tablename__ = "evento_academico"
    
    id_evento = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    id_tipo_evento = Column(String(36), ForeignKey("tipo_evento.id_tipo_evento", ondelete="RESTRICT"), nullable=False)
    id_actor = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="RESTRICT"), nullable=False)
    entidad_afectada_tipo = Column(String(50), nullable=False)
    entidad_afectada_id = Column(String(36), nullable=False)
    fecha_ocurrencia = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valor_anterior = Column(String(1000), nullable=True)  # JSON serialized string
    valor_nuevo = Column(String(1000), nullable=True)     # JSON serialized string
    id_evento_ref = Column(String(36), ForeignKey("evento_academico.id_evento", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    tenant = relationship("Tenant", backref="eventos_academicos")
    tipo_evento = relationship("TipoEvento", backref="eventos_generados")
    actor = relationship("Usuario", backref="eventos_iniciados")
    evento_ref = relationship("EventoAcademico", remote_side=[id_evento], backref="eventos_posteriores")

class RegistroAuditoria(Base):
    __tablename__ = "registro_auditoria"
    
    id_registro = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    id_usuario = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="RESTRICT"), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    tipo_operacion = Column(String(80), nullable=False)
    entidad_afectada_tipo = Column(String(50), nullable=False)
    entidad_afectada_id = Column(String(36), nullable=False)
    resultado = Column(String(15), nullable=False)  # EXITOSA, RECHAZADA
    valor_anterior = Column(String(1000), nullable=True)
    valor_nuevo = Column(String(1000), nullable=True)
    motivo_rechazo = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    tenant = relationship("Tenant", backref="registros_auditoria")
    usuario = relationship("Usuario", backref="registros_auditoria")
    
    __table_args__ = (
        CheckConstraint("resultado IN ('EXITOSA', 'RECHAZADA')", name="chk_auditoria_resultado"),
    )
