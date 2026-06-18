import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import Badge from '../../components/Badge'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorAlert from '../../components/ErrorAlert'
import { historialService } from '../../services/historialService'
import { useAuth } from '../../context/AuthContext'

export default function HistorialPage() {
  const { auth } = useAuth()
  const [historial, setHistorial] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    if (!auth?.id) return
    historialService.obtener(auth.id)
      .then(setHistorial)
      .catch(e => setError(e.response?.data?.detail || 'No se pudo cargar el historial académico'))
      .finally(() => setLoading(false))
  }, [auth?.id])

  const handleDownloadPDF = async () => {
    setDownloading(true)
    try {
      await historialService.descargarPDF(auth.id)
    } catch (e) {
      setError('Error al descargar el récord de notas')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Historial Académico</h1>
            <p className="page-subtitle">Registro de notas, promedios y condición académica</p>
          </div>
          <button
            id="btn-download-pdf"
            className="btn btn-secondary"
            onClick={handleDownloadPDF}
            disabled={downloading || !historial}
          >
            {downloading ? '⏳ Descargando...' : '📄 Descargar Récord PDF'}
          </button>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />

        {loading ? (
          <LoadingSpinner text="Cargando historial académico..." />
        ) : !historial ? (
          <div className="card">
            <div className="empty-state">
              <span className="empty-state-icon">🎓</span>
              <span className="empty-state-title">Sin historial académico</span>
              <span className="empty-state-text">Aún no tienes períodos académicos completados</span>
            </div>
          </div>
        ) : (
          <>
            {/* Resumen */}
            {historial.resumen && (
              <div className="grid-3 mb-6">
                <div className="stat-card">
                  <div className="stat-card-icon indigo">📊</div>
                  <div className="stat-card-info">
                    <div className="stat-card-label">PPA Acumulado</div>
                    <div className="stat-card-value">{historial.resumen.ppa ?? '—'}</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-card-icon green">✅</div>
                  <div className="stat-card-info">
                    <div className="stat-card-label">Créditos Aprobados</div>
                    <div className="stat-card-value">{historial.resumen.creditos_aprobados ?? '—'}</div>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-card-icon blue">📋</div>
                  <div className="stat-card-info">
                    <div className="stat-card-label">Condición Académica</div>
                    <div className="stat-card-value" style={{ fontSize: '1rem' }}>
                      {historial.resumen.condicion_academica
                        ? <Badge value={historial.resumen.condicion_academica} />
                        : 'Normal'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Períodos */}
            {historial.periodos ? (
              historial.periodos.map((periodo, pi) => (
                <div key={pi} className="card mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3>{periodo.nombre_periodo}</h3>
                    <div className="flex items-center gap-3">
                      {periodo.pps !== undefined && (
                        <span className="badge badge-indigo">PPS: {periodo.pps}</span>
                      )}
                      <Badge value={periodo.estado} dot />
                    </div>
                  </div>

                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Curso</th>
                        <th>Créditos</th>
                        <th>Nota Final</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(periodo.cursos || periodo.inscripciones || []).map((c, ci) => (
                        <tr key={ci}>
                          <td className="cell-primary">{c.nombre_curso || c.id_seccion || '—'}</td>
                          <td>{c.creditos ?? '—'}</td>
                          <td style={{ fontWeight: 700, color: c.nota_final >= 11 ? 'var(--success)' : 'var(--danger)' }}>
                            {c.nota_final ?? '—'}
                          </td>
                          <td><Badge value={c.estado} dot /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))
            ) : (
              /* Si el historial viene en formato diferente, mostramos los datos crudos de forma amigable */
              <div className="card">
                <h3 style={{ marginBottom: 16 }}>📋 Detalle del Historial</h3>
                <pre style={{
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  fontSize: '0.82rem',
                  color: 'var(--text-secondary)',
                  overflow: 'auto',
                  maxHeight: 400,
                }}>
                  {JSON.stringify(historial, null, 2)}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
