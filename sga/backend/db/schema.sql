-- SGA: Unified Database Schema for PostgreSQL / Supabase
-- Supports both Phase 1 (Raw SQL / asyncpg) and Phase 2/3 (SQLAlchemy / ORM)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- 1. BASE TABLES (PHASE 1 CONVENTIONS)
-- ==========================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    nombre VARCHAR(255) NOT NULL,
    dominio VARCHAR(100) NOT NULL UNIQUE,
    zona_horaria VARCHAR(64) NOT NULL DEFAULT 'America/Lima',
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO'
        CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_dominio ON tenants (dominio);

CREATE TYPE rol_usuario AS ENUM (
    'ADMIN_CENTRAL',
    'ADMIN',
    'DOCENTE',
    'ALUMNO'
);

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID REFERENCES tenants (id),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_usuario_email_por_tenant UNIQUE (id_tenant, email)
);

CREATE INDEX idx_usuarios_tenant ON usuarios (id_tenant);
CREATE INDEX idx_usuarios_email ON usuarios (email);
CREATE UNIQUE INDEX uq_usuario_admin_central_email ON usuarios (email) WHERE id_tenant IS NULL;

-- Catalog tables (Phase 1)
CREATE TABLE cat_escala_evaluacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    nombre_escala VARCHAR(100) NOT NULL,
    nota_minima NUMERIC(5, 2) NOT NULL,
    nota_maxima NUMERIC(5, 2) NOT NULL,
    nota_aprobatoria NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_escala_rango CHECK (
        nota_minima <= nota_aprobatoria AND nota_aprobatoria <= nota_maxima
    )
);

CREATE TABLE cat_tipo_componente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id_tenant, codigo)
);

CREATE TABLE cat_tipo_condicion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id_tenant, codigo)
);

CREATE TABLE cat_tipo_evento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    cuenta_objetivo VARCHAR(100),
    operacion VARCHAR(20) CHECK (operacion IN ('INCREMENTO', 'DECREMENTO', 'ASIGNACION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id_tenant, codigo)
);

CREATE TABLE token_blacklist (
    jti UUID PRIMARY KEY,
    expira_en TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_token_blacklist_expira ON token_blacklist (expira_en);

CREATE TABLE intentos_login (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    id_tenant UUID REFERENCES tenants (id),
    intentos_fallidos INT NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_intentos_login_sin_tenant ON intentos_login (email) WHERE id_tenant IS NULL;
CREATE UNIQUE INDEX uq_intentos_login_con_tenant ON intentos_login (email, id_tenant) WHERE id_tenant IS NOT NULL;

CREATE TABLE auditoria_eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID REFERENCES tenants (id),
    id_usuario UUID REFERENCES usuarios (id),
    tipo_operacion VARCHAR(100) NOT NULL,
    entidad_afectada VARCHAR(100),
    id_entidad UUID,
    valor_anterior JSONB,
    valor_nuevo JSONB,
    motivo_rechazo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auditoria_tenant_fecha ON auditoria_eventos (id_tenant, created_at DESC);

-- ==========================================
-- 2. ACADEMIC PERIODS & OFFER TABLES
-- ==========================================

CREATE TABLE periodo_academico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    nombre_periodo VARCHAR(20) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'CONFIGURACION'
        CHECK (estado IN ('CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO')),
    fecha_estado_actual TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    id_usuario_transicion UUID REFERENCES usuarios (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_periodo_nombre_por_tenant UNIQUE (id_tenant, nombre_periodo),
    CONSTRAINT chk_periodo_fechas CHECK (fecha_inicio < fecha_fin)
);

CREATE UNIQUE INDEX uq_periodo_activo_por_tenant ON periodo_academico (id_tenant)
WHERE estado IN ('MATRICULA', 'REGISTRO_NOTAS');

CREATE TABLE politica_credito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    ppa_minimo NUMERIC(5, 2) NOT NULL,
    ppa_maximo NUMERIC(5, 2) NOT NULL,
    creditos_maximos SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_politica_credito_ppa CHECK (ppa_minimo < ppa_maximo),
    CONSTRAINT chk_politica_credito_max CHECK (creditos_maximos > 0)
);

CREATE TABLE politica_condicion_academica (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    id_tipo_condicion UUID NOT NULL REFERENCES cat_tipo_condicion (id) ON DELETE RESTRICT,
    cuenta_evaluada VARCHAR(50) NOT NULL,
    umbral NUMERIC(8, 2) NOT NULL,
    operador VARCHAR(20) NOT NULL
        CHECK (operador IN ('MAYOR_QUE', 'MAYOR_IGUAL', 'IGUAL', 'MENOR_IGUAL', 'MENOR_QUE')),
    accion_resultante VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_politica_condicion_periodo UNIQUE (id_periodo, id_tipo_condicion)
);

CREATE TABLE politica_retiro (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    tipo_retiro VARCHAR(50) NOT NULL,
    semana_limite SMALLINT NOT NULL CHECK (semana_limite > 0),
    condiciones_bloqueantes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE politica_reserva (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL UNIQUE REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    max_periodos_consecutivos SMALLINT NOT NULL,
    max_periodos_alternos SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE formula_promedio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    tipo_promedio VARCHAR(10) NOT NULL CHECK (tipo_promedio IN ('PPS', 'PPA')),
    expresion_calculo TEXT NOT NULL,
    regla_inclusion VARCHAR(30) NOT NULL
        CHECK (regla_inclusion IN ('TODOS', 'ULTIMO', 'SOLO_APROBADOS')),
    version_formula VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_formula_promedio_periodo UNIQUE (id_periodo, tipo_promedio)
);

CREATE TABLE politica_dispersion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL UNIQUE REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    ciclos_max_dispersion SMALLINT NOT NULL,
    prioridad_ciclo_atrasado BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE plan_estudios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_plan_estudios UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    carrera VARCHAR(200) NOT NULL,
    version_plan VARCHAR(20) NOT NULL,
    creditos_totales SMALLINT NOT NULL CHECK (creditos_totales > 0),
    estado VARCHAR(10) NOT NULL DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'ACTIVO')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plan_estudios_version UNIQUE (id_tenant, carrera, version_plan)
);

CREATE TABLE curso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_curso UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    codigo_curso VARCHAR(20) NOT NULL,
    nombre_curso VARCHAR(200) NOT NULL,
    creditos SMALLINT NOT NULL CHECK (creditos > 0),
    tipo_curso VARCHAR(15) NOT NULL
        CHECK (tipo_curso IN ('OBLIGATORIO', 'ELECTIVO')),
    ciclo_sugerido SMALLINT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_curso_codigo UNIQUE (id_tenant, codigo_curso)
);

CREATE TABLE plan_estudios_curso (
    id_plan_estudios UUID NOT NULL REFERENCES plan_estudios (id) ON DELETE RESTRICT,
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
    ciclo_en_plan SMALLINT NOT NULL,
    es_obligatorio BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id_plan_estudios, id_curso)
);

CREATE TABLE prerrequisito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
    id_curso_requerido UUID REFERENCES curso (id) ON DELETE RESTRICT,
    tipo_prereq VARCHAR(20) NOT NULL
        CHECK (tipo_prereq IN ('APROBACION_CURSO', 'MINIMO_CREDITOS')),
    valor_min_creditos SMALLINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_prerrequisito_auto Check (id_curso <> id_curso_requerido),
    CONSTRAINT chk_prerrequisito_campos CHECK (
        (tipo_prereq = 'APROBACION_CURSO' AND id_curso_requerido IS NOT NULL) OR
        (tipo_prereq = 'MINIMO_CREDITOS' AND valor_min_creditos IS NOT NULL)
    )
);

CREATE TABLE seccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_seccion UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
    codigo_seccion VARCHAR(10) NOT NULL,
    vacantes_maximas SMALLINT NOT NULL,
    vacantes_disponibles SMALLINT NOT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'ABIERTA'
        CHECK (estado IN ('ABIERTA', 'CERRADA', 'SUSPENDIDA')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_seccion_codigo UNIQUE (id_periodo, id_curso, codigo_seccion),
    CONSTRAINT chk_seccion_vacantes_disp CHECK (vacantes_disponibles >= 0),
    CONSTRAINT chk_seccion_vacantes_max CHECK (vacantes_disponibles <= vacantes_maximas)
);

CREATE TABLE asignacion_docente_seccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_asignacion UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_usuario_docente UUID NOT NULL REFERENCES usuarios (id) ON DELETE RESTRICT,
    id_tipo_componente UUID NOT NULL REFERENCES cat_tipo_componente (id) ON DELETE RESTRICT,
    es_coordinador BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_asignacion_docente_componente UNIQUE (id_seccion, id_usuario_docente, id_tipo_componente)
);

CREATE TABLE componente_evaluacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_componente UUID UNIQUE DEFAULT gen_random_uuid(), -- SQLAlchemy compatibility
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_tipo_componente UUID NOT NULL REFERENCES cat_tipo_componente (id) ON DELETE RESTRICT,
    id_escala UUID NOT NULL REFERENCES cat_escala_evaluacion (id) ON DELETE RESTRICT,
    peso_relativo NUMERIC(5, 2) NOT NULL CHECK (peso_relativo > 0 AND peso_relativo <= 100),
    orden_presentacion SMALLINT,
    estado VARCHAR(15) NOT NULL DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'PUBLICADO', 'CERRADO')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 3. ID SYNCHRONIZATION TRIGGERS
-- ==========================================

CREATE OR REPLACE FUNCTION sync_ids()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'tenants' THEN
        IF NEW.id_tenant IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_tenant := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_tenant IS NOT NULL THEN
            NEW.id := NEW.id_tenant;
        END IF;
    ELSIF TG_TABLE_NAME = 'periodo_academico' THEN
        IF NEW.id_periodo IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_periodo := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_periodo IS NOT NULL THEN
            NEW.id := NEW.id_periodo;
        END IF;
    ELSIF TG_TABLE_NAME = 'plan_estudios' THEN
        IF NEW.id_plan_estudios IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_plan_estudios := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_plan_estudios IS NOT NULL THEN
            NEW.id := NEW.id_plan_estudios;
        END IF;
    ELSIF TG_TABLE_NAME = 'curso' THEN
        IF NEW.id_curso IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_curso := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_curso IS NOT NULL THEN
            NEW.id := NEW.id_curso;
        END IF;
    ELSIF TG_TABLE_NAME = 'seccion' THEN
        IF NEW.id_seccion IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_seccion := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_seccion IS NOT NULL THEN
            NEW.id := NEW.id_seccion;
        END IF;
    ELSIF TG_TABLE_NAME = 'componente_evaluacion' THEN
        IF NEW.id_componente IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_componente := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_componente IS NOT NULL THEN
            NEW.id := NEW.id_componente;
        END IF;
    ELSIF TG_TABLE_NAME = 'asignacion_docente_seccion' THEN
        IF NEW.id_asignacion IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_asignacion := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_asignacion IS NOT NULL THEN
            NEW.id := NEW.id_asignacion;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_tenants BEFORE INSERT OR UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_periodo BEFORE INSERT OR UPDATE ON periodo_academico FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_plan_estudios BEFORE INSERT OR UPDATE ON plan_estudios FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_curso BEFORE INSERT OR UPDATE ON curso FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_seccion BEFORE INSERT OR UPDATE ON seccion FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_componente BEFORE INSERT OR UPDATE ON componente_evaluacion FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_asignacion BEFORE INSERT OR UPDATE ON asignacion_docente_seccion FOR EACH ROW EXECUTE FUNCTION sync_ids();

-- ==========================================
-- 4. ALCHEMY COMPATIBILITY SCHEMA (PHASE 2/3)
-- ==========================================

CREATE TABLE usuario (
    id_usuario UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    nombre_completo VARCHAR(200) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('ADMINISTRADOR_CENTRAL', 'ADMINISTRADOR', 'DOCENTE', 'ALUMNO')),
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_usuario_email UNIQUE (id_tenant, email)
);

CREATE TABLE escala_evaluacion (
    id_escala UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    nombre_escala VARCHAR(100) NOT NULL,
    nota_minima NUMERIC(5, 2) NOT NULL,
    nota_maxima NUMERIC(5, 2) NOT NULL,
    nota_aprobatoria NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_escala_tenant UNIQUE (id_tenant),
    CONSTRAINT chk_escala_notas CHECK (nota_minima < nota_aprobatoria AND nota_aprobatoria <= nota_maxima)
);

CREATE TABLE tipo_componente (
    id_tipo_componente UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_componente_codigo UNIQUE (id_tenant, codigo)
);

CREATE TABLE tipo_condicion_academica (
    id_tipo_condicion UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_condicion_codigo UNIQUE (id_tenant, codigo)
);

CREATE TABLE tipo_evento (
    id_tipo_evento UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    cuenta_objetivo VARCHAR(50) NOT NULL,
    operacion VARCHAR(20) NOT NULL CHECK (operacion IN ('INCREMENTO', 'DECREMENTO', 'ASIGNACION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_evento_codigo UNIQUE (id_tenant, codigo)
);

CREATE TABLE perfil_alumno (
    id_perfil_alumno UUID PRIMARY KEY,
    id_usuario UUID NOT NULL UNIQUE REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    id_plan_estudios UUID NOT NULL REFERENCES plan_estudios (id_plan_estudios) ON DELETE RESTRICT,
    codigo_alumno VARCHAR(20) NOT NULL,
    carrera VARCHAR(200) NOT NULL,
    ciclo_actual INTEGER,
    periodo_ingreso VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE perfil_docente (
    id_perfil_docente UUID PRIMARY KEY,
    id_usuario UUID NOT NULL UNIQUE REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    codigo_docente VARCHAR(20) NOT NULL,
    especialidad VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE matricula (
    id_matricula UUID PRIMARY KEY,
    id_perfil_alumno UUID NOT NULL REFERENCES perfil_alumno (id_perfil_alumno) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id_periodo) ON DELETE RESTRICT,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'RESERVADA', 'ANULADA')),
    numero_constancia VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_matricula_alumno_periodo UNIQUE (id_perfil_alumno, id_periodo)
);

CREATE TABLE inscripcion (
    id_inscripcion UUID PRIMARY KEY,
    id_matricula UUID NOT NULL REFERENCES matricula (id_matricula) ON DELETE RESTRICT,
    id_seccion UUID NOT NULL REFERENCES seccion (id_seccion) ON DELETE RESTRICT,
    estado VARCHAR(15) NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'RETIRADA', 'APROBADA', 'DESAPROBADA', 'ANULADA')),
    fecha_inscripcion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_cambio_estado TIMESTAMPTZ,
    nota_final NUMERIC(5, 2) CHECK (nota_final IS NULL OR (nota_final >= 0 AND nota_final <= 100)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inscripcion_seccion UNIQUE (id_matricula, id_seccion)
);

CREATE TABLE calificacion (
    id_calificacion UUID PRIMARY KEY,
    id_inscripcion UUID NOT NULL REFERENCES inscripcion (id_inscripcion) ON DELETE RESTRICT,
    id_componente UUID NOT NULL REFERENCES componente_evaluacion (id_componente) ON DELETE RESTRICT,
    valor_nota NUMERIC(5, 2) NOT NULL CHECK (valor_nota >= 0),
    estado VARCHAR(15) NOT NULL DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR', 'PUBLICADO')),
    fecha_ingreso TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    id_docente_ingreso UUID NOT NULL REFERENCES perfil_docente (id_perfil_docente) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_calificacion_inscripcion_componente UNIQUE (id_inscripcion, id_componente)
);

CREATE TABLE cuenta_seguimiento_alumno (
    id_cuenta UUID PRIMARY KEY,
    id_perfil_alumno UUID NOT NULL REFERENCES perfil_alumno (id_perfil_alumno) ON DELETE RESTRICT,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    tipo_cuenta VARCHAR(40) NOT NULL CHECK (tipo_cuenta IN ('CTA-DESAPROBACIONES', 'CTA-CREDITOS-APROBADOS', 'CTA-CREDITOS-INSCRITOS', 'CTA-RESERVAS-MATRICULA', 'CTA-CONDICION-ACADEMICA', 'CTA-PROMEDIO-SNAPSHOT')),
    id_periodo_ref UUID REFERENCES periodo_academico (id_periodo) ON DELETE RESTRICT,
    id_curso_ref UUID REFERENCES curso (id_curso) ON DELETE RESTRICT,
    valor_actual NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (valor_actual >= 0),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cuenta_seguimiento_unique UNIQUE (id_perfil_alumno, tipo_cuenta, id_periodo_ref, id_curso_ref)
);

CREATE TABLE evento_academico (
    id_evento UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    id_tipo_evento UUID NOT NULL REFERENCES tipo_evento (id_tipo_evento) ON DELETE RESTRICT,
    id_actor UUID NOT NULL REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    entidad_afectada_tipo VARCHAR(50) NOT NULL,
    entidad_afectada_id UUID NOT NULL,
    fecha_ocurrencia TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valor_anterior VARCHAR(1000),
    valor_nuevo VARCHAR(1000),
    id_evento_ref UUID REFERENCES evento_academico (id_evento) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE correccion_nota (
    id_correccion UUID PRIMARY KEY,
    id_calificacion UUID NOT NULL REFERENCES calificacion (id_calificacion) ON DELETE RESTRICT,
    id_evento_original UUID NOT NULL REFERENCES evento_academico (id_evento) ON DELETE RESTRICT,
    id_evento_nuevo UUID REFERENCES evento_academico (id_evento) ON DELETE RESTRICT,
    valor_anterior NUMERIC(5, 2) NOT NULL,
    valor_nuevo NUMERIC(5, 2) NOT NULL,
    justificacion VARCHAR(1000) NOT NULL,
    id_admin_aprobador UUID NOT NULL REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    fecha_correccion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_correccion_valores CHECK (valor_anterior <> valor_nuevo)
);

CREATE TABLE snapshot_promedio (
    id_snapshot UUID PRIMARY KEY,
    id_perfil_alumno UUID NOT NULL REFERENCES perfil_alumno (id_perfil_alumno) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id_periodo) ON DELETE RESTRICT,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    pps NUMERIC(5, 2) NOT NULL,
    ppa NUMERIC(5, 2) NOT NULL,
    id_formula_aplicada UUID REFERENCES formula_promedio (id) ON DELETE RESTRICT,
    fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    id_snapshot_anterior UUID REFERENCES snapshot_promedio (id_snapshot) ON DELETE RESTRICT,
    id_evento_correc UUID REFERENCES evento_academico (id_evento) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_snapshot_alumno_periodo_rec UNIQUE (id_perfil_alumno, id_periodo, id_snapshot_anterior)
);

CREATE TABLE condicion_academica_alumno (
    id_condicion UUID PRIMARY KEY,
    id_perfil_alumno UUID NOT NULL REFERENCES perfil_alumno (id_perfil_alumno) ON DELETE RESTRICT,
    id_tipo_condicion UUID NOT NULL REFERENCES tipo_condicion_academica (id_tipo_condicion) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id_periodo) ON DELETE RESTRICT,
    id_evento_origen UUID NOT NULL REFERENCES evento_academico (id_evento) ON DELETE RESTRICT,
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'RESUELTA')),
    fecha_activacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_resolucion TIMESTAMPTZ,
    observaciones VARCHAR(1000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE registro_auditoria (
    id_registro UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    id_usuario UUID NOT NULL REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tipo_operacion VARCHAR(80) NOT NULL,
    entidad_afectada_tipo VARCHAR(50) NOT NULL,
    entidad_afectada_id UUID NOT NULL,
    resultado VARCHAR(15) NOT NULL CHECK (resultado IN ('EXITOSA', 'RECHAZADA')),
    valor_anterior VARCHAR(1000),
    valor_nuevo VARCHAR(1000),
    motivo_rechazo VARCHAR(1000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 5. INITIAL SEED DATA
-- ==========================================

INSERT INTO tenants (id, id_tenant, nombre, dominio, zona_horaria)
VALUES (
    'a1111111-1111-1111-1111-111111111111',
    'a1111111-1111-1111-1111-111111111111',
    'Universidad Demo',
    'uni-demo',
    'America/Lima'
);


-- SGA Fase 1: Turnos de Matrícula (Dair Ramos)
-- Responsable: editar solo este archivo para turnos de matrícula.

CREATE TABLE politica_turno_matricula (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    numero_turno INT NOT NULL,
    fecha_hora_inicio TIMESTAMPTZ NOT NULL,
    creditos_maximos INT NOT NULL CHECK (creditos_maximos > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_politica_turno_periodo UNIQUE (id_periodo, numero_turno)
);

ALTER TABLE matricula 
ADD COLUMN numero_turno INT DEFAULT 1,
ADD COLUMN fecha_hora_turno TIMESTAMPTZ;
