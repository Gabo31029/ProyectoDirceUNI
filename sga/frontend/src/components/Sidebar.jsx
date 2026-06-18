import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'

const NAV_BY_ROL = {
  ADMIN_CENTRAL: [
    { section: 'Principal', items: [
      { to: '/admin-central', icon: '⊞', label: 'Dashboard' },
      { to: '/admin-central/tenants', icon: '🏛', label: 'Instituciones' },
      { to: '/admin-central/catalogos', icon: '📚', label: 'Catálogos' },
    ]},
  ],
  ADMIN: [
    { section: 'General', items: [
      { to: '/admin', icon: '⊞', label: 'Panel principal' },
      { to: '/admin/periodos', icon: '📅', label: 'Períodos académicos' },
    ]},
    { section: 'Configuración', items: [
      { to: '/admin/oferta', icon: '📖', label: 'Oferta académica' },
      { to: '/admin/usuarios', icon: '👥', label: 'Usuarios' },
    ]},
    { section: 'Académico', items: [
      { to: '/admin/cierre', icon: '🔒', label: 'Cierre académico' },
    ]},
  ],
  DOCENTE: [
    { section: 'Principal', items: [
      { to: '/docente', icon: '⊞', label: 'Mis secciones' },
      { to: '/docente/calificaciones', icon: '📝', label: 'Calificaciones' },
    ]},
  ],
  ALUMNO: [
    { section: 'Principal', items: [
      { to: '/alumno', icon: '⊞', label: 'Inicio' },
      { to: '/alumno/matricula', icon: '📋', label: 'Matrícula' },
      { to: '/alumno/historial', icon: '🎓', label: 'Historial académico' },
    ]},
  ],
}

export default function Sidebar({ collapsed, onToggle }) {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const sections = NAV_BY_ROL[auth?.rol] || []

  const handleLogout = async () => {
    await authService.logout()
    logout()
    navigate('/login')
  }

  return (
    <aside className={`sidebar${collapsed ? ' collapsed' : ''}`}>
      {/* Brand */}
      <div className="brandbox">
        <div className="brand-logo">S</div>
        <div className="brand-meta">
          <div className="brand-name">SGA</div>
          <div className="brand-sub">Gestión Académica</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="nav">
        {sections.map((sec, gi) => (
          <div className="nav-group" key={gi}>
            {sec.section && (
              <div className="nav-label eyebrow">{sec.section}</div>
            )}
            {sec.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to.split('/').length <= 2}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                title={item.label}
              >
                <span className="ic" style={{ fontSize: 16 }}>{item.icon}</span>
                <span className="lbl">{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-foot">
        <div
          className="nav-item"
          onClick={handleLogout}
          id="btn-logout"
          style={{ color: 'var(--red)', marginBottom: 4 }}
        >
          <span className="ic">🚪</span>
          <span className="lbl">Cerrar sesión</span>
        </div>
        <div className="nav-item" onClick={onToggle} title="Contraer">
          <span className="ic">{collapsed ? '›' : '‹'}</span>
          <span className="lbl">Contraer menú</span>
        </div>
      </div>
    </aside>
  )
}
