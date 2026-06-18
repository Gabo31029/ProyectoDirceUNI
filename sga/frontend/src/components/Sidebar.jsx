import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'
import Icon from './Icon'

const NAV_BY_ROL = {
  ADMIN_CENTRAL: [
    { section: 'Principal', items: [
      { to: '/admin-central', icon: 'grid', label: 'Dashboard' },
      { to: '/admin-central/tenants', icon: 'building', label: 'Instituciones' },
      { to: '/admin-central/catalogos', icon: 'library', label: 'Catálogos' },
    ]},
  ],
  ADMIN: [
    { section: 'General', items: [
      { to: '/admin', icon: 'grid', label: 'Panel principal' },
      { to: '/admin/periodos', icon: 'calendar', label: 'Períodos académicos' },
    ]},
    { section: 'Configuración', items: [
      { to: '/admin/oferta', icon: 'document', label: 'Oferta académica' },
      { to: '/admin/usuarios', icon: 'users', label: 'Usuarios' },
    ]},
    { section: 'Académico', items: [
      { to: '/admin/cierre', icon: 'lock', label: 'Cierre académico' },
    ]},
  ],
  DOCENTE: [
    { section: 'Principal', items: [
      { to: '/docente', icon: 'grid', label: 'Mis secciones' },
      { to: '/docente/calificaciones', icon: 'clipboard', label: 'Calificaciones' },
    ]},
  ],
  ALUMNO: [
    { section: 'Principal', items: [
      { to: '/alumno', icon: 'grid', label: 'Inicio' },
      { to: '/alumno/matricula', icon: 'clipboard', label: 'Matrícula' },
      { to: '/alumno/historial', icon: 'graduation-cap', label: 'Historial académico' },
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
      <div className="brandbox">
        <div className="brand-logo">S</div>
        <div className="brand-meta">
          <div className="brand-name">SGA</div>
          <div className="brand-sub">Gestión Académica</div>
        </div>
      </div>

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
                <span className="ic"><Icon name={item.icon} size={16} /></span>
                <span className="lbl">{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div
          className="nav-item"
          onClick={handleLogout}
          id="btn-logout"
          style={{ color: 'var(--red)' }}
        >
          <span className="ic"><Icon name="logout" size={16} /></span>
          <span className="lbl">Cerrar sesión</span>
        </div>
        <div className="nav-item" onClick={onToggle} title={collapsed ? 'Expandir' : 'Contraer'}>
          <span className="ic"><Icon name={collapsed ? 'chevron-right' : 'chevron-left'} size={16} /></span>
          <span className="lbl">Contraer menú</span>
        </div>
      </div>
    </aside>
  )
}
