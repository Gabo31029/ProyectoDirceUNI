import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorAlert from '../../components/ErrorAlert'
import Icon from '../../components/Icon'
import { historialService } from '../../services/historialService'
import { useAuth } from '../../context/AuthContext'

export default function HistorialPage() {
  const { auth } = useAuth()
  const [historial, setHistorial] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [selectedPeriodId, setSelectedPeriodId] = useState('')
  const [expandedCourses, setExpandedCourses] = useState({})

  useEffect(() => {
    if (!auth?.id) return
    historialService.obtener(auth.id)
      .then(data => {
        setHistorial(data)
        if (data?.periodos?.length > 0) {
          // Set latest period as default selected
          setSelectedPeriodId(data.periodos[data.periodos.length - 1].id_periodo)
        }
      })
      .catch(e => setError(e.response?.data?.detail || 'No se pudo cargar el historial académico'))
      .finally(() => setLoading(false))
  }, [auth?.id])

  const handleDownloadPDF = async () => {
    setDownloading(true)
    try {
      await historialService.descargarPDF(auth.id)
    } catch {
      setError('Error al descargar el récord de notas')
    } finally {
      setDownloading(false)
    }
  }

  const toggleCourse = (idInscripcion) => {
    setExpandedCourses(prev => ({
      ...prev,
      [idInscripcion]: !prev[idInscripcion]
    }))
  }

  const selectedPeriod = historial?.periodos?.find(p => p.id_periodo === selectedPeriodId)

  return (
    <Layout>
      <div className="page-container">
        <div className="page-head">
          <div className="ph-l">
            <h1 className="h1">Historial Académico</h1>
            <p className="ph-sub">Registro de notas, promedios y condición académica</p>
          </div>
          <div className="page-actions">
            <button
              id="btn-download-pdf"
              className="btn btn-secondary"
              onClick={handleDownloadPDF}
              disabled={downloading || !historial}
            >
              {downloading ? 'Descargando…' : 'Descargar Récord PDF'}
            </button>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />

        {loading ? (
          <LoadingSpinner text="Cargando historial académico…" />
        ) : !historial ? (
          <div className="card card-pad">
            <div className="empty">
              <div className="empty-ic"><Icon name="graduation-cap" size={32} style={{ color: 'var(--ink-4)' }} /></div>
              <div className="empty-title">Sin historial académico</div>
              <div className="empty-sub">Aún no tienes períodos académicos completados</div>
            </div>
          </div>
        ) : (
          <>
            {/* Resumen Global */}
            {historial.resumen && (
              <div className="stat-grid" style={{ marginBottom: 24 }}>
                <StatCard icon={<Icon name="bar-chart" size={18} />} label="PPA Acumulado" value={historial.resumen.ppa?.toFixed(2) ?? '—'} colorClass="indigo" />
                <StatCard icon={<Icon name="check-circle" size={18} />} label="Créditos Aprobados" value={historial.resumen.creditos_aprobados ?? '—'} colorClass="green" />
                <StatCard icon={<Icon name="clipboard" size={18} />} label="Condición Académica" value={historial.resumen.condicion_academica || 'Normal'} colorClass="blue" />
              </div>
            )}

            {/* Selector de Período Académico */}
            {historial.periodos && historial.periodos.length > 0 && (
              <div className="card card-pad" style={{ marginBottom: 24, background: 'var(--surface-1)', border: '1px solid var(--line)' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
                  <div>
                    <label className="form-label" style={{ fontWeight: 600, marginBottom: 6, display: 'block', fontSize: '0.9rem' }}>
                      Seleccionar Periodo Académico
                    </label>
                    <select
                      id="select-periodo-historial"
                      className="form-select"
                      value={selectedPeriodId}
                      onChange={e => setSelectedPeriodId(e.target.value)}
                      style={{ minWidth: 280 }}
                    >
                      {historial.periodos.map((p, idx) => (
                        <option key={idx} value={p.id_periodo}>
                          {p.nombre_periodo}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {selectedPeriod && (
                    <div style={{ display: 'flex', gap: 12 }}>
                      <div className="stat-card" style={{ padding: '8px 16px', background: 'var(--surface-2)', borderRadius: 'var(--r-sm)', border: '1px solid var(--line)' }}>
                        <span className="text-xs text-muted" style={{ display: 'block', textTransform: 'uppercase', letterSpacing: 0.5 }}>Promedio Periodo (PPS)</span>
                        <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)' }}>
                          {selectedPeriod.pps?.toFixed(2) ?? '—'}
                        </span>
                      </div>
                      <div className="stat-card" style={{ padding: '8px 16px', background: 'var(--surface-2)', borderRadius: 'var(--r-sm)', border: '1px solid var(--line)' }}>
                        <span className="text-xs text-muted" style={{ display: 'block', textTransform: 'uppercase', letterSpacing: 0.5 }}>Promedio Acumulado (PPA)</span>
                        <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--indigo)' }}>
                          {selectedPeriod.ppa?.toFixed(2) ?? '—'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Listado de cursos para el período seleccionado */}
            {selectedPeriod ? (
              <div className="card card-flush" style={{ marginBottom: 24 }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div className="h3" style={{ margin: 0 }}>Cursos Matriculados — {selectedPeriod.nombre_periodo}</div>
                  <Badge value={selectedPeriod.estado || 'REGISTRO_NOTAS'} dot />
                </div>
                
                <div className="tbl-wrap">
                  <table className="tbl">
                    <thead>
                      <tr>
                        <th style={{ width: '50%' }}>Curso</th>
                        <th>Créditos</th>
                        <th className="num">Nota Final / Promedio</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedPeriod.cursos || selectedPeriod.inscripciones || []).map((c, ci) => {
                        const isExpanded = expandedCourses[c.id_inscripcion]
                        const finalNota = c.nota_final ?? c.promedio_ponderado_curso
                        return (
                          <>
                            <tr 
                              key={ci} 
                              className="zebra" 
                              onClick={() => toggleCourse(c.id_inscripcion)} 
                              style={{ cursor: 'pointer', transition: 'background-color 0.2s' }}
                            >
                              <td className="cell-strong">
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                  <Icon 
                                    name={isExpanded ? "chevron-down" : "chevron-right"} 
                                    size={14} 
                                    style={{ color: 'var(--ink-3)', transition: 'transform 0.2s' }} 
                                  />
                                  <div>
                                    <span style={{ fontSize: '0.95rem' }}>{c.nombre_curso}</span>
                                    <span className="text-muted text-xs" style={{ marginLeft: 8 }}>({c.codigo_curso})</span>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span className="pill gray" style={{ fontWeight: 600 }}>{c.creditos ?? '—'} CR</span>
                              </td>
                              <td className="num" style={{ fontWeight: 700, fontSize: '1.05rem', color: finalNota >= 11 ? 'var(--green)' : 'var(--red)' }}>
                                {finalNota !== null ? finalNota.toFixed(2) : '—'}
                              </td>
                              <td>
                                <Badge value={c.estado} dot />
                              </td>
                            </tr>
                            
                            {isExpanded && (
                              <tr>
                                <td colSpan="4" style={{ backgroundColor: 'var(--surface-2)', padding: '16px 24px', borderBottom: '1px solid var(--line)' }}>
                                  <div style={{ marginBottom: 12 }}>
                                    <span className="text-xs text-muted" style={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Detalle de Evaluaciones</span>
                                  </div>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                                    {c.evaluaciones && c.evaluaciones.length > 0 ? (
                                      c.evaluaciones.map((ev, evi) => (
                                        <div 
                                          key={evi} 
                                          style={{ 
                                            flex: '1 1 220px', 
                                            background: 'var(--surface-1)', 
                                            borderRadius: 'var(--r-sm)', 
                                            padding: '12px 16px', 
                                            border: '1px solid var(--line)',
                                            boxShadow: 'var(--shadow-sm)'
                                          }}
                                        >
                                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                            <span className="text-sm font-semibold" style={{ color: 'var(--ink-1)' }}>{ev.nombre_tipo_evaluacion}</span>
                                            <span className="pill blue text-xs" style={{ padding: '2px 6px' }}>{ev.peso_relativo}%</span>
                                          </div>
                                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span className="text-xs text-muted">
                                              Estado: <Badge value={ev.estado_nota} size="sm" />
                                            </span>
                                            <span style={{ fontWeight: 700, fontSize: '1.1rem', color: ev.nota >= 11 ? 'var(--green)' : 'var(--red)' }}>
                                              {ev.nota !== null ? ev.nota.toFixed(2) : '—'}
                                            </span>
                                          </div>
                                        </div>
                                      ))
                                    ) : (
                                      <span className="text-muted text-sm">No hay evaluaciones registradas para este curso.</span>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="card card-pad">
                <div className="empty">
                  <div className="empty-ic"><Icon name="search" size={32} style={{ color: 'var(--ink-4)' }} /></div>
                  <div className="empty-title">Período no encontrado</div>
                  <div className="empty-sub">El período académico seleccionado no tiene registros</div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
