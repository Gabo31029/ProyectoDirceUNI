-- SGA Database Schema (Unified for Phase 2/3: Cierre and Matricula)

-- ==========================================
-- 1. BASE TABLES (PHASE 1)
-- ==========================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID UNIQUE, -- synced with id via trigger
    nombre VARCHAR(255) NOT NULL,
    dominio VARCHAR(100) NOT NULL UNIQUE,
    zona_horaria VARCHAR(64) NOT NULL DEFAULT 'America/Lima',
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_usuario UUID UNIQUE, -- synced with id via trigger
    id_tenant UUID REFERENCES tenants (id) ON DELETE RESTRICT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('ADMIN_CENTRAL', 'ADMIN', 'DOCENTE', 'ALUMNO')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_usuarios_tenant_email UNIQUE (id_tenant, email)
);

CREATE TABLE cat_escala_evaluacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_escala UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    nombre_escala VARCHAR(100) NOT NULL,
    nota_minima NUMERIC(5, 2) NOT NULL,
    nota_maxima NUMERIC(5, 2) NOT NULL,
    nota_aprobatoria NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cat_escala_tenant UNIQUE (id_tenant)
);

CREATE TABLE cat_tipo_componente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tipo_componente UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cat_tipo_comp_tenant_cod UNIQUE (id_tenant, codigo)
);

CREATE TABLE cat_tipo_condicion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tipo_condicion UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cat_tipo_cond_tenant_cod UNIQUE (id_tenant, codigo)
);

CREATE TABLE cat_tipo_evento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tipo_evento UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    cuenta_objetivo VARCHAR(50) NOT NULL,
    operacion VARCHAR(20) NOT NULL CHECK (operacion IN ('INCREMENTO', 'DECREMENTO', 'ASIGNACION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cat_tipo_event_tenant_cod UNIQUE (id_tenant, codigo)
);

CREATE TABLE token_blacklist (
    jti VARCHAR(255) PRIMARY KEY,
    expira_en TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE intentos_login (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    id_tenant UUID REFERENCES tenants (id) ON DELETE CASCADE,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_intentos_login UNIQUE (email, id_tenant)
);

CREATE TABLE auditoria_eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID REFERENCES tenants (id) ON DELETE RESTRICT,
    id_usuario UUID REFERENCES usuarios (id) ON DELETE SET NULL,
    tipo_operacion VARCHAR(100) NOT NULL,
    entidad_afectada VARCHAR(100),
    id_entidad UUID,
    valor_anterior JSONB,
    valor_nuevo JSONB,
    motivo_rechazo VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE periodo_academico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    nombre_periodo VARCHAR(50) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'CONFIGURACION' 
        CHECK (estado IN ('CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO')),
    fecha_estado_actual TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    id_usuario_transicion UUID REFERENCES usuarios (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_periodo_tenant_nombre UNIQUE (id_tenant, nombre_periodo),
    CONSTRAINT chk_periodo_fechas CHECK (fecha_inicio < fecha_fin)
);

CREATE TABLE politica_credito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    ppa_minimo NUMERIC(5, 2) NOT NULL,
    ppa_maximo NUMERIC(5, 2) NOT NULL,
    creditos_maximos INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_politica_cred_ppa CHECK (ppa_minimo <= ppa_maximo)
);

CREATE TABLE politica_condicion_academica (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    id_tipo_condicion UUID NOT NULL REFERENCES cat_tipo_condicion (id) ON DELETE RESTRICT,
    cuenta_evaluada VARCHAR(50) NOT NULL,
    umbral NUMERIC(10, 2) NOT NULL,
    operador VARCHAR(20) NOT NULL CHECK (operador IN ('MAYOR_QUE', 'MAYOR_IGUAL', 'IGUAL', 'MENOR_IGUAL', 'MENOR_QUE')),
    accion_resultante VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE politica_retiro (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    tipo_retiro VARCHAR(50) NOT NULL,
    semana_limite INTEGER NOT NULL,
    condiciones_bloqueantes VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE politica_reserva (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    max_periodos_consecutivos INTEGER NOT NULL,
    max_periodos_alternos INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE formula_promedio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    tipo_promedio VARCHAR(10) NOT NULL CHECK (tipo_promedio IN ('PPS', 'PPA')),
    expresion_calculo VARCHAR(500) NOT NULL,
    regla_inclusion VARCHAR(20) NOT NULL CHECK (regla_inclusion IN ('TODOS', 'ULTIMO', 'SOLO_APROBADOS')),
    version_formula VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE politica_dispersion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE CASCADE,
    ciclos_max_dispersion INTEGER NOT NULL,
    prioridad_ciclo_atrasado BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE plan_estudios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_plan_estudios UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    carrera VARCHAR(200) NOT NULL,
    version_plan VARCHAR(20) NOT NULL,
    creditos_totales INTEGER NOT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR', 'ACTIVO')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plan_estudios_carrera_ver UNIQUE (id_tenant, carrera, version_plan)
);

CREATE TABLE curso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_curso UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    codigo_curso VARCHAR(20) NOT NULL,
    nombre_curso VARCHAR(200) NOT NULL,
    creditos INTEGER NOT NULL,
    tipo_curso VARCHAR(15) NOT NULL CHECK (tipo_curso IN ('OBLIGATORIO', 'ELECTIVO')),
    ciclo_sugerido INTEGER,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_curso_tenant_codigo UNIQUE (id_tenant, codigo_curso)
);

CREATE TABLE plan_estudios_curso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_plan_estudios UUID NOT NULL REFERENCES plan_estudios (id) ON DELETE RESTRICT,
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
    ciclo_en_plan INTEGER NOT NULL,
    es_obligatorio BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plan_curso UNIQUE (id_plan_estudios, id_curso)
);

CREATE TABLE prerrequisito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE CASCADE,
    id_curso_requerido UUID REFERENCES curso (id) ON DELETE RESTRICT,
    tipo_prereq VARCHAR(20) NOT NULL CHECK (tipo_prereq IN ('APROBACION_CURSO', 'MINIMO_CREDITOS')),
    valor_min_creditos INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_prereq_coherencia CHECK (
        (tipo_prereq = 'APROBACION_CURSO' AND id_curso_requerido IS NOT NULL) OR
        (tipo_prereq = 'MINIMO_CREDITOS' AND valor_min_creditos IS NOT NULL)
    )
);

CREATE TABLE seccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_seccion UUID UNIQUE,
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
    codigo_seccion VARCHAR(10) NOT NULL,
    vacantes_maximas INTEGER NOT NULL,
    vacantes_disponibles INTEGER NOT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'ABIERTA' CHECK (estado IN ('ABIERTA', 'CERRADA', 'SUSPENDIDA')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_seccion_periodo_curso_cod UNIQUE (id_periodo, id_curso, codigo_seccion),
    CONSTRAINT chk_seccion_vacantes CHECK (vacantes_maximas > 0),
    CONSTRAINT chk_seccion_vacantes_max CHECK (vacantes_disponibles <= vacantes_maximas)
);

CREATE TABLE asignacion_docente_seccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_asignacion UUID UNIQUE,
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_usuario_docente UUID NOT NULL REFERENCES usuarios (id) ON DELETE RESTRICT,
    id_tipo_componente UUID NOT NULL REFERENCES cat_tipo_componente (id) ON DELETE RESTRICT,
    es_coordinador BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_asignacion_docente UNIQUE (id_seccion, id_usuario_docente, id_tipo_componente)
);

CREATE TABLE componente_evaluacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_componente UUID UNIQUE,
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_tipo_componente UUID NOT NULL REFERENCES cat_tipo_componente (id) ON DELETE RESTRICT,
    id_escala UUID NOT NULL REFERENCES cat_escala_evaluacion (id) ON DELETE RESTRICT,
    peso_relativo NUMERIC(5, 2) NOT NULL CHECK (peso_relativo > 0 AND peso_relativo <= 100),
    orden_presentacion SMALLINT,
    estado VARCHAR(15) NOT NULL DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR', 'PUBLICADO', 'CERRADO')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 2. ID SYNCHRONIZATION TRIGGERS
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
    ELSIF TG_TABLE_NAME = 'usuarios' THEN
        IF NEW.id_usuario IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_usuario := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_usuario IS NOT NULL THEN
            NEW.id := NEW.id_usuario;
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
    ELSIF TG_TABLE_NAME = 'matricula' THEN
        IF NEW.id_matricula IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_matricula := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_matricula IS NOT NULL THEN
            NEW.id := NEW.id_matricula;
        END IF;
        IF NEW.fecha_registro IS NULL AND NEW.fecha_matricula IS NOT NULL THEN
            NEW.fecha_registro := NEW.fecha_matricula;
        ELSIF NEW.fecha_matricula IS NULL AND NEW.fecha_registro IS NOT NULL THEN
            NEW.fecha_matricula := NEW.fecha_registro;
        END IF;
    ELSIF TG_TABLE_NAME = 'inscripcion' THEN
        IF NEW.id_inscripcion IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_inscripcion := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_inscripcion IS NOT NULL THEN
            NEW.id := NEW.id_inscripcion;
        END IF;
    ELSIF TG_TABLE_NAME = 'cuenta_seguimiento_alumno' THEN
        IF NEW.id_cuenta IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_cuenta := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_cuenta IS NOT NULL THEN
            NEW.id := NEW.id_cuenta;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_tenants BEFORE INSERT OR UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_usuarios BEFORE INSERT OR UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_periodo BEFORE INSERT OR UPDATE ON periodo_academico FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_plan_estudios BEFORE INSERT OR UPDATE ON plan_estudios FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_curso BEFORE INSERT OR UPDATE ON curso FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_seccion BEFORE INSERT OR UPDATE ON seccion FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_componente BEFORE INSERT OR UPDATE ON componente_evaluacion FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE TRIGGER trg_sync_asignacion BEFORE INSERT OR UPDATE ON asignacion_docente_seccion FOR EACH ROW EXECUTE FUNCTION sync_ids();

-- ==========================================
-- 3. ALCHEMY COMPATIBILITY SCHEMA (PHASE 2/3) & UNIFIED MODULES
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
    CONSTRAINT uq_escala_tenant UNIQUE (id_tenant)
);

CREATE TABLE tipo_componente (
    id_tipo_componente UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_comp_tenant_cod UNIQUE (id_tenant, codigo)
);

CREATE TABLE tipo_condicion_academica (
    id_tipo_condicion UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_cond_tenant_cod UNIQUE (id_tenant, codigo)
);

CREATE TABLE tipo_evento (
    id_tipo_evento UUID PRIMARY KEY,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    cuenta_objetivo VARCHAR(50) NOT NULL,
    operacion VARCHAR(20) NOT NULL CHECK (operacion IN ('INCREMENTO', 'DECREMENTO', 'ASIGNACION')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_event_tenant_cod UNIQUE (id_tenant, codigo)
);

CREATE TABLE perfil_alumno (
    id_perfil_alumno UUID PRIMARY KEY,
    id_usuario UUID NOT NULL UNIQUE REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    id_tenant UUID NOT NULL REFERENCES tenants (id_tenant) ON DELETE RESTRICT,
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

-- UNIFIED MATRICULA TABLE (Leonardo & Luis Gabriel)
CREATE TABLE matricula (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_matricula UUID, -- synced with id via trigger
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_alumno UUID REFERENCES usuarios (id) ON DELETE RESTRICT,
    id_perfil_alumno UUID REFERENCES perfil_alumno (id_perfil_alumno) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'RESERVADA', 'ANULADA', 'RETIRADA', 'FINALIZADA')),
    creditos_matriculados SMALLINT NOT NULL DEFAULT 0 CHECK (creditos_matriculados >= 0),
    fecha_matricula TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- synced with fecha_matricula via trigger
    numero_constancia VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_matricula_alumno_periodo UNIQUE (id_tenant, id_alumno, id_periodo)
);

CREATE TRIGGER trg_sync_matricula BEFORE INSERT OR UPDATE ON matricula FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE INDEX idx_matricula_tenant_periodo ON matricula (id_tenant, id_periodo);
CREATE INDEX idx_matricula_alumno ON matricula (id_alumno);

-- UNIFIED INSCRIPCION TABLE (Leonardo & Luis Gabriel)
CREATE TABLE inscripcion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_inscripcion UUID UNIQUE, -- synced with id via trigger
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_matricula UUID NOT NULL REFERENCES matricula (id) ON DELETE RESTRICT,
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_curso UUID REFERENCES curso (id) ON DELETE RESTRICT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'RETIRADA', 'APROBADA', 'DESAPROBADA', 'ANULADA')),
    creditos SMALLINT CHECK (creditos > 0),
    nota_final NUMERIC(5, 2) CHECK (nota_final IS NULL OR (nota_final >= 0 AND nota_final <= 100)),
    fecha_inscripcion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_retiro TIMESTAMPTZ,
    fecha_cambio_estado TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inscripcion_seccion UNIQUE (id_matricula, id_seccion)
);

CREATE TRIGGER trg_sync_inscripcion BEFORE INSERT OR UPDATE ON inscripcion FOR EACH ROW EXECUTE FUNCTION sync_ids();
CREATE UNIQUE INDEX uq_inscripcion_activa_curso ON inscripcion (id_matricula, id_curso) WHERE estado = 'ACTIVA';
CREATE INDEX idx_inscripcion_matricula ON inscripcion (id_matricula);
CREATE INDEX idx_inscripcion_seccion ON inscripcion (id_seccion);

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

-- UNIFIED CUENTA_SEGUIMIENTO_ALUMNO TABLE (Leonardo & Luis Gabriel)
CREATE TABLE cuenta_seguimiento_alumno (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_cuenta UUID, -- synced with id via trigger
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_alumno UUID REFERENCES usuarios (id) ON DELETE RESTRICT,
    id_perfil_alumno UUID REFERENCES perfil_alumno (id_perfil_alumno) ON DELETE RESTRICT,
    tipo_cuenta VARCHAR(40) CHECK (tipo_cuenta IN ('CTA-DESAPROBACIONES', 'CTA-CREDITOS-APROBADOS', 'CTA-CREDITOS-INSCRITOS', 'CTA-RESERVAS-MATRICULA', 'CTA-CONDICION-ACADEMICA', 'CTA-PROMEDIO-SNAPSHOT')),
    id_periodo_ref UUID REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    id_curso_ref UUID REFERENCES curso (id) ON DELETE RESTRICT,
    valor_actual NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (valor_actual >= 0),
    creditos_inscritos_periodo SMALLINT NOT NULL DEFAULT 0 CHECK (creditos_inscritos_periodo >= 0),
    creditos_aprobados_acumulados SMALLINT NOT NULL DEFAULT 0 CHECK (creditos_aprobados_acumulados >= 0),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cuenta_seguimiento_alumno UNIQUE (id_tenant, id_alumno),
    CONSTRAINT uq_cuenta_seguimiento_unique UNIQUE (id_perfil_alumno, tipo_cuenta, id_periodo_ref, id_curso_ref)
);

CREATE TRIGGER trg_sync_cuenta BEFORE INSERT OR UPDATE ON cuenta_seguimiento_alumno FOR EACH ROW EXECUTE FUNCTION sync_ids();

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
-- 4. INITIAL SEED DATA
-- ==========================================

INSERT INTO tenants (id, id_tenant, nombre, dominio, zona_horaria)
VALUES (
    'a1111111-1111-1111-1111-111111111111',
    'a1111111-1111-1111-1111-111111111111',
    'Universidad Demo',
    'uni-demo',
    'America/Lima'
) ON CONFLICT DO NOTHING;
