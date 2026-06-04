-- SGA Fase 1: Auth, Tenant, Usuarios (Leonardo Chavez Miranda)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

INSERT INTO tenants (id, nombre, dominio, zona_horaria)
VALUES (
    'a1111111-1111-1111-1111-111111111111',
    'Universidad Demo',
    'uni-demo',
    'America/Lima'
);

-- SGA Fase 1: Periodos Académicos y Políticas (Dair Ramos)
CREATE TABLE periodo_academico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- SGA Fase 1: Oferta Académica (Dair Ramos)
CREATE TABLE plan_estudios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_usuario_docente UUID NOT NULL REFERENCES usuarios (id) ON DELETE RESTRICT,
    id_tipo_componente UUID NOT NULL REFERENCES cat_tipo_componente (id) ON DELETE RESTRICT,
    es_coordinador BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_asignacion_docente_componente UNIQUE (id_seccion, id_usuario_docente, id_tipo_componente)
);

CREATE TABLE componente_evaluacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- SGA: Matricula e Inscripciones (Luis Gabriel Eustaquio Avila)
CREATE TABLE cuenta_seguimiento_alumno (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_alumno UUID NOT NULL REFERENCES usuarios (id) ON DELETE RESTRICT,
    creditos_inscritos_periodo SMALLINT NOT NULL DEFAULT 0 CHECK (creditos_inscritos_periodo >= 0),
    creditos_aprobados_acumulados SMALLINT NOT NULL DEFAULT 0 CHECK (creditos_aprobados_acumulados >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cuenta_seguimiento_alumno UNIQUE (id_tenant, id_alumno)
);

CREATE TABLE matricula (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_alumno UUID NOT NULL REFERENCES usuarios (id) ON DELETE RESTRICT,
    id_periodo UUID NOT NULL REFERENCES periodo_academico (id) ON DELETE RESTRICT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'RETIRADA', 'FINALIZADA')),
    creditos_matriculados SMALLINT NOT NULL DEFAULT 0 CHECK (creditos_matriculados >= 0),
    fecha_matricula TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_matricula_alumno_periodo UNIQUE (id_tenant, id_alumno, id_periodo)
);

CREATE INDEX idx_matricula_tenant_periodo ON matricula (id_tenant, id_periodo);
CREATE INDEX idx_matricula_alumno ON matricula (id_alumno);

CREATE TABLE inscripcion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_tenant UUID NOT NULL REFERENCES tenants (id) ON DELETE RESTRICT,
    id_matricula UUID NOT NULL REFERENCES matricula (id) ON DELETE RESTRICT,
    id_seccion UUID NOT NULL REFERENCES seccion (id) ON DELETE RESTRICT,
    id_curso UUID NOT NULL REFERENCES curso (id) ON DELETE RESTRICT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'RETIRADA', 'APROBADA', 'DESAPROBADA', 'ANULADA')),
    creditos SMALLINT NOT NULL CHECK (creditos > 0),
    fecha_inscripcion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_retiro TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_inscripcion_activa_curso
    ON inscripcion (id_matricula, id_curso)
    WHERE estado = 'ACTIVA';

CREATE INDEX idx_inscripcion_matricula ON inscripcion (id_matricula);
CREATE INDEX idx_inscripcion_seccion ON inscripcion (id_seccion);
