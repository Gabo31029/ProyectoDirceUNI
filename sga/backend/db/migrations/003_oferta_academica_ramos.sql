-- SGA Fase 1: Oferta Académica (Dair Ramos)
-- Responsable: editar solo este archivo para plan de estudios, cursos y secciones.

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
