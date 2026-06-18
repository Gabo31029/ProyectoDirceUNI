-- SGA: Matricula e Inscripciones (Luis Gabriel Eustaquio Avila)
-- Responsable: editar solo este archivo para matrícula e inscripciones.

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
