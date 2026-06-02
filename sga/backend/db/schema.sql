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
