-- =============================================================================
-- GENERADO por ./db/build_schema.sh — no editar schema.sql a mano.
-- Fuente: db/migrations/*.sql — ver db/README.md
-- =============================================================================

-- SGA Fase 1: Auth, Tenant, Usuarios (Leonardo Chavez Miranda)
-- Responsable: editar solo este archivo para cambios de auth/tenant.

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


-- Supabase híbrido (SQLAlchemy legacy + módulo matrícula Gabriel).
-- Ejecutar UNA VEZ en el SQL Editor de Supabase para pruebas de integración sin Docker.
-- Idempotente: CREATE OR REPLACE sobre la función sync_ids existente.

CREATE OR REPLACE FUNCTION public.sync_ids()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
    BEGIN
        IF TG_TABLE_NAME = 'tenants' THEN
            IF NEW.id_tenant IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_tenant := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_tenant IS NOT NULL THEN
                NEW.id := NEW.id_tenant;
            ELSIF NEW.id_tenant <> NEW.id THEN
                NEW.id_tenant := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'usuarios' THEN
            IF NEW.id_usuario IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_usuario := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_usuario IS NOT NULL THEN
                NEW.id := NEW.id_usuario;
            ELSIF NEW.id_usuario <> NEW.id THEN
                NEW.id_usuario := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'periodo_academico' THEN
            IF NEW.id_periodo IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_periodo := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_periodo IS NOT NULL THEN
                NEW.id := NEW.id_periodo;
            ELSIF NEW.id_periodo <> NEW.id THEN
                NEW.id_periodo := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'plan_estudios' THEN
            IF NEW.id_plan_estudios IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_plan_estudios := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_plan_estudios IS NOT NULL THEN
                NEW.id := NEW.id_periodo;
            ELSIF NEW.id_plan_estudios <> NEW.id THEN
                NEW.id_plan_estudios := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'curso' THEN
            IF NEW.id_curso IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_curso := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_curso IS NOT NULL THEN
                NEW.id := NEW.id_curso;
            ELSIF NEW.id_curso <> NEW.id THEN
                NEW.id_curso := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'seccion' THEN
            IF NEW.id_seccion IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_seccion := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_seccion IS NOT NULL THEN
                NEW.id := NEW.id_seccion;
            ELSIF NEW.id_seccion <> NEW.id THEN
                NEW.id_seccion := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'componente_evaluacion' THEN
            IF NEW.id_componente IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_componente := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_componente IS NOT NULL THEN
                NEW.id := NEW.id_componente;
            ELSIF NEW.id_componente <> NEW.id THEN
                NEW.id_componente := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'asignacion_docente_seccion' THEN
            IF NEW.id_asignacion IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_asignacion := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_asignacion IS NOT NULL THEN
                NEW.id := NEW.id_asignacion;
            ELSIF NEW.id_asignacion <> NEW.id THEN
                NEW.id_asignacion := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'matricula' THEN
            IF NEW.id_matricula IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_matricula := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_matricula IS NOT NULL THEN
                NEW.id := NEW.id_matricula;
            ELSIF NEW.id_matricula <> NEW.id THEN
                NEW.id_matricula := NEW.id;
            END IF;
            IF NEW.fecha_registro IS NULL AND NEW.fecha_matricula IS NOT NULL THEN
                NEW.fecha_registro := NEW.fecha_matricula;
            ELSIF NEW.fecha_matricula IS NULL AND NEW.fecha_registro IS NOT NULL THEN
                NEW.fecha_matricula := NEW.fecha_registro;
            END IF;
            IF NEW.id_perfil_alumno IS NULL AND NEW.id_alumno IS NOT NULL THEN
                SELECT pa.id_perfil_alumno INTO NEW.id_perfil_alumno
                FROM perfil_alumno pa
                WHERE pa.id_usuario = NEW.id_alumno
                LIMIT 1;
            END IF;
        ELSIF TG_TABLE_NAME = 'inscripcion' THEN
            IF NEW.id_inscripcion IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_inscripcion := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_inscripcion IS NOT NULL THEN
                NEW.id := NEW.id_inscripcion;
            ELSIF NEW.id_inscripcion <> NEW.id THEN
                NEW.id_inscripcion := NEW.id;
            END IF;
        ELSIF TG_TABLE_NAME = 'cuenta_seguimiento_alumno' THEN
            IF NEW.id_cuenta IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_cuenta := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_cuenta IS NOT NULL THEN
                NEW.id := NEW.id_cuenta;
            ELSIF NEW.id_cuenta <> NEW.id THEN
                NEW.id_cuenta := NEW.id;
            END IF;
            IF NEW.id_perfil_alumno IS NULL AND NEW.id_alumno IS NOT NULL THEN
                SELECT pa.id_perfil_alumno INTO NEW.id_perfil_alumno
                FROM perfil_alumno pa
                WHERE pa.id_usuario = NEW.id_alumno
                LIMIT 1;
            END IF;
            IF NEW.tipo_cuenta IS NULL THEN
                NEW.tipo_cuenta := 'CTA-CREDITOS-INSCRITOS';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $function$;


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


-- Sync existing users from usuarios to usuario
INSERT INTO public.usuario (
    id_usuario,
    id_tenant,
    nombre_completo,
    email,
    password_hash,
    rol,
    estado,
    fecha_registro
)
SELECT 
    u.id,
    COALESCE(t.id_tenant, 'b387616c-4731-489c-bc4d-84092face20b'),
    u.nombre || ' ' || u.apellido,
    u.email,
    u.password_hash,
    CASE 
        WHEN u.rol::text = 'ADMIN_CENTRAL' THEN 'ADMINISTRADOR_CENTRAL'
        WHEN u.rol::text = 'ADMIN' THEN 'ADMINISTRADOR'
        ELSE u.rol::text
    END,
    CASE WHEN u.activo THEN 'ACTIVO' ELSE 'INACTIVO' END,
    u.created_at
FROM public.usuarios u
LEFT JOIN public.tenants t ON u.id_tenant = t.id
ON CONFLICT (id_usuario) DO UPDATE SET
    id_tenant = EXCLUDED.id_tenant,
    nombre_completo = EXCLUDED.nombre_completo,
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    rol = EXCLUDED.rol,
    estado = EXCLUDED.estado,
    updated_at = NOW();

-- Create trigger function to sync changes from usuarios to usuario
CREATE OR REPLACE FUNCTION public.sync_usuarios_to_usuario_func()
RETURNS TRIGGER AS $$
DECLARE
    v_id_tenant UUID;
BEGIN
    SELECT t.id_tenant INTO v_id_tenant
    FROM public.tenants t
    WHERE t.id = NEW.id_tenant;

    IF v_id_tenant IS NULL THEN
        v_id_tenant := 'b387616c-4731-489c-bc4d-84092face20b';
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO public.usuario (
            id_usuario,
            id_tenant,
            nombre_completo,
            email,
            password_hash,
            rol,
            estado,
            fecha_registro
        ) VALUES (
            NEW.id,
            v_id_tenant,
            NEW.nombre || ' ' || NEW.apellido,
            NEW.email,
            NEW.password_hash,
            CASE 
                WHEN NEW.rol::text = 'ADMIN_CENTRAL' THEN 'ADMINISTRADOR_CENTRAL'
                WHEN NEW.rol::text = 'ADMIN' THEN 'ADMINISTRADOR'
                ELSE NEW.rol::text
            END,
            CASE WHEN NEW.activo THEN 'ACTIVO' ELSE 'INACTIVO' END,
            NEW.created_at
        ) ON CONFLICT (id_usuario) DO NOTHING;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE public.usuario SET
            id_tenant = v_id_tenant,
            nombre_completo = NEW.nombre || ' ' || NEW.apellido,
            email = NEW.email,
            password_hash = NEW.password_hash,
            rol = CASE 
                WHEN NEW.rol::text = 'ADMIN_CENTRAL' THEN 'ADMINISTRADOR_CENTRAL'
                WHEN NEW.rol::text = 'ADMIN' THEN 'ADMINISTRADOR'
                ELSE NEW.rol::text
            END,
            estado = CASE WHEN NEW.activo THEN 'ACTIVO' ELSE 'INACTIVO' END,
            updated_at = NOW()
        WHERE id_usuario = OLD.id;
    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM public.usuario WHERE id_usuario = OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_usuarios_to_usuario ON public.usuarios;
CREATE TRIGGER trg_sync_usuarios_to_usuario
AFTER INSERT OR UPDATE OR DELETE ON public.usuarios
FOR EACH ROW EXECUTE FUNCTION public.sync_usuarios_to_usuario_func();


-- 009_alter_tipo_evento_nullable_and_seed.sql
-- Alter table tipo_evento to allow nullable values for cuenta_objetivo and operacion
ALTER TABLE tipo_evento ALTER COLUMN cuenta_objetivo DROP NOT NULL;
ALTER TABLE tipo_evento ALTER COLUMN operacion DROP NOT NULL;

-- PL/pgSQL block to seed default events for all existing tenants
DO $$
DECLARE
    t RECORD;
    evt_id UUID;
BEGIN
    FOR t IN SELECT id, id_tenant FROM tenants LOOP
        -- 1. EVT-NOTA-FINAL-CALCULADA
        IF NOT EXISTS (SELECT 1 FROM cat_tipo_evento WHERE id_tenant = t.id AND codigo = 'EVT-NOTA-FINAL-CALCULADA') THEN
            evt_id := gen_random_uuid();
            INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id, 'EVT-NOTA-FINAL-CALCULADA', 'Nota Final Calculada', 'CTA-CREDITOS-APROBADOS', 'INCREMENTO');
            INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id_tenant, 'EVT-NOTA-FINAL-CALCULADA', 'Nota Final Calculada', 'CTA-CREDITOS-APROBADOS', 'INCREMENTO');
        END IF;

        -- 2. EVT-REPROBO-CURSO
        IF NOT EXISTS (SELECT 1 FROM cat_tipo_evento WHERE id_tenant = t.id AND codigo = 'EVT-REPROBO-CURSO') THEN
            evt_id := gen_random_uuid();
            INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id, 'EVT-REPROBO-CURSO', 'Reprobó Curso', 'CTA-DESAPROBACIONES', 'INCREMENTO');
            INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id_tenant, 'EVT-REPROBO-CURSO', 'Reprobó Curso', 'CTA-DESAPROBACIONES', 'INCREMENTO');
        END IF;

        -- 3. EVT-SNAPSHOT-PROMEDIO
        IF NOT EXISTS (SELECT 1 FROM cat_tipo_evento WHERE id_tenant = t.id AND codigo = 'EVT-SNAPSHOT-PROMEDIO') THEN
            evt_id := gen_random_uuid();
            INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id, 'EVT-SNAPSHOT-PROMEDIO', 'Snapshot de Promedio Semestral/Acumulado', 'CTA-PROMEDIO-SNAPSHOT', 'ASIGNACION');
            INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id_tenant, 'EVT-SNAPSHOT-PROMEDIO', 'Snapshot de Promedio Semestral/Acumulado', 'CTA-PROMEDIO-SNAPSHOT', 'ASIGNACION');
        END IF;

        -- 4. EVT-CONDICION-ACTIVADA
        IF NOT EXISTS (SELECT 1 FROM cat_tipo_evento WHERE id_tenant = t.id AND codigo = 'EVT-CONDICION-ACTIVADA') THEN
            evt_id := gen_random_uuid();
            INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id, 'EVT-CONDICION-ACTIVADA', 'Condición Académica Activada', NULL, NULL);
            INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id_tenant, 'EVT-CONDICION-ACTIVADA', 'Condición Académica Activada', NULL, NULL);
        END IF;

        -- 5. EVT-CONDICION-RESUELTA
        IF NOT EXISTS (SELECT 1 FROM cat_tipo_evento WHERE id_tenant = t.id AND codigo = 'EVT-CONDICION-RESUELTA') THEN
            evt_id := gen_random_uuid();
            INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id, 'EVT-CONDICION-RESUELTA', 'Condición Académica Resuelta', NULL, NULL);
            INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id_tenant, 'EVT-CONDICION-RESUELTA', 'Condición Académica Resuelta', NULL, NULL);
        END IF;

        -- 6. EVT-NOTA-CORREGIDA
        IF NOT EXISTS (SELECT 1 FROM cat_tipo_evento WHERE id_tenant = t.id AND codigo = 'EVT-NOTA-CORREGIDA') THEN
            evt_id := gen_random_uuid();
            INSERT INTO cat_tipo_evento (id, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id, 'EVT-NOTA-CORREGIDA', 'Nota Corregida por Docente', 'CTA-CREDITOS-APROBADOS', 'INCREMENTO');
            INSERT INTO tipo_evento (id_tipo_evento, id_tenant, codigo, nombre, cuenta_objetivo, operacion)
            VALUES (evt_id, t.id_tenant, 'EVT-NOTA-CORREGIDA', 'Nota Corregida por Docente', 'CTA-CREDITOS-APROBADOS', 'INCREMENTO');
        END IF;
    END LOOP;
END $$;


-- 010_rename_componente_to_evaluacion.sql

-- 1. Rename table cat_tipo_componente to cat_tipo_evaluacion
ALTER TABLE cat_tipo_componente RENAME TO cat_tipo_evaluacion;

-- 2. Rename table tipo_componente to tipo_evaluacion
ALTER TABLE tipo_componente RENAME TO tipo_evaluacion;
ALTER TABLE tipo_evaluacion RENAME COLUMN id_tipo_componente TO id_tipo_evaluacion;
ALTER TABLE tipo_evaluacion RENAME CONSTRAINT uq_tipo_componente_codigo TO uq_tipo_evaluacion_codigo;

-- 3. Rename columns and constraints in asignacion_docente_seccion
ALTER TABLE asignacion_docente_seccion RENAME COLUMN id_tipo_componente TO id_tipo_evaluacion;
ALTER TABLE asignacion_docente_seccion RENAME CONSTRAINT uq_asignacion_docente_componente TO uq_asignacion_docente_evaluacion;

-- 4. Rename table componente_evaluacion to evaluacion_academica
ALTER TABLE componente_evaluacion RENAME TO evaluacion_academica;
ALTER TABLE evaluacion_academica RENAME COLUMN id_componente TO id_evaluacion;
ALTER TABLE evaluacion_academica RENAME COLUMN id_tipo_componente TO id_tipo_evaluacion;
ALTER TABLE evaluacion_academica RENAME CONSTRAINT componente_evaluacion_peso_relativo_check TO evaluacion_academica_peso_relativo_check;
ALTER TABLE evaluacion_academica RENAME CONSTRAINT componente_evaluacion_estado_check TO evaluacion_academica_estado_check;

-- 5. Rename columns and constraints in calificacion
ALTER TABLE calificacion RENAME COLUMN id_componente TO id_evaluacion;
ALTER TABLE calificacion RENAME CONSTRAINT uq_calificacion_inscripcion_componente TO uq_calificacion_inscripcion_evaluacion;

-- 6. Drop the old trigger and recreate the new sync trigger for evaluacion_academica
DROP TRIGGER IF EXISTS trg_sync_componente ON evaluacion_academica;
CREATE TRIGGER trg_sync_evaluacion BEFORE INSERT OR UPDATE ON evaluacion_academica FOR EACH ROW EXECUTE FUNCTION sync_ids();

-- 7. Update the sync_ids trigger function to handle 'evaluacion_academica' instead of 'componente_evaluacion'
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
    ELSIF TG_TABLE_NAME = 'evaluacion_academica' THEN
        IF NEW.id_evaluacion IS NULL AND NEW.id IS NOT NULL THEN
            NEW.id_evaluacion := NEW.id;
        ELSIF NEW.id IS NULL AND NEW.id_evaluacion IS NOT NULL THEN
            NEW.id := NEW.id_evaluacion;
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


-- 011_curso_evaluacion_config.sql
-- Tabla que almacena la plantilla de evaluaciones y sus pesos para cada curso.
-- Esta configuración define cómo se calcula la nota final de ese curso:
--   nota_final = SUM(nota * peso) / SUM(pesos)

CREATE TABLE IF NOT EXISTS curso_evaluacion_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_curso        UUID NOT NULL REFERENCES curso(id) ON DELETE CASCADE,
    id_tipo_evaluacion UUID NOT NULL REFERENCES tipo_evaluacion(id_tipo_evaluacion) ON DELETE RESTRICT,
    peso            NUMERIC(7, 4) NOT NULL CHECK (peso > 0),
    orden           INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_curso_tipo_evaluacion UNIQUE (id_curso, id_tipo_evaluacion)
);

-- Índice para búsquedas frecuentes por curso
CREATE INDEX IF NOT EXISTS idx_curso_eval_config_curso ON curso_evaluacion_config(id_curso);


