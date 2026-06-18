import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'

const ROL_LABEL = {
  ADMIN_CENTRAL: 'Administrador Central',
  ADMIN: 'Administrador Académico',
  DOCENTE: 'Docente',
  ALUMNO: 'Alumno',
}

export default function Topbar() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await authService.logout()
    logout()
    navigate('/login')
  }

  const initials = [auth?.nombre?.[0], auth?.apellido?.[0]]
    .filter(Boolean).join('').toUpperCase() || '?'

  return (
    <header className="topbar">
      <div className="topbar-spacer" />

      <button className="iconbtn" title="Notificaciones" aria-label="Notificaciones">
        🔔
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ textAlign: 'right', lineHeight: 1.3 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>
            {auth?.nombre} {auth?.apellido}
          </div>
          <div className="caption">{ROL_LABEL[auth?.rol] || auth?.rol}</div>
        </div>
        <div
          className="avatar"
          style={{ cursor: 'pointer' }}
          onClick={handleLogout}
          title="Cerrar sesión"
        >
          {initials}
        </div>
      </div>
    </header>
  )
}
