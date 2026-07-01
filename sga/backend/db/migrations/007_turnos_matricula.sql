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
