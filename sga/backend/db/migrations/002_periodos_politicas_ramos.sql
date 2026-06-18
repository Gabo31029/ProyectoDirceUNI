-- SGA Fase 1: Periodos Académicos y Políticas (Dair Ramos)
-- Responsable: editar solo este archivo para periodos y políticas.

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
