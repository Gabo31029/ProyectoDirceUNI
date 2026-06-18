import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'
import ErrorAlert from '../components/ErrorAlert'

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
      // fetch user info to get nombre/apellido
      // Store token first so /me can authenticate
      login({ ...data, nombre: '', apellido: '' })
      try {
        const me = await authService.me()
        login({ ...data, nombre: me.nombre, apellido: me.apellido })
      } catch {
        // ignore, login is valid
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
    <div className="login-page">
      <div className="login-bg-gradient" />
      <div className="login-card">
        <div className="login-logo">
          <div className="logo-icon" style={{ width: 44, height: 44, fontSize: '1.3rem' }}>S</div>
          <div>
            <div className="login-title">SGA</div>
            <div className="login-subtitle">Sistema de Gestión Académica</div>
          </div>
        </div>

        <h1 style={{ fontSize: '1.25rem', marginBottom: 24 }}>Iniciar sesión</h1>

        <ErrorAlert message={error} onClose={() => setError('')} />

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Correo electrónico</label>
            <input
              id="email"
              name="email"
              type="email"
              className="form-input"
              placeholder="usuario@institución.edu"
              value={form.email}
              onChange={handleChange}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Contraseña</label>
            <input
              id="password"
              name="password"
              type="password"
              className="form-input"
              placeholder="Mínimo 8 caracteres"
              value={form.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="dominio_tenant">
              Dominio institucional{' '}
              <span style={{ color: 'var(--text-muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                (para Docentes y Alumnos)
              </span>
            </label>
            <input
              id="dominio_tenant"
              name="dominio_tenant"
              type="text"
              className="form-input"
              placeholder="ej: mi-universidad"
              value={form.dominio_tenant}
              onChange={handleChange}
              autoComplete="off"
            />
          </div>

          <button
            id="btn-login-submit"
            type="submit"
            className="btn btn-primary w-full"
            style={{ marginTop: 8, justifyContent: 'center', padding: '12px' }}
            disabled={loading}
          >
            {loading ? 'Autenticando...' : 'Ingresar al sistema'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Sistema de gestión académica — Grupo 4 &mdash; 2026-I
        </p>
      </div>
    </div>
  )
}
