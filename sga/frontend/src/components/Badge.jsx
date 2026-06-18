const ESTADO_LABELS = {
  // Períodos
  CONFIGURACION: { label: 'Configuración', css: 'badge-warning' },
  MATRICULA: { label: 'Matrícula', css: 'badge-info' },
  REGISTRO_NOTAS: { label: 'Registro Notas', css: 'badge-indigo' },
  CERRADO: { label: 'Cerrado', css: 'badge-muted' },
  // Secciones
  ABIERTA: { label: 'Abierta', css: 'badge-success' },
  SUSPENDIDA: { label: 'Suspendida', css: 'badge-danger' },
  // Componentes
  BORRADOR: { label: 'Borrador', css: 'badge-warning' },
  PUBLICADO: { label: 'Publicado', css: 'badge-success' },
  // Inscripciones
  ACTIVA: { label: 'Activa', css: 'badge-success' },
  RETIRADA: { label: 'Retirada', css: 'badge-danger' },
  APROBADA: { label: 'Aprobada', css: 'badge-success' },
  DESAPROBADA: { label: 'Desaprobada', css: 'badge-danger' },
  ANULADA: { label: 'Anulada', css: 'badge-muted' },
  // Usuarios
  ADMIN: { label: 'Admin', css: 'badge-indigo' },
  ADMIN_CENTRAL: { label: 'Admin Central', css: 'badge-purple' },
  DOCENTE: { label: 'Docente', css: 'badge-info' },
  ALUMNO: { label: 'Alumno', css: 'badge-success' },
  // Tenant
  ACTIVO: { label: 'Activo', css: 'badge-success' },
  INACTIVO: { label: 'Inactivo', css: 'badge-danger' },
}

export default function Badge({ value, dot }) {
  const meta = ESTADO_LABELS[value] || { label: value, css: 'badge-muted' }
  return (
    <span className={`badge ${meta.css}`}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />}
      {meta.label}
    </span>
  )
}
