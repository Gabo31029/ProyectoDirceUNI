from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class RolUsuario(str, Enum):
    ADMIN_CENTRAL = "ADMIN_CENTRAL"
    ADMIN = "ADMIN"
    DOCENTE = "DOCENTE"
    ALUMNO = "ALUMNO"


class TenantEstado(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    dominio_tenant: str | None = Field(
        default=None,
        description="Dominio del tenant. Obligatorio para usuarios institucionales.",
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    rol: RolUsuario
    tenant_id: str | None = None


class UserPublic(BaseModel):
    id: str
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    nombre: str
    apellido: str
    rol: RolUsuario
    tenant_id: str | None
    activo: bool


class TenantCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=255)
    dominio: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    zona_horaria: str = Field(default="America/Lima", max_length=64)


class TenantUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=255)
    zona_horaria: str | None = Field(default=None, max_length=64)
    estado: TenantEstado | None = None


class TenantResponse(BaseModel):
    id: str
    nombre: str
    dominio: str
    zona_horaria: str
    estado: TenantEstado


class EscalaEvaluacionCreate(BaseModel):
    nombre_escala: str
    nota_minima: float
    nota_maxima: float
    nota_aprobatoria: float


class TipoCatalogoCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None


class TipoEventoCreate(TipoCatalogoCreate):
    cuenta_objetivo: str | None = None
    operacion: str | None = Field(default=None, pattern=r"^(INCREMENTO|DECREMENTO|ASIGNACION)$")


class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    nombre: str = Field(min_length=2, max_length=255)
    apellido: str = Field(min_length=2, max_length=255)
    rol: RolUsuario = Field(default=RolUsuario.ALUMNO)
    # Campos opcionales de perfil para ALUMNO
    codigo_alumno: str | None = None
    id_plan_estudios: UUID | None = None
    periodo_ingreso: str | None = None


class UserUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=255)
    apellido: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8)


class DesactivarUsuarioRequest(BaseModel):
    confirmar: bool = False


class DesactivarUsuarioResponse(BaseModel):
    id: str
    activo: bool
    advertencias: list[str] = Field(default_factory=list)


# --- Periodos Académicos y Políticas ---

class PeriodoEstado(str, Enum):
    CONFIGURACION = "CONFIGURACION"
    MATRICULA = "MATRICULA"
    REGISTRO_NOTAS = "REGISTRO_NOTAS"
    CERRADO = "CERRADO"


class PeriodoAcademicoCreate(BaseModel):
    nombre_periodo: str = Field(min_length=3, max_length=20)
    fecha_inicio: date
    fecha_fin: date


class PeriodoAcademicoResponse(BaseModel):
    id: UUID
    id_tenant: UUID
    nombre_periodo: str
    fecha_inicio: date
    fecha_fin: date
    estado: PeriodoEstado
    fecha_estado_actual: datetime
    id_usuario_transicion: UUID | None
    created_at: datetime
    updated_at: datetime


class PeriodoAcademicoTransition(BaseModel):
    estado_nuevo: PeriodoEstado


class PoliticaCreditoCreate(BaseModel):
    ppa_minimo: Decimal
    ppa_maximo: Decimal
    creditos_maximos: int = Field(gt=0)


class PoliticaCreditoResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    ppa_minimo: Decimal
    ppa_maximo: Decimal
    creditos_maximos: int
    created_at: datetime


class PoliticaTurnoCreate(BaseModel):
    numero_turno: int = Field(gt=0)
    fecha_hora_inicio: datetime
    creditos_maximos: int = Field(gt=0)


class PoliticaTurnoResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    numero_turno: int
    fecha_hora_inicio: datetime
    creditos_maximos: int
    created_at: datetime


class PoliticaCondicionCreate(BaseModel):
    id_tipo_condicion: UUID
    cuenta_evaluada: str
    umbral: Decimal
    operador: str = Field(pattern=r"^(MAYOR_QUE|MAYOR_IGUAL|IGUAL|MENOR_IGUAL|MENOR_QUE)$")
    accion_resultante: str


class PoliticaCondicionResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    id_tipo_condicion: UUID
    cuenta_evaluada: str
    umbral: Decimal
    operador: str
    accion_resultante: str
    created_at: datetime


class PoliticaRetiroCreate(BaseModel):
    tipo_retiro: str
    semana_limite: int = Field(gt=0)
    condiciones_bloqueantes: str | None = None


class PoliticaRetiroResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    tipo_retiro: str
    semana_limite: int
    condiciones_bloqueantes: str | None
    created_at: datetime


class PoliticaReservaCreate(BaseModel):
    max_periodos_consecutivos: int
    max_periodos_alternos: int


class PoliticaReservaResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    max_periodos_consecutivos: int
    max_periodos_alternos: int
    created_at: datetime


class FormulaPromedioCreate(BaseModel):
    tipo_promedio: str = Field(pattern=r"^(PPS|PPA)$")
    expresion_calculo: str
    regla_inclusion: str = Field(pattern=r"^(TODOS|ULTIMO|SOLO_APROBADOS)$")
    version_formula: str


class FormulaPromedioResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    tipo_promedio: str
    expresion_calculo: str
    regla_inclusion: str
    version_formula: str
    created_at: datetime


class PoliticaDispersionCreate(BaseModel):
    ciclos_max_dispersion: int
    prioridad_ciclo_atrasado: bool


class PoliticaDispersionResponse(BaseModel):
    id: UUID
    id_periodo: UUID
    ciclos_max_dispersion: int
    prioridad_ciclo_atrasado: bool
    created_at: datetime


# --- Oferta Académica ---

class PlanEstado(str, Enum):
    BORRADOR = "BORRADOR"
    ACTIVO = "ACTIVO"


class PlanEstudiosCreate(BaseModel):
    carrera: str = Field(min_length=2, max_length=200)
    version_plan: str = Field(min_length=1, max_length=20)
    creditos_totales: int = Field(gt=0)


class PlanEstudiosResponse(BaseModel):
    id: UUID
    id_tenant: UUID
    carrera: str
    version_plan: str
    creditos_totales: int
    estado: PlanEstado
    created_at: datetime
    updated_at: datetime


class CursoEvaluacionConfigItem(BaseModel):
    id_tipo_evaluacion: UUID
    peso: Decimal = Field(gt=0)
    orden: int = 1


class CursoEvaluacionConfigResponse(BaseModel):
    id: UUID
    id_curso: UUID
    id_tipo_evaluacion: UUID
    peso: Decimal
    orden: int
    nombre_tipo_evaluacion: str | None = None
    created_at: datetime


class CursoCreate(BaseModel):
    codigo_curso: str = Field(min_length=2, max_length=20)
    nombre_curso: str = Field(min_length=2, max_length=200)
    creditos: int = Field(gt=0)
    tipo_curso: str = Field(pattern=r"^(OBLIGATORIO|ELECTIVO)$")
    ciclo_sugerido: int | None = None
    prerrequisitos: list[UUID] = []
    evaluaciones_config: list[CursoEvaluacionConfigItem] = []

    @model_validator(mode="after")
    def validar_pesos_suma_100(self) -> "CursoCreate":
        if self.evaluaciones_config:
            total = sum(item.peso for item in self.evaluaciones_config)
            if abs(total - Decimal("100")) > Decimal("0.01"):
                raise ValueError(
                    f"Los pesos de las evaluaciones deben sumar exactamente 100%. Suma actual: {total}%"
                )
        return self


class CursoResponse(BaseModel):
    id: UUID
    id_tenant: UUID
    codigo_curso: str
    nombre_curso: str
    creditos: int
    tipo_curso: str
    ciclo_sugerido: int | None
    activo: bool
    created_at: datetime
    updated_at: datetime
    prerrequisitos: list[UUID] = []
    evaluaciones_config: list[CursoEvaluacionConfigResponse] = []



class CursoAsociarPlan(BaseModel):
    id_curso: UUID
    ciclo_en_plan: int
    es_obligatorio: bool = True


class PrerrequisitoCreate(BaseModel):
    id_curso_requerido: UUID | None = None
    tipo_prereq: str = Field(pattern=r"^(APROBACION_CURSO|MINIMO_CREDITOS)$")
    valor_min_creditos: int | None = None


class PrerrequisitoResponse(BaseModel):
    id: UUID
    id_curso: UUID
    id_curso_requerido: UUID | None
    tipo_prereq: str
    valor_min_creditos: int | None
    created_at: datetime


class SeccionEstado(str, Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"
    SUSPENDIDA = "SUSPENDIDA"


class DocenteAsignacionInput(BaseModel):
    id_usuario_docente: UUID
    id_tipo_evaluacion: UUID
    es_coordinador: bool = False


class SeccionCreate(BaseModel):
    id_periodo: UUID
    id_curso: UUID
    codigo_seccion: str = Field(min_length=1, max_length=10)
    vacantes_maximas: int = Field(gt=0)
    docentes: list[DocenteAsignacionInput] = []


class SeccionResponse(BaseModel):
    id: UUID
    id_tenant: UUID
    id_periodo: UUID
    id_curso: UUID
    codigo_seccion: str
    vacantes_maximas: int
    vacantes_disponibles: int
    estado: SeccionEstado
    created_at: datetime
    updated_at: datetime


class AsignacionDocenteCreate(BaseModel):
    id_usuario_docente: UUID
    id_tipo_evaluacion: UUID
    es_coordinador: bool = False


class AsignacionDocenteResponse(BaseModel):
    id: UUID
    id_seccion: UUID
    id_usuario_docente: UUID
    id_tipo_evaluacion: UUID
    es_coordinador: bool
    created_at: datetime


class EvaluacionEstado(str, Enum):
    BORRADOR = "BORRADOR"
    PUBLICADO = "PUBLICADO"
    CERRADO = "CERRADO"


class EvaluacionAcademicaCreate(BaseModel):
    id_tipo_evaluacion: UUID
    id_escala: UUID
    peso_relativo: Decimal = Field(gt=0, le=100)
    orden_presentacion: int | None = None


class EvaluacionAcademicaResponse(BaseModel):
    id: UUID
    id_seccion: UUID
    id_tipo_evaluacion: UUID
    id_escala: UUID
    peso_relativo: Decimal
    orden_presentacion: int | None
    estado: EvaluacionEstado
    created_at: datetime
    updated_at: datetime


# --- Matricula e Inscripciones (Luis Gabriel Eustaquio Avila) ---


class MatriculaEstado(str, Enum):
    ACTIVA = "ACTIVA"
    RETIRADA = "RETIRADA"
    FINALIZADA = "FINALIZADA"


class InscripcionEstado(str, Enum):
    ACTIVA = "ACTIVA"
    RETIRADA = "RETIRADA"
    APROBADA = "APROBADA"
    DESAPROBADA = "DESAPROBADA"
    ANULADA = "ANULADA"


class MatriculaCreate(BaseModel):
    id_periodo: UUID
    id_alumno: UUID | None = Field(
        default=None,
        description="Solo ADMIN. Si es ALUMNO, se usa el usuario autenticado.",
    )


class MatriculaResponse(BaseModel):
    id: UUID
    id_tenant: UUID
    id_alumno: UUID
    id_periodo: UUID
    estado: MatriculaEstado
    creditos_matriculados: int
    fecha_matricula: datetime
    numero_turno: int | None = None
    fecha_hora_turno: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InscripcionCreate(BaseModel):
    id_seccion: UUID


class InscripcionResponse(BaseModel):
    id: UUID
    id_tenant: UUID
    id_matricula: UUID
    id_seccion: UUID
    id_curso: UUID
    estado: InscripcionEstado
    creditos: int
    fecha_inscripcion: datetime
    fecha_retiro: datetime | None
    created_at: datetime
    updated_at: datetime


class RetiroRequest(BaseModel):
    motivo: str | None = Field(default=None, max_length=500)
