import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'

const NAV_BY_ROL = {
  ADMIN_CENTRAL: [
    { section: 'Principal', items: [
      { to: '/admin-central', icon: '🏠', label: 'Dashboard', id: 'nav-dashboard' },
      { to: '/admin-central/tenants', icon: '🏛️', label: 'Instituciones', id: 'nav-tenants' },
      { to: '/admin-central/catalogos', icon: '📚', label: 'Catálogos', id: 'nav-catalogos' },
    ]},
  ],
  ADMIN: [
    { section: 'Principal', items: [
      { to: '/admin', icon: '🏠', label: 'Dashboard', id: 'nav-dashboard' },
    ]},
    { section: 'Gestión Académica', items: [
      { to: '/admin/periodos', icon: '📅', label: 'Períodos', id: 'nav-periodos' },
      { to: '/admin/oferta', icon: '📖', label: 'Oferta Académica', id: 'nav-oferta' },
      { to: '/admin/cierre', icon: '🔒', label: 'Cierre Académico', id: 'nav-cierre' },
    ]},
    { section: 'Configuración', items: [
      { to: '/admin/usuarios', icon: '👥', label: 'Usuarios', id: 'nav-usuarios' },
    ]},
  ],
  DOCENTE: [
    { section: 'Principal', items: [
      { to: '/docente', icon: '🏠', label: 'Dashboard', id: 'nav-dashboard' },
      { to: '/docente/calificaciones', icon: '📝', label: 'Calificaciones', id: 'nav-calificaciones' },
    ]},
  ],
  ALUMNO: [
    { section: 'Principal', items: [
      { to: '/alumno', icon: '🏠', label: 'Dashboard', id: 'nav-dashboard' },
      { to: '/alumno/matricula', icon: '📋', label: 'Matrícula', id: 'nav-matricula' },
      { to: '/alumno/historial', icon: '🎓', label: 'Historial Académico', id: 'nav-historial' },
    ]},
  ],
}

export default function Sidebar() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const sections = NAV_BY_ROL[auth?.rol] || []

  const handleLogout = async () => {
    await authService.logout()
    logout()
    navigate('/login')
  }

  const initials = [auth?.nombre?.[0], auth?.apellido?.[0]].filter(Boolean).join('').toUpperCase() || '?'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">
          <div className="logo-icon">S</div>
          <div>
            <div className="logo-text">SGA</div>
            <div className="logo-subtitle">Gestión Académica</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {sections.map(sec => (
          <div key={sec.section}>
            <div className="nav-section-label">{sec.section}</div>
            {sec.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to.split('/').length <= 2}
                id={item.id}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 4px', marginBottom: 8 }}>
          <div className="user-avatar" style={{ width: 36, height: 36 }}>{initials}</div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div className="user-name" style={{ fontSize: '0.82rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {auth?.nombre} {auth?.apellido}
            </div>
            <div className="user-role">{auth?.rol}</div>
          </div>
        </div>
        <button
          id="btn-logout"
          className="btn btn-ghost w-full"
          style={{ justifyContent: 'flex-start', color: 'var(--danger)', fontSize: '0.85rem' }}
          onClick={handleLogout}
        >
          🚪 Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
