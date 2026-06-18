import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import { periodoService } from '../../services/periodoService'
import { useAuth } from '../../context/AuthContext'

export default function DashboardDocente() {
  const { auth } = useAuth()
  const navigate = useNavigate()
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
        <div className="page-head">
          <div className="ph-l">
            <h1 className="h1">Bienvenido, {auth?.nombre || 'Docente'} 👋</h1>
            <p className="ph-sub">Panel del docente — gestión de calificaciones</p>
          </div>
        </div>

        <div className="stat-grid" style={{ marginBottom: 24 }}>
          <StatCard icon="📅" label="Período Activo" value={loading ? '…' : (periodo?.nombre_periodo || 'Ninguno')} colorClass="indigo" />
          <StatCard icon="📊" label="Estado del Período" value={loading ? '…' : (periodo?.estado || '—')} colorClass="blue" />
          <StatCard icon="👤" label="Rol" value="Docente" colorClass="green" />
        </div>

        <div className="grid-2">
          {/* Estado del período */}
          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>📅 Período Académico</div>
            {loading ? (
              <p className="muted small">Cargando…</p>
            ) : !periodo ? (
              <div className="empty">
                <div className="empty-ic">📅</div>
                <div className="empty-title">Sin período activo</div>
                <div className="empty-sub">No hay un período académico activo en este momento</div>
              </div>
            ) : (
              <>
                <div className="info-grid">
                  <div>
                    <div className="info-label">Período</div>
                    <div className="info-value">{periodo.nombre_periodo}</div>
                  </div>
                  <div>
                    <div className="info-label">Estado</div>
                    <div className="info-value"><Badge value={periodo.estado} dot /></div>
                  </div>
                  <div>
                    <div className="info-label">Inicio</div>
                    <div className="info-value">{periodo.fecha_inicio}</div>
                  </div>
                  <div>
                    <div className="info-label">Fin</div>
                    <div className="info-value">{periodo.fecha_fin}</div>
                  </div>
                </div>
                {periodo?.estado === 'REGISTRO_NOTAS' && (
                  <div className="banner banner-info" style={{ marginTop: 16 }}>
                    📝 El período está en <strong>Registro de Notas</strong>. Puedes registrar y publicar calificaciones.
                  </div>
                )}
              </>
            )}
          </div>

          {/* Accesos rápidos */}
          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Accesos rápidos</div>
            <button
              id="link-calificaciones"
              onClick={() => navigate('/docente/calificaciones')}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '11px 14px', borderRadius: 'var(--r-sm)',
                background: 'var(--surface-2)', border: '1px solid var(--line)',
                color: 'var(--ink)', cursor: 'pointer', width: '100%', textAlign: 'left',
                transition: 'border-color .14s, background .14s',
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'var(--accent-soft)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.background = 'var(--surface-2)'; }}
            >
              <span style={{ fontSize: '1.4rem' }}>📝</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>Gestionar Calificaciones</div>
                <div className="caption">Registrar notas y publicar componentes de evaluación</div>
              </div>
              <span style={{ color: 'var(--ink-3)' }}>›</span>
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
