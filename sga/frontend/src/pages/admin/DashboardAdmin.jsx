import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import { periodoService } from '../../services/periodoService'
import { ofertaService } from '../../services/ofertaService'
import { userService } from '../../services/userService'

const FASES = ['CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO']
const FASE_LABEL = {
  CONFIGURACION:  'Configuración',
  MATRICULA:      'Matrícula',
  REGISTRO_NOTAS: 'Reg. Notas',
  CERRADO:        'Cerrado',
}

function PhaseTimeline({ estado }) {
  const idx = FASES.indexOf(estado)
  return (
    <div className="timeline" style={{ gap: 0 }}>
      {FASES.map((f, i) => (
        <div key={f} style={{ display: 'flex', alignItems: 'center', flex: i < FASES.length - 1 ? '1' : '0 0 auto' }}>
          <div className="tl-step">
            <div className={`tl-node${i < idx ? ' done' : i === idx ? ' current' : ''}`}>
              {i < idx ? '✓' : i + 1}
            </div>
            <span className={`tl-lbl${i <= idx ? ' on' : ''}`}>{FASE_LABEL[f]}</span>
          </div>
          {i < FASES.length - 1 && (
            <div className={`tl-bar${i < idx ? ' done' : ''}`} style={{ flex: 1 }} />
          )}
        </div>
      ))}
    </div>
  )
}

export default function DashboardAdmin() {
  const navigate = useNavigate()
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

  return (
    <Layout>
      <div className="page-container">
        {/* Page head */}
        <div className="page-head">
          <div className="ph-l">
            <h1 className="h1">Panel principal</h1>
            <p className="ph-sub">Vista general del período académico activo</p>
          </div>
          <div className="page-actions">
            <button className="btn btn-secondary" onClick={() => navigate('/admin/periodos')}>
              Gestionar período →
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="stat-grid" style={{ marginBottom: 24 }}>
          <StatCard icon="📅" label="Período Activo" value={loading ? '…' : (periodo?.nombre_periodo || 'Ninguno')} colorClass="indigo" />
          <StatCard icon="📖" label="Secciones Abiertas" value={loading ? '…' : secciones.filter(s => s.estado === 'ABIERTA').length} colorClass="green" />
          <StatCard icon="👥" label="Usuarios" value={loading ? '…' : usuarios.length} colorClass="blue" />
          <StatCard icon="🎓" label="Docentes" value={loading ? '…' : usuarios.filter(u => u.rol === 'DOCENTE').length} colorClass="violet" />
        </div>

        <div className="grid-2">
          {/* Período activo + timeline */}
          <div className="card card-pad">
            <div className="between" style={{ marginBottom: 18, flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div className="eyebrow">Período activo</div>
                <div className="h2" style={{ marginTop: 4 }}>
                  {loading ? '…' : (periodo?.nombre_periodo || 'Sin período')}
                </div>
                {periodo && (
                  <div className="caption" style={{ marginTop: 2 }}>
                    {periodo.fecha_inicio} – {periodo.fecha_fin}
                  </div>
                )}
              </div>
              {periodo && <Badge value={periodo.estado} dot />}
            </div>

            {periodo ? (
              <PhaseTimeline estado={periodo.estado} />
            ) : (
              <div className="empty">
                <div className="empty-ic">📅</div>
                <div className="empty-title">Sin período activo</div>
                <div className="empty-sub">Crea un nuevo período académico para comenzar</div>
              </div>
            )}
          </div>

          {/* Accesos rápidos */}
          <div className="card card-pad">
            <div className="h3" style={{ marginBottom: 14 }}>Accesos rápidos</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: '📅', label: 'Períodos académicos', sub: 'Crear y transicionar períodos', to: '/admin/periodos' },
                { icon: '📖', label: 'Oferta académica', sub: 'Planes, cursos y secciones', to: '/admin/oferta' },
                { icon: '👥', label: 'Usuarios', sub: 'Docentes y alumnos', to: '/admin/usuarios' },
                { icon: '🔒', label: 'Cierre académico', sub: 'Cerrar actas y período', to: '/admin/cierre' },
              ].map(item => (
                <button
                  key={item.to}
                  onClick={() => navigate(item.to)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '11px 14px', borderRadius: 'var(--r-sm)',
                    background: 'var(--surface-2)', border: '1px solid var(--line)',
                    color: 'var(--ink)', textDecoration: 'none', cursor: 'pointer',
                    transition: 'border-color .14s, background .14s', width: '100%', textAlign: 'left',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'var(--accent-soft)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.background = 'var(--surface-2)'; }}
                >
                  <span style={{ fontSize: '1.3rem', flexShrink: 0 }}>{item.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.label}</div>
                    <div className="caption">{item.sub}</div>
                  </div>
                  <span style={{ color: 'var(--ink-3)' }}>›</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
