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
