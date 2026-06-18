import { useAuth } from '../context/AuthContext'

const ROL_LABEL = {
  ADMIN_CENTRAL: 'Administrador Central',
  ADMIN: 'Administrador Académico',
  DOCENTE: 'Docente',
  ALUMNO: 'Alumno',
}

export default function Topbar() {
  const { auth } = useAuth()
  const initials = [auth?.nombre?.[0], auth?.apellido?.[0]]
    .filter(Boolean).join('').toUpperCase() || '?'

  return (
    <header className="topbar">
      <div className="topbar-spacer" />
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ textAlign: 'right', lineHeight: 1.3 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>
            {auth?.nombre} {auth?.apellido}
          </div>
          <div className="caption">{ROL_LABEL[auth?.rol] || auth?.rol}</div>
        </div>
        <div className="avatar">{initials}</div>
      </div>
    </header>
  )
}
