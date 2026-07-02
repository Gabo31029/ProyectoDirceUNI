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
