import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import { periodoService } from '../../services/periodoService'
import { ofertaService } from '../../services/ofertaService'
import { userService } from '../../services/userService'

const ESTADOS_PERIODO = ['CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO']

export default function DashboardAdmin() {
  const [periodo, setPeriodo] = useState(null)
  const [secciones, setSecciones] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const p = await periodoService.activo().catch(() => null)
        setPeriodo(p)
        if (p) {
          const s = await ofertaService.listarSecciones(p.id).catch(() => [])
          setSecciones(s)
        }
        const u = await userService.listar().catch(() => [])
        setUsuarios(u)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const estadoIdx = periodo ? ESTADOS_PERIODO.indexOf(periodo.estado) : -1

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Panel Administrador</h1>
            <p className="page-subtitle">Vista general del período académico activo</p>
          </div>
        </div>

        <div className="grid-4 mb-6">
          <StatCard
            icon="📅"
            label="Período Activo"
            value={loading ? '...' : (periodo?.nombre_periodo || 'Ninguno')}
            colorClass="indigo"
          />
          <StatCard
            icon="📖"
            label="Secciones Abiertas"
            value={loading ? '...' : secciones.filter(s => s.estado === 'ABIERTA').length}
            colorClass="green"
          />
          <StatCard
            icon="👥"
            label="Usuarios del Sistema"
            value={loading ? '...' : usuarios.length}
            colorClass="blue"
          />
          <StatCard
            icon="🎓"
            label="Docentes"
            value={loading ? '...' : usuarios.filter(u => u.rol === 'DOCENTE').length}
            colorClass="purple"
          />
        </div>

        <div className="grid-2">
          {/* Período Activo */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3>📅 Período Académico Activo</h3>
              {periodo && <Badge value={periodo.estado} dot />}
            </div>
            {loading ? (
              <p className="text-muted text-sm">Cargando...</p>
            ) : !periodo ? (
              <div className="empty-state">
                <span className="empty-state-icon">📅</span>
                <span className="empty-state-title">Sin período activo</span>
                <span className="empty-state-text">Crea un nuevo período académico para comenzar</span>
              </div>
            ) : (
              <>
                <div className="info-grid mb-4">
                  <div className="info-item">
                    <div className="info-label">Nombre</div>
                    <div className="info-value">{periodo.nombre_periodo}</div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Estado</div>
                    <div className="info-value"><Badge value={periodo.estado} /></div>
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

                {/* Stepper de estado */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {ESTADOS_PERIODO.map((est, i) => (
                    <div key={est} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                      }}>
                        <div style={{
                          width: 28, height: 28, borderRadius: '50%',
                          background: i < estadoIdx ? 'var(--success)' : i === estadoIdx ? 'var(--accent-500)' : 'var(--bg-hover)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.7rem', color: i <= estadoIdx ? '#fff' : 'var(--text-muted)',
                          fontWeight: 700,
                        }}>
                          {i < estadoIdx ? '✓' : i + 1}
                        </div>
                        <span style={{ fontSize: '0.65rem', color: i === estadoIdx ? 'var(--accent-400)' : 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {est.replace('_', ' ')}
                        </span>
                      </div>
                      {i < ESTADOS_PERIODO.length - 1 && (
                        <div style={{ width: 30, height: 2, background: i < estadoIdx ? 'var(--success)' : 'var(--border)', marginBottom: 16 }} />
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Accesos Rápidos */}
          <div className="card">
            <h3 style={{ marginBottom: 16 }}>⚡ Accesos Rápidos</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: '📅', label: 'Gestionar Períodos', sub: 'Crear y transicionar períodos', to: '/admin/periodos' },
                { icon: '📖', label: 'Oferta Académica', sub: 'Planes, cursos y secciones', to: '/admin/oferta' },
                { icon: '👥', label: 'Usuarios', sub: 'Docentes y alumnos', to: '/admin/usuarios' },
                { icon: '🔒', label: 'Cierre Académico', sub: 'Cerrar actas y período', to: '/admin/cierre' },
              ].map(item => (
                <a
                  key={item.to}
                  href={item.to}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '12px', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', textDecoration: 'none',
                    transition: 'all var(--transition)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-500)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                >
                  <span style={{ fontSize: '1.3rem' }}>{item.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.sub}</div>
                  </div>
                  <span style={{ color: 'var(--text-muted)' }}>→</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
