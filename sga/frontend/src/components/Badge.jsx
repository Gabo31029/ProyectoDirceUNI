const ESTADO_MAP = {
  // Períodos
  CONFIGURACION:   { label: 'Configuración',   tone: 'amber' },
  MATRICULA:       { label: 'Matrícula',        tone: 'blue' },
  REGISTRO_NOTAS:  { label: 'Reg. Notas',       tone: 'violet' },
  CERRADO:         { label: 'Cerrado',           tone: 'gray' },
  // Secciones
  ABIERTA:         { label: 'Abierta',           tone: 'green' },
  SUSPENDIDA:      { label: 'Suspendida',        tone: 'red' },
  // Componentes
  BORRADOR:        { label: 'Borrador',          tone: 'amber' },
  PUBLICADO:       { label: 'Publicado',         tone: 'green' },
  // Inscripciones
  ACTIVA:          { label: 'Activa',            tone: 'green' },
  RETIRADA:        { label: 'Retirada',          tone: 'red' },
  APROBADA:        { label: 'Aprobada',          tone: 'green' },
  DESAPROBADA:     { label: 'Desaprobada',       tone: 'red' },
  ANULADA:         { label: 'Anulada',           tone: 'gray' },
  // Roles
  ADMIN:           { label: 'Admin',             tone: 'blue' },
  ADMIN_CENTRAL:   { label: 'Admin Central',     tone: 'violet' },
  DOCENTE:         { label: 'Docente',           tone: 'blue' },
  ALUMNO:          { label: 'Alumno',            tone: 'green' },
  // Tenant
  ACTIVO:          { label: 'Activo',            tone: 'green' },
  INACTIVO:        { label: 'Inactivo',          tone: 'red' },
  // Académico
  NORMAL:              { label: 'Normal',              tone: 'green' },
  RIESGO_ACADEMICO:    { label: 'Riesgo Académico',    tone: 'amber' },
  SUSPENDIDO:          { label: 'Suspendido',           tone: 'red' },
  RETIRADO_DEFINITIVO: { label: 'Retirado Definitivo', tone: 'red' },
}

export default function Badge({ value, dot }) {
  const meta = ESTADO_MAP[value] || { label: value, tone: 'gray' }
  return (
    <span className={`pill ${meta.tone}`}>
      {dot && <span className="dot" />}
      {meta.label}
    </span>
  )
}
