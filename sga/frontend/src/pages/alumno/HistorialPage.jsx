import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import StatCard from '../../components/StatCard'
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
    } catch {
      setError('Error al descargar el récord de notas')
    } finally {
      setDownloading(false)
    }
  }

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
              {downloading ? '⏳ Descargando…' : '📄 Descargar Récord PDF'}
            </button>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />

        {loading ? (
          <LoadingSpinner text="Cargando historial académico…" />
        ) : !historial ? (
          <div className="card card-pad">
            <div className="empty">
              <div className="empty-ic">🎓</div>
              <div className="empty-title">Sin historial académico</div>
              <div className="empty-sub">Aún no tienes períodos académicos completados</div>
            </div>
          </div>
        ) : (
          <>
            {/* Resumen */}
            {historial.resumen && (
              <div className="stat-grid" style={{ marginBottom: 24 }}>
                <StatCard icon="📊" label="PPA Acumulado" value={historial.resumen.ppa ?? '—'} colorClass="indigo" />
                <StatCard icon="✓" label="Créditos Aprobados" value={historial.resumen.creditos_aprobados ?? '—'} colorClass="green" />
                <StatCard icon="📋" label="Condición Académica" value={historial.resumen.condicion_academica || 'Normal'} colorClass="blue" />
              </div>
            )}

            {/* Períodos */}
            {historial.periodos ? (
              historial.periodos.map((per, pi) => (
                <div key={pi} className="card card-flush" style={{ marginBottom: 20 }}>
                  <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                    <div className="h3">{per.nombre_periodo}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {per.pps !== undefined && (
                        <span className="pill blue">PPS: {per.pps}</span>
                      )}
                      <Badge value={per.estado} dot />
                    </div>
                  </div>
                  <div className="tbl-wrap">
                    <table className="tbl">
                      <thead>
                        <tr>
                          <th>Curso</th>
                          <th>Créditos</th>
                          <th className="num">Nota Final</th>
                          <th>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(per.cursos || per.inscripciones || []).map((c, ci) => (
                          <tr key={ci} className="zebra">
                            <td className="cell-strong">{c.nombre_curso || c.id_seccion || '—'}</td>
                            <td>{c.creditos ?? '—'}</td>
                            <td className="num" style={{ fontWeight: 700, color: c.nota_final >= 11 ? 'var(--green)' : 'var(--red)' }}>
                              {c.nota_final ?? '—'}
                            </td>
                            <td><Badge value={c.estado} dot /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            ) : (
              <div className="card card-pad">
                <div className="h3" style={{ marginBottom: 14 }}>Detalle del Historial</div>
                <pre style={{
                  background: 'var(--surface-3)', borderRadius: 'var(--r-sm)',
                  padding: '14px', fontSize: '0.82rem', color: 'var(--ink-2)',
                  overflow: 'auto', maxHeight: 400,
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
