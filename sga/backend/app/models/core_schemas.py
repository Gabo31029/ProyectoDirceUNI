import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Date, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Tenant(Base):
    __tablename__ = "tenants"
    
    id_tenant = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre_institucional = Column(String(200), nullable=False)
    dominio = Column(String(100), unique=True, nullable=False)
    zona_horaria = Column(String(60), nullable=False, default="America/Lima")
    estado = Column(String(10), nullable=False, default="ACTIVO")  # ACTIVO, INACTIVO
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint("estado IN ('ACTIVO', 'INACTIVO')", name="chk_tenant_estado"),
    )

class EscalaEvaluacion(Base):
    __tablename__ = "escala_evaluacion"
    
    id_escala = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    nombre_escala = Column(String(100), nullable=False)
    nota_minima = Column(Numeric(5, 2), nullable=False)
    nota_maxima = Column(Numeric(5, 2), nullable=False)
    nota_aprobatoria = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", name="uq_escala_tenant"),
        CheckConstraint("nota_minima < nota_aprobatoria AND nota_aprobatoria <= nota_maxima", name="chk_escala_notas"),
    )

class TipoEvaluacion(Base):
    __tablename__ = "tipo_evaluacion"
    
    id_tipo_evaluacion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(100), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "codigo", name="uq_tipo_evaluacion_codigo"),
    )

class TipoCondicionAcademica(Base):
    __tablename__ = "tipo_condicion_academica"
    
    id_tipo_condicion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    codigo = Column(String(30), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "codigo", name="uq_tipo_condicion_codigo"),
    )

class TipoEvento(Base):
    __tablename__ = "tipo_evento"
    
    id_tipo_evento = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(150), nullable=False)
    cuenta_objetivo = Column(String(50), nullable=True)
    operacion = Column(String(20), nullable=True)  # INCREMENTO, DECREMENTO, ASIGNACION
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "codigo", name="uq_tipo_evento_codigo"),
        CheckConstraint("operacion IN ('INCREMENTO', 'DECREMENTO', 'ASIGNACION')", name="chk_tipo_evento_operacion"),
    )

class Usuario(Base):
    __tablename__ = "usuario"
    
    id_usuario = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    nombre_completo = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(30), nullable=False)  # ADMINISTRADOR_CENTRAL, ADMINISTRADOR, DOCENTE, ALUMNO
    estado = Column(String(10), nullable=False, default="ACTIVO")  # ACTIVO, INACTIVO
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "email", name="uq_usuario_email"),
        CheckConstraint("rol IN ('ADMINISTRADOR_CENTRAL', 'ADMINISTRADOR', 'DOCENTE', 'ALUMNO')", name="chk_usuario_rol"),
        CheckConstraint("estado IN ('ACTIVO', 'INACTIVO')", name="chk_usuario_estado"),
    )

class PlanEstudios(Base):
    __tablename__ = "plan_estudios"
    
    id_plan_estudios = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    carrera = Column(String(200), nullable=False)
    version_plan = Column(String(20), nullable=False)
    creditos_totales = Column(Integer, nullable=False)
    estado = Column(String(10), nullable=False, default="BORRADOR")  # BORRADOR, ACTIVO
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "carrera", "version_plan", name="uq_plan_estudios_version"),
        CheckConstraint("estado IN ('BORRADOR', 'ACTIVO')", name="chk_plan_estado"),
        CheckConstraint("creditos_totales > 0", name="chk_plan_creditos"),
    )

class PerfilAlumno(Base):
    __tablename__ = "perfil_alumno"
    
    id_perfil_alumno = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="RESTRICT"), unique=True, nullable=False)
    id_plan_estudios = Column(String(36), ForeignKey("plan_estudios.id_plan_estudios", ondelete="RESTRICT"), nullable=False)
    codigo_alumno = Column(String(20), nullable=False)
    carrera = Column(String(200), nullable=False)
    ciclo_actual = Column(Integer, nullable=True)
    periodo_ingreso = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    usuario = relationship("Usuario", backref="perfil_alumno")
    plan_estudios = relationship("PlanEstudios", backref="perfiles_alumno")

class PerfilDocente(Base):
    __tablename__ = "perfil_docente"
    
    id_perfil_docente = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="RESTRICT"), unique=True, nullable=False)
    codigo_docente = Column(String(20), nullable=False)
    especialidad = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    usuario = relationship("Usuario", backref="perfil_docente")

class PeriodoAcademico(Base):
    __tablename__ = "periodo_academico"
    
    id_periodo = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(String(36), unique=True, nullable=True)
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    nombre_periodo = Column(String(20), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False, default="CONFIGURACION")  # CONFIGURACION, MATRICULA, REGISTRO_NOTAS, CERRADO
    fecha_estado_actual = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    id_usuario_transicion = Column(String(36), ForeignKey("usuario.id_usuario", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "nombre_periodo", name="uq_periodo_nombre"),
        CheckConstraint("estado IN ('CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO')", name="chk_periodo_estado"),
        CheckConstraint("fecha_inicio < fecha_fin", name="chk_periodo_fechas"),
    )

class PoliticaTurnoMatricula(Base):
    __tablename__ = "politica_turno_matricula"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="CASCADE"), nullable=False)
    numero_turno = Column(Integer, nullable=False)
    fecha_hora_inicio = Column(DateTime(timezone=True), nullable=False)
    creditos_maximos = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    periodo = relationship("PeriodoAcademico", backref="politicas_turno")
    
    __table_args__ = (
        UniqueConstraint("id_periodo", "numero_turno", name="uq_politica_turno_periodo"),
        CheckConstraint("creditos_maximos > 0", name="chk_politica_turno_creditos"),
    )

class Curso(Base):
    __tablename__ = "curso"
    
    id_curso = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    codigo_curso = Column(String(20), nullable=False)
    nombre_curso = Column(String(200), nullable=False)
    creditos = Column(Integer, nullable=False)
    tipo_curso = Column(String(15), nullable=False)  # OBLIGATORIO, ELECTIVO
    ciclo_sugerido = Column(Integer, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint("id_tenant", "codigo_curso", name="uq_curso_codigo"),
        CheckConstraint("tipo_curso IN ('OBLIGATORIO', 'ELECTIVO')", name="chk_curso_tipo"),
        CheckConstraint("creditos > 0", name="chk_curso_creditos"),
    )

class Seccion(Base):
    __tablename__ = "seccion"
    
    id_seccion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(String(36), unique=True, nullable=True)
    id_tenant = Column(String(36), ForeignKey("tenants.id_tenant", ondelete="RESTRICT"), nullable=False)
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    id_curso = Column(String(36), ForeignKey("curso.id_curso", ondelete="RESTRICT"), nullable=False)
    codigo_seccion = Column(String(10), nullable=False)
    vacantes_maximas = Column(Integer, nullable=False)
    vacantes_disponibles = Column(Integer, nullable=False)
    estado = Column(String(15), nullable=False, default="ABIERTA")  # ABIERTA, CERRADA, SUSPENDIDA
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    curso = relationship("Curso", backref="secciones")
    periodo = relationship("PeriodoAcademico", backref="secciones")
    
    __table_args__ = (
        UniqueConstraint("id_periodo", "id_curso", "codigo_seccion", name="uq_seccion_codigo"),
        CheckConstraint("vacantes_disponibles >= 0", name="chk_seccion_vacantes_disp"),
        CheckConstraint("vacantes_disponibles <= vacantes_maximas", name="chk_seccion_vacantes_max"),
        CheckConstraint("estado IN ('ABIERTA', 'CERRADA', 'SUSPENDIDA')", name="chk_seccion_estado"),
    )

class AsignacionDocenteSeccion(Base):
    __tablename__ = "asignacion_docente_seccion"
    
    id_asignacion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_seccion = Column(String(36), ForeignKey("seccion.id_seccion", ondelete="RESTRICT"), nullable=False)
    id_perfil_docente = Column(String(36), ForeignKey("perfil_docente.id_perfil_docente", ondelete="RESTRICT"), nullable=False)
    id_tipo_evaluacion = Column(String(36), ForeignKey("tipo_evaluacion.id_tipo_evaluacion", ondelete="RESTRICT"), nullable=False)
    es_coordinador = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    seccion = relationship("Seccion", backref="asignaciones_docente")
    perfil_docente = relationship("PerfilDocente", backref="asignaciones_seccion")
    tipo_evaluacion = relationship("TipoEvaluacion", backref="asignaciones_docente")
    
    __table_args__ = (
        UniqueConstraint("id_seccion", "id_perfil_docente", "id_tipo_evaluacion", name="uq_asignacion_docente"),
    )

class Matricula(Base):
    __tablename__ = "matricula"
    
    id_matricula = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_perfil_alumno = Column(String(36), ForeignKey("perfil_alumno.id_perfil_alumno", ondelete="RESTRICT"), nullable=False)
    id_periodo = Column(String(36), ForeignKey("periodo_academico.id_periodo", ondelete="RESTRICT"), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    estado = Column(String(15), nullable=False, default="ACTIVA")  # ACTIVA, RESERVADA, ANULADA
    numero_constancia = Column(String(50), nullable=True)
    numero_turno = Column(Integer, nullable=True, default=1)
    fecha_hora_turno = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    perfil_alumno = relationship("PerfilAlumno", backref="matriculas")
    periodo = relationship("PeriodoAcademico", backref="matriculas")
    
    __table_args__ = (
        UniqueConstraint("id_perfil_alumno", "id_periodo", name="uq_matricula_alumno_periodo"),
        CheckConstraint("estado IN ('ACTIVA', 'RESERVADA', 'ANULADA')", name="chk_matricula_estado"),
    )

class Inscripcion(Base):
    __tablename__ = "inscripcion"
    
    id_inscripcion = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id = Column(String(36), unique=True, nullable=True)
    id_matricula = Column(String(36), ForeignKey("matricula.id_matricula", ondelete="RESTRICT"), nullable=False)
    id_seccion = Column(String(36), ForeignKey("seccion.id_seccion", ondelete="RESTRICT"), nullable=False)
    estado = Column(String(15), nullable=False, default="ACTIVA")  # ACTIVA, RETIRADA, APROBADA, DESAPROBADA, ANULADA
    fecha_inscripcion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_cambio_estado = Column(DateTime(timezone=True), nullable=True)
    nota_final = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    matricula = relationship("Matricula", backref="inscripciones")
    seccion = relationship("Seccion", backref="inscripciones")
    
    __table_args__ = (
        UniqueConstraint("id_matricula", "id_seccion", name="uq_inscripcion_seccion"),
        CheckConstraint("estado IN ('ACTIVA', 'RETIRADA', 'APROBADA', 'DESAPROBADA', 'ANULADA')", name="chk_inscripcion_estado"),
        CheckConstraint("nota_final IS NULL OR (nota_final >= 0 AND nota_final <= 100)", name="chk_inscripcion_nota_final"),
    )
