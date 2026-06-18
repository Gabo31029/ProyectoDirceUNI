import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import { periodoService } from '../../services/periodoService'
import { useAuth } from '../../context/AuthContext'

export default function DashboardDocente() {
  const { auth } = useAuth()
  const [periodo, setPeriodo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    periodoService.activo()
      .then(setPeriodo)
      .catch(() => setPeriodo(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Bienvenido, {auth?.nombre || 'Docente'}</h1>
            <p className="page-subtitle">Panel del docente — gestión de calificaciones</p>
          </div>
        </div>

        <div className="grid-3 mb-6">
          <StatCard icon="📅" label="Período Activo" value={loading ? '...' : (periodo?.nombre_periodo || 'Ninguno')} colorClass="indigo" />
          <StatCard icon="📊" label="Estado Período" value={loading ? '...' : (periodo?.estado || '—')} colorClass="blue" />
          <StatCard icon="👤" label="Mi Rol" value="DOCENTE" colorClass="purple" />
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>📋 Estado del Período Académico</h3>
          {loading ? (
            <p className="text-muted text-sm">Cargando...</p>
          ) : !periodo ? (
            <div className="empty-state">
              <span className="empty-state-icon">📅</span>
              <span className="empty-state-title">Sin período activo</span>
              <span className="empty-state-text">No hay un período académico activo en este momento</span>
            </div>
          ) : (
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
                <div className="info-label">Fecha Inicio</div>
                <div className="info-value">{periodo.fecha_inicio}</div>
              </div>
              <div className="info-item">
                <div className="info-label">Fecha Fin</div>
                <div className="info-value">{periodo.fecha_fin}</div>
              </div>
            </div>
          )}

          {periodo?.estado === 'REGISTRO_NOTAS' && (
            <div className="alert alert-info" style={{ marginTop: 16 }}>
              <span>📝</span>
              <span>El período está en <strong>REGISTRO_NOTAS</strong>. Puedes registrar y publicar calificaciones.</span>
            </div>
          )}
        </div>

        <div className="card" style={{ marginTop: 20 }}>
          <h3 style={{ marginBottom: 16 }}>⚡ Accesos Rápidos</h3>
          <a
            href="/docente/calificaciones"
            id="link-calificaciones"
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
            <span style={{ fontSize: '1.4rem' }}>📝</span>
            <div>
              <div style={{ fontWeight: 600 }}>Gestionar Calificaciones</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Registrar notas y publicar componentes de evaluación</div>
            </div>
            <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>→</span>
          </a>
        </div>
      </div>
    </Layout>
  )
}
