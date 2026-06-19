import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import Icon from '../../components/Icon'
import { periodoService } from '../../services/periodoService'
import { matriculaService } from '../../services/matriculaService'
import { useAuth } from '../../context/AuthContext'

export default function DashboardAlumno() {
  const { auth } = useAuth()
  const navigate = useNavigate()
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
        <div className="page-head">
          <div className="ph-l">
            <h1 className="h1">Hola, {auth?.nombre || 'Alumno'}</h1>
            <p className="ph-sub">Resumen de tu período académico</p>
          </div>
        </div>

        <div className="stat-grid" style={{ marginBottom: 24 }}>
          <StatCard icon={<Icon name="calendar" size={18} />} label="Período Activo" value={loading ? '…' : (periodo?.nombre_periodo || 'Ninguno')} colorClass="indigo" />
          <StatCard icon={<Icon name="clipboard" size={18} />} label="Estado Matrícula" value={loading ? '…' : (matriculaActiva ? 'Activa' : 'Sin matrícula')} colorClass={matriculaActiva ? 'green' : 'amber'} />
          <StatCard icon={<Icon name="bar-chart" size={18} />} label="Créditos" value={loading ? '…' : (matriculaActiva?.creditos_matriculados ?? '—')} colorClass="blue" />
          <StatCard icon={<Icon name="graduation-cap" size={18} />} label="Rol" value="Alumno" colorClass="violet" />
        </div>

        <div className="grid-2">
          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Período académico activo</div>
            {loading ? (
              <p className="muted small">Cargando…</p>
            ) : !periodo ? (
              <div className="empty">
                <div className="empty-ic"><Icon name="calendar" size={32} style={{ color: 'var(--ink-4)' }} /></div>
                <div className="empty-title">Sin período activo</div>
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
                {periodo.estado === 'MATRICULA' && (
                  <div className="banner banner-success" style={{ marginTop: 16 }}>
                    <Icon name="check-circle" size={14} />
                    <span>El período está en fase de <strong>Matrícula</strong>. Puedes inscribirte en secciones.</span>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Matrícula actual</div>
            {loading ? (
              <p className="muted small">Cargando…</p>
            ) : !matriculaActiva ? (
              <div className="empty">
                <div className="empty-ic"><Icon name="clipboard" size={32} style={{ color: 'var(--ink-4)' }} /></div>
                <div className="empty-title">Sin matrícula activa</div>
                <div className="empty-sub">Ve a Matrícula para inscribirte en secciones</div>
                <button className="btn btn-primary btn-sm" style={{ marginTop: 16 }} onClick={() => navigate('/alumno/matricula')}>
                  Ir a Matrícula
                </button>
              </div>
            ) : (
              <>
                <div className="info-grid">
                  <div>
                    <div className="info-label">Estado</div>
                    <div className="info-value"><Badge value={matriculaActiva.estado} dot /></div>
                  </div>
                  <div>
                    <div className="info-label">Créditos</div>
                    <div className="info-value">{matriculaActiva.creditos_matriculados}</div>
                  </div>
                  <div>
                    <div className="info-label">Fecha</div>
                    <div className="info-value">{new Date(matriculaActiva.fecha_matricula).toLocaleDateString('es-PE')}</div>
                  </div>
                </div>
                <button className="btn btn-secondary btn-sm" style={{ marginTop: 16 }} onClick={() => navigate('/alumno/matricula')}>
                  Ver mis cursos
                </button>
              </>
            )}
          </div>
        </div>

        <div className="card card-pad" style={{ marginTop: 20 }}>
          <div className="h3" style={{ marginBottom: 14 }}>Accesos rápidos</div>
          <div className="grid-2">
            {[
              { icon: 'clipboard', label: 'Mi Matrícula', sub: 'Ver e inscribir cursos', to: '/alumno/matricula' },
              { icon: 'graduation-cap', label: 'Historial Académico', sub: 'Notas y récord oficial', to: '/alumno/historial' },
            ].map(item => (
              <button
                key={item.to}
                id={`quick-${item.to.split('/').pop()}`}
                onClick={() => navigate(item.to)}
                className="quicklink"
              >
                <Icon name={item.icon} size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.label}</div>
                  <div className="caption">{item.sub}</div>
                </div>
                <Icon name="chevron-right" size={14} style={{ color: 'var(--ink-4)' }} />
              </button>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
