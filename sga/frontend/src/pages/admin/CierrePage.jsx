import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import Modal from '../../components/Modal'
import { periodoService } from '../../services/periodoService'
import { ofertaService } from '../../services/ofertaService'

export default function CierrePage() {
  const [periodos, setPeriodos] = useState([])
  const [secciones, setSecciones] = useState([])
  const [selectedPeriodo, setSelectedPeriodo] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [confirmModal, setConfirmModal] = useState(null) // { type: 'acta'|'periodo', id, label }
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    periodoService.listar().then(list => {
      setPeriodos(list)
      const reg = list.find(p => p.estado === 'REGISTRO_NOTAS')
      if (reg) setSelectedPeriodo(reg.id)
      else if (list.length > 0) setSelectedPeriodo(list[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedPeriodo) return
    setLoading(true)
    ofertaService.listarSecciones(selectedPeriodo)
      .then(setSecciones)
      .catch(() => setSecciones([]))
      .finally(() => setLoading(false))
  }, [selectedPeriodo])

  const handleConfirm = async () => {
    setProcessing(true)
    setError('')
    try {
      if (confirmModal.type === 'acta') {
        const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/cierre/secciones/${confirmModal.id}/cerrar-acta`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${JSON.parse(localStorage.getItem('sga_auth') || '{}').token || ''}`,
          },
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Error')
        setSuccess(`Acta cerrada. Alumnos procesados: ${data.alumnos_procesados}`)
      } else if (confirmModal.type === 'periodo') {
        const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/cierre/periodos/${confirmModal.id}/cerrar`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${JSON.parse(localStorage.getItem('sga_auth') || '{}').token || ''}`,
          },
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Error')
        setSuccess(`Período cerrado exitosamente. Estado: ${data.estado}`)
      }
      setConfirmModal(null)
    } catch (e) {
      setError(e.message || 'Error en el proceso de cierre')
    } finally {
      setProcessing(false)
    }
  }

  const periodoCurrent = periodos.find(p => p.id === selectedPeriodo)

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Cierre Académico</h1>
            <p className="page-subtitle">Cierre de actas de secciones y cierre del período</p>
          </div>
          <select
            id="select-periodo-cierre"
            className="form-select"
            style={{ width: 220 }}
            value={selectedPeriodo}
            onChange={e => setSelectedPeriodo(e.target.value)}
          >
            {periodos.map(p => <option key={p.id} value={p.id}>{p.nombre_periodo} — {p.estado}</option>)}
          </select>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        {/* Cerrar Período */}
        {periodoCurrent && (
          <div className="card mb-6" style={{ borderColor: periodoCurrent.estado === 'REGISTRO_NOTAS' ? 'var(--accent-500)' : 'var(--border)' }}>
            <div className="flex items-center justify-between">
              <div>
                <h3>🔒 Cerrar Período Académico</h3>
                <p className="text-secondary text-sm" style={{ marginTop: 4 }}>
                  Calcula PPS/PPA de todos los alumnos y evalúa condiciones académicas. <strong>Acción irreversible.</strong>
                </p>
              </div>
              <button
                id="btn-cerrar-periodo"
                className="btn btn-danger"
                disabled={periodoCurrent.estado !== 'REGISTRO_NOTAS'}
                onClick={() => setConfirmModal({ type: 'periodo', id: periodoCurrent.id, label: periodoCurrent.nombre_periodo })}
              >
                🔒 Cerrar Período
              </button>
            </div>
            {periodoCurrent.estado !== 'REGISTRO_NOTAS' && (
              <p className="alert alert-info" style={{ marginTop: 12 }}>
                El período debe estar en estado <strong>REGISTRO_NOTAS</strong> para poder cerrarse.
              </p>
            )}
          </div>
        )}

        {/* Secciones */}
        <div className="table-container">
          <div className="table-header">
            <span className="table-title">Actas de Secciones — Cerrar individualmente</span>
          </div>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Cargando secciones...</div>
          ) : secciones.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state-icon">📋</span>
              <span className="empty-state-title">Sin secciones</span>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código Sección</th>
                  <th>Estado</th>
                  <th>Vacantes Máx.</th>
                  <th>Disponibles</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {secciones.map(sec => (
                  <tr key={sec.id}>
                    <td className="cell-primary">{sec.codigo_seccion}</td>
                    <td>
                      <span className={`badge ${sec.estado === 'ABIERTA' ? 'badge-success' : sec.estado === 'CERRADA' ? 'badge-muted' : 'badge-danger'}`}>
                        {sec.estado}
                      </span>
                    </td>
                    <td>{sec.vacantes_maximas}</td>
                    <td>{sec.vacantes_disponibles}</td>
                    <td>
                      <button
                        id={`btn-cerrar-acta-${sec.id}`}
                        className="btn btn-secondary btn-sm"
                        disabled={sec.estado === 'CERRADA'}
                        onClick={() => setConfirmModal({ type: 'acta', id: sec.id, label: `Sección ${sec.codigo_seccion}` })}
                      >
                        {sec.estado === 'CERRADA' ? '✅ Cerrada' : '🔒 Cerrar Acta'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Modal de confirmación */}
        {confirmModal && (
          <Modal
            title={confirmModal.type === 'acta' ? 'Cerrar Acta de Sección' : 'Cerrar Período Académico'}
            onClose={() => setConfirmModal(null)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setConfirmModal(null)}>Cancelar</button>
                <button id="btn-confirm-cierre" className="btn btn-danger" onClick={handleConfirm} disabled={processing}>
                  {processing ? 'Procesando...' : '🔒 Confirmar Cierre'}
                </button>
              </>
            }
          >
            <div className="alert alert-warning">
              <span>⚠️</span>
              <span>
                Estás a punto de cerrar <strong>{confirmModal.label}</strong>.<br />
                {confirmModal.type === 'periodo'
                  ? 'Esto calculará los promedios finales (PPS/PPA) y evaluará las condiciones académicas de todos los alumnos.'
                  : 'Esto calculará las notas finales y estados de aprobación de todos los alumnos en esta sección.'
                }<br />
                <strong>Esta operación no puede deshacerse.</strong>
              </span>
            </div>
          </Modal>
        )}
      </div>
    </Layout>
  )
}
