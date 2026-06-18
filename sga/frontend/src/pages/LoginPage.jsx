import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'
import Icon from '../components/Icon'

const ROLE_REDIRECT = {
  ADMIN_CENTRAL: '/admin-central',
  ADMIN: '/admin',
  DOCENTE: '/docente',
  ALUMNO: '/alumno',
}

const DEMO_ACCOUNTS = [
  {
    id: 'btn-demo-admin-central',
    role: 'ADMIN_CENTRAL',
    label: 'Admin Central',
    email: 'admin.central@sga.local',
    password: 'AdminCentral123!',
    dominio_tenant: '',
  },
  {
    id: 'btn-demo-admin',
    role: 'ADMIN',
    label: 'Administrador',
    email: 'admin@uni-demo.local',
    password: 'AdminDemo123!',
    dominio_tenant: 'uni-demo',
  },
  {
    id: 'btn-demo-alumno',
    role: 'ALUMNO',
    label: 'Alumno',
    email: 'alumno@uni-demo.local',
    password: 'AlumnoDemo123!',
    dominio_tenant: 'uni-demo',
  },
  {
    id: 'btn-demo-docente',
    role: 'DOCENTE',
    label: 'Docente',
    email: null,
    password: null,
    dominio_tenant: 'uni-demo',
    disabled: true,
    hint: 'Sin cuenta demo',
  },
]

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '', dominio_tenant: '' })
  const [loading, setLoading] = useState(false)
  const [loadingDemo, setLoadingDemo] = useState('')
  const [error, setError] = useState('')

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const doLogin = async (email, password, dominio_tenant) => {
    const data = await authService.login(email, password, dominio_tenant || undefined)
    login({ ...data, nombre: '', apellido: '' })
    try {
      const me = await authService.me()
      login({ ...data, nombre: me.nombre, apellido: me.apellido })
    } catch {
      // ignore
    }
    navigate(ROLE_REDIRECT[data.rol] || '/')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await doLogin(form.email, form.password, form.dominio_tenant)
    } catch (err) {
      setError(err.response?.data?.detail || 'Credenciales incorrectas. Verifica tus datos.')
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = async (account) => {
    if (account.disabled) return
    setError('')
    setLoadingDemo(account.role)
    try {
      await doLogin(account.email, account.password, account.dominio_tenant)
    } catch (err) {
      setError(err.response?.data?.detail || `No se pudo acceder con la cuenta demo de ${account.label}.`)
    } finally {
      setLoadingDemo('')
    }
  }

  const anyLoading = loading || loadingDemo !== ''

  return (
    <div className="auth-stage">
      <div className="auth-card fade-in">
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div className="auth-logo">S</div>
          <div className="h2" style={{ marginBottom: 4 }}>SGA</div>
          <div className="caption">Sistema de Gestión Académica</div>
        </div>

        <div className="card card-pad" style={{ padding: '26px' }}>
          {error && (
            <div className="banner banner-danger" style={{ marginBottom: 16 }}>
              <Icon name="warning" size={14} style={{ flexShrink: 0 }} />
              <span style={{ flex: 1 }}>{error}</span>
              <button
                onClick={() => setError('')}
                className="iconbtn"
                aria-label="Cerrar"
              >
                <Icon name="x" size={13} />
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="field" style={{ marginBottom: 14 }}>
              <label className="label" htmlFor="email">Correo electrónico</label>
              <input
                id="email"
                name="email"
                type="email"
                className="input"
                placeholder="usuario@institución.edu"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
                disabled={anyLoading}
              />
            </div>

            <div className="field" style={{ marginBottom: 14 }}>
              <label className="label" htmlFor="password">Contraseña</label>
              <input
                id="password"
                name="password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                required
                autoComplete="current-password"
                disabled={anyLoading}
              />
            </div>

            <div className="field" style={{ marginBottom: 20 }}>
              <label className="label" htmlFor="dominio_tenant">
                Dominio institucional{' '}
                <span style={{ color: 'var(--ink-3)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                  (Docentes y Alumnos)
                </span>
              </label>
              <input
                id="dominio_tenant"
                name="dominio_tenant"
                type="text"
                className="input"
                placeholder="ej: uni-demo"
                value={form.dominio_tenant}
                onChange={handleChange}
                autoComplete="off"
                disabled={anyLoading}
              />
            </div>

            <button
              id="btn-login-submit"
              type="submit"
              className="btn btn-primary btn-block btn-lg"
              disabled={anyLoading}
            >
              {loading ? 'Autenticando…' : 'Iniciar sesión'}
            </button>
          </form>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '20px 0 14px' }}>
            <div className="divider" style={{ flex: 1 }} />
            <span className="caption">Acceso de demostración</span>
            <div className="divider" style={{ flex: 1 }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {DEMO_ACCOUNTS.map(acc => (
              <button
                key={acc.role}
                id={acc.id}
                type="button"
                disabled={anyLoading || acc.disabled}
                onClick={() => handleDemo(acc)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: 8,
                  height: 42, padding: '0 12px', borderRadius: 'var(--r-sm)',
                  border: `1px solid ${acc.disabled ? 'var(--line)' : 'var(--line-2)'}`,
                  background: acc.disabled ? 'var(--surface-2)' : 'var(--surface)',
                  color: acc.disabled ? 'var(--ink-4)' : 'var(--ink-2)',
                  cursor: acc.disabled ? 'not-allowed' : 'pointer',
                  fontSize: 13, fontWeight: 500, fontFamily: 'var(--font)',
                  transition: 'background .12s, border-color .12s, color .12s',
                  opacity: acc.disabled ? 0.6 : 1,
                }}
                onMouseEnter={e => {
                  if (!acc.disabled && !anyLoading) {
                    e.currentTarget.style.borderColor = 'var(--accent)'
                    e.currentTarget.style.color = 'var(--accent-ink)'
                    e.currentTarget.style.background = 'var(--accent-soft)'
                  }
                }}
                onMouseLeave={e => {
                  if (!acc.disabled) {
                    e.currentTarget.style.borderColor = 'var(--line-2)'
                    e.currentTarget.style.color = 'var(--ink-2)'
                    e.currentTarget.style.background = 'var(--surface)'
                  }
                }}
                title={acc.disabled ? acc.hint : `Ingresar como ${acc.label}`}
              >
                <Icon
                  name={acc.role === 'ADMIN_CENTRAL' ? 'globe' : acc.role === 'ADMIN' ? 'settings' : acc.role === 'ALUMNO' ? 'graduation-cap' : 'clipboard'}
                  size={14}
                  style={{ flexShrink: 0, opacity: acc.disabled ? 0.5 : 1 }}
                />
                <span style={{ flex: 1, textAlign: 'left' }}>
                  {loadingDemo === acc.role ? 'Ingresando…' : acc.label}
                </span>
                {acc.disabled && (
                  <span style={{ fontSize: 10, color: 'var(--ink-4)' }}>N/D</span>
                )}
              </button>
            ))}
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <span className="caption">
            SGA · Plataforma académica multi-institucional · 2026-I
          </span>
        </div>
      </div>
    </div>
  )
}
