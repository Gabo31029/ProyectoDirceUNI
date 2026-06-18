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
            END IF;
        ELSIF TG_TABLE_NAME = 'cuenta_seguimiento_alumno' THEN
            IF NEW.id_cuenta IS NULL AND NEW.id IS NOT NULL THEN
                NEW.id_cuenta := NEW.id;
            ELSIF NEW.id IS NULL AND NEW.id_cuenta IS NOT NULL THEN
                NEW.id := NEW.id_cuenta;
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
