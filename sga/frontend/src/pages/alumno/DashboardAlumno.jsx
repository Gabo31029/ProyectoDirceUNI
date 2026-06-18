import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import { periodoService } from '../../services/periodoService'
import { matriculaService } from '../../services/matriculaService'
import { useAuth } from '../../context/AuthContext'

export default function DashboardAlumno() {
  const { auth } = useAuth()
  const [periodo, setPeriodo] = useState(null)
  const [matriculas, setMatriculas] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const p = await periodoService.activo().catch(() => null)
        setPeriodo(p)
        if (auth?.id) {
          const ms = await matriculaService.listar(auth.id).catch(() => [])
          setMatriculas(ms)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [auth?.id])

  const matriculaActiva = matriculas.find(m => m.estado === 'ACTIVA')

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Hola, {auth?.nombre || 'Alumno'} 👋</h1>
            <p className="page-subtitle">Tu portal académico personal</p>
          </div>
        </div>

        <div className="grid-4 mb-6">
          <StatCard icon="📅" label="Período Activo" value={loading ? '...' : (periodo?.nombre_periodo || 'Ninguno')} colorClass="indigo" />
          <StatCard icon="📋" label="Estado Matrícula" value={loading ? '...' : (matriculaActiva ? 'Activa' : 'Sin matrícula')} colorClass={matriculaActiva ? 'green' : 'amber'} />
          <StatCard icon="📚" label="Créditos Matriculados" value={loading ? '...' : (matriculaActiva?.creditos_matriculados ?? '—')} colorClass="blue" />
          <StatCard icon="🎓" label="Mi Rol" value="ALUMNO" colorClass="purple" />
        </div>

        <div className="grid-2">
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>📅 Período Académico Activo</h3>
            {loading ? (
              <p className="text-muted text-sm">Cargando...</p>
            ) : !periodo ? (
              <div className="empty-state">
                <span className="empty-state-icon">📅</span>
                <span className="empty-state-title">Sin período activo</span>
              </div>
            ) : (
              <>
                <div className="info-grid">
                  <div className="info-item">
                    <div className="info-label">Período</div>
                    <div className="info-value">{periodo.nombre_periodo}</div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Estado</div>
                    <div className="info-value"><Badge value={periodo.estado} dot /></div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Inicio</div>
                    <div className="info-value">{periodo.fecha_inicio}</div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Fin</div>
                    <div className="info-value">{periodo.fecha_fin}</div>
                  </div>
                </div>
                {periodo.estado === 'MATRICULA' && (
                  <div className="alert alert-success" style={{ marginTop: 16 }}>
                    <span>✅</span>
                    <span>¡El período está en fase de <strong>MATRÍCULA</strong>! Puedes inscribirte en secciones.</span>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 16 }}>🗂️ Mi Matrícula Actual</h3>
            {loading ? (
              <p className="text-muted text-sm">Cargando...</p>
            ) : !matriculaActiva ? (
              <div className="empty-state">
                <span className="empty-state-icon">📋</span>
                <span className="empty-state-title">Sin matrícula activa</span>
                <span className="empty-state-text">Dirígete a Matrícula para inscribirte</span>
                <a href="/alumno/matricula" className="btn btn-primary btn-sm" style={{ marginTop: 8 }}>
                  Ir a Matrícula
                </a>
              </div>
            ) : (
              <>
                <div className="info-grid">
                  <div className="info-item">
                    <div className="info-label">Estado</div>
                    <div className="info-value"><Badge value={matriculaActiva.estado} dot /></div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Créditos</div>
                    <div className="info-value">{matriculaActiva.creditos_matriculados}</div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Fecha</div>
                    <div className="info-value">{new Date(matriculaActiva.fecha_matricula).toLocaleDateString('es-PE')}</div>
                  </div>
                </div>
                <a href="/alumno/matricula" className="btn btn-secondary btn-sm" style={{ marginTop: 12 }}>
                  Ver mis cursos →
                </a>
              </>
            )}
          </div>
        </div>

        <div className="card" style={{ marginTop: 20 }}>
          <h3 style={{ marginBottom: 16 }}>⚡ Accesos Rápidos</h3>
          <div className="grid-2">
            {[
              { icon: '📋', label: 'Mi Matrícula', sub: 'Ver e inscribir cursos', to: '/alumno/matricula' },
              { icon: '🎓', label: 'Historial Académico', sub: 'Notas y récord oficial', to: '/alumno/historial' },
            ].map(item => (
              <a
                key={item.to}
                href={item.to}
                id={`quick-${item.to.split('/').pop()}`}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '14px', borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', textDecoration: 'none',
                  transition: 'all var(--transition)',
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-500)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <span style={{ fontSize: '1.4rem' }}>{item.icon}</span>
                <div>
                  <div style={{ fontWeight: 600 }}>{item.label}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.sub}</div>
                </div>
                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>→</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
