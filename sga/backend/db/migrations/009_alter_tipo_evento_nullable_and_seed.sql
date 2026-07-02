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
