import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import Icon from '../../components/Icon'
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
            <h1 className="h1">Hola, {auth?.nombre || 'Docente'}</h1>
            <p className="ph-sub">Tus secciones y calificaciones del período activo</p>
          </div>
        </div>

        <div className="stat-grid" style={{ marginBottom: 24 }}>
          <StatCard icon={<Icon name="calendar" size={18} />} label="Período Activo" value={loading ? '…' : (periodo?.nombre_periodo || 'Ninguno')} colorClass="indigo" />
          <StatCard icon={<Icon name="bar-chart" size={18} />} label="Estado del Período" value={loading ? '…' : (periodo?.estado || '—')} colorClass="blue" />
          <StatCard icon={<Icon name="user" size={18} />} label="Rol" value="Docente" colorClass="green" />
        </div>

        <div className="grid-2">
          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Período académico</div>
            {loading ? (
              <p className="muted small">Cargando…</p>
            ) : !periodo ? (
              <div className="empty">
                <div className="empty-ic"><Icon name="calendar" size={32} style={{ color: 'var(--ink-4)' }} /></div>
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
                    <Icon name="info" size={14} />
                    <span>El período está en <strong>Registro de Notas</strong>. Puedes registrar y publicar calificaciones.</span>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Accesos rápidos</div>
            <button
              id="link-calificaciones"
              onClick={() => navigate('/docente/calificaciones')}
              className="quicklink"
            >
              <Icon name="clipboard" size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>Calificaciones</div>
                <div className="caption">Registrar notas y publicar componentes</div>
              </div>
              <Icon name="chevron-right" size={14} style={{ color: 'var(--ink-4)' }} />
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
