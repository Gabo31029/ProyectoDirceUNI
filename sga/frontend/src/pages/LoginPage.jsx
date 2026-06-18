import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'

const ROLE_REDIRECT = {
  ADMIN_CENTRAL: '/admin-central',
  ADMIN: '/admin',
  DOCENTE: '/docente',
  ALUMNO: '/alumno',
}

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '', dominio_tenant: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await authService.login(
        form.email,
        form.password,
        form.dominio_tenant || undefined
      )
      login({ ...data, nombre: '', apellido: '' })
      try {
        const me = await authService.me()
        login({ ...data, nombre: me.nombre, apellido: me.apellido })
      } catch {
        // ignore
      }
      navigate(ROLE_REDIRECT[data.rol] || '/')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Credenciales incorrectas. Verifica tus datos.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-stage">
      <div className="auth-card fade-in">
        {/* Logo centrado */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div className="auth-logo">S</div>
          <div className="h2" style={{ marginBottom: 4 }}>SGA</div>
          <div className="caption">Sistema de Gestión Académica</div>
        </div>

        <div className="card card-pad" style={{ padding: '26px' }}>
          {error && (
            <div className="banner banner-danger" style={{ marginBottom: 16 }}>
              <span style={{ flex: 1 }}>⚠ {error}</span>
              <button
                onClick={() => setError('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem', padding: 0 }}
                aria-label="Cerrar"
              >×</button>
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
                placeholder="ej: mi-universidad"
                value={form.dominio_tenant}
                onChange={handleChange}
                autoComplete="off"
              />
            </div>

            <button
              id="btn-login-submit"
              type="submit"
              className="btn btn-primary btn-block btn-lg"
              disabled={loading}
            >
              {loading ? 'Autenticando…' : 'Iniciar sesión →'}
            </button>
          </form>
        </div>

        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <span className="caption">
            Plataforma multi-institucional <strong style={{ color: 'var(--ink-2)' }}>SGA</strong> · 2026-I
          </span>
        </div>
      </div>
    </div>
  )
}
