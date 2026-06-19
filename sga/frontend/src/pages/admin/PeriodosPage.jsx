import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { periodoService } from '../../services/periodoService'

const ESTADOS = ['CONFIGURACION', 'MATRICULA', 'REGISTRO_NOTAS', 'CERRADO']
const TABS_POLITICAS = ['Crédito', 'Condición', 'Retiro', 'Reserva', 'Fórmula', 'Dispersión']

export default function PeriodosPage() {
  const [periodos, setPeriodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showPoliticasModal, setShowPoliticasModal] = useState(false)
  const [showTransModal, setShowTransModal] = useState(false)
  const [selectedPeriodo, setSelectedPeriodo] = useState(null)
  const [politicasTab, setPoliticasTab] = useState(0)
  const [politicasData, setPoliticasData] = useState([])
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ nombre_periodo: '', fecha_inicio: '', fecha_fin: '' })
  const [polForm, setPolForm] = useState({})
  const [transEstado, setTransEstado] = useState('')

  const fetchPeriodos = async () => {
    try {
      setLoading(true)
      setPeriodos(await periodoService.listar())
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar períodos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPeriodos() }, [])

  const loadPoliticas = async (periodoId, tab) => {
    try {
      let result = []
      if (tab === 0) result = await periodoService.listarPoliticasCredito(periodoId)
      else if (tab === 1) result = await periodoService.listarPoliticasCondicion(periodoId)
      else if (tab === 2) result = await periodoService.listarPoliticasRetiro(periodoId)
      else if (tab === 3) {
        const r = await periodoService.obtenerPoliticaReserva(periodoId)
        result = r ? [r] : []
      }
      else if (tab === 4) result = await periodoService.listarFormulas(periodoId)
      else if (tab === 5) {
        const r = await periodoService.obtenerDispersion(periodoId)
        result = r ? [r] : []
      }
      setPoliticasData(result)
    } catch { setPoliticasData([]) }
  }

  const openPoliticas = async (p) => {
    setSelectedPeriodo(p)
    setPoliticasTab(0)
    await loadPoliticas(p.id, 0)
    setShowPoliticasModal(true)
    setPolForm({})
  }

  const handleTabChange = async (tab) => {
    setPoliticasTab(tab)
    if (selectedPeriodo) await loadPoliticas(selectedPeriodo.id, tab)
    setPolForm({})
  }

  const handleCrearPeriodo = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await periodoService.crear(form)
      setSuccess('Período creado exitosamente')
      setShowModal(false)
      fetchPeriodos()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al crear período')
    } finally {
      setSaving(false)
    }
  }

  const handleTransicion = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await periodoService.transicionar(selectedPeriodo.id, transEstado)
      setSuccess(`Período transicionado a ${transEstado}`)
      setShowTransModal(false)
      fetchPeriodos()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error en la transición')
    } finally {
      setSaving(false)
    }
  }

  const handleCrearPolitica = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const id = selectedPeriodo.id
      if (politicasTab === 0) await periodoService.crearPoliticaCredito(id, polForm)
      else if (politicasTab === 1) await periodoService.crearPoliticaCondicion(id, polForm)
      else if (politicasTab === 2) await periodoService.crearPoliticaRetiro(id, polForm)
      else if (politicasTab === 3) await periodoService.crearPoliticaReserva(id, polForm)
      else if (politicasTab === 4) await periodoService.crearFormula(id, polForm)
      else if (politicasTab === 5) await periodoService.crearDispersion(id, polForm)
      setSuccess('Política agregada')
      setPolForm({})
      await loadPoliticas(id, politicasTab)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar política')
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { accessor: 'nombre_periodo', header: 'Nombre Período', primary: true },
    { accessor: 'fecha_inicio', header: 'Inicio' },
    { accessor: 'fecha_fin', header: 'Fin' },
    { key: 'estado', header: 'Estado', render: r => <Badge value={r.estado} dot /> },
    { key: 'creado', header: 'Creado', render: r => new Date(r.created_at).toLocaleDateString('es-PE') },
  ]

  const nextEstado = (est) => {
    const idx = ESTADOS.indexOf(est)
    return idx < ESTADOS.length - 1 ? ESTADOS[idx + 1] : null
  }

  const renderPolForm = () => {
    const f = polForm
    const set = (k, v) => setPolForm({ ...f, [k]: v })
    if (politicasTab === 0) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-ppa-min">PPA Mínimo</label>
          <input id="pol-ppa-min" type="number" step="0.01" className="form-input" value={f.ppa_minimo || ''} onChange={e => set('ppa_minimo', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-ppa-max">PPA Máximo</label>
          <input id="pol-ppa-max" type="number" step="0.01" className="form-input" value={f.ppa_maximo || ''} onChange={e => set('ppa_maximo', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-cred-max">Créditos Máximos</label>
          <input id="pol-cred-max" type="number" className="form-input" value={f.creditos_maximos || ''} onChange={e => set('creditos_maximos', parseInt(e.target.value))} />
        </div>
      </div>
    )
    if (politicasTab === 1) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-cuenta">Cuenta Evaluada</label>
          <input id="pol-cuenta" className="form-input" value={f.cuenta_evaluada || ''} onChange={e => set('cuenta_evaluada', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-umbral">Umbral</label>
          <input id="pol-umbral" type="number" step="0.01" className="form-input" value={f.umbral || ''} onChange={e => set('umbral', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-operador">Operador</label>
          <select id="pol-operador" className="form-select" value={f.operador || ''} onChange={e => set('operador', e.target.value)}>
            <option value="">Selecciona...</option>
            {['MAYOR_QUE','MAYOR_IGUAL','IGUAL','MENOR_IGUAL','MENOR_QUE'].map(o => <option key={o} value={o}>{o.replace('_',' ')}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-accion">Acción Resultante</label>
          <input id="pol-accion" className="form-input" value={f.accion_resultante || ''} onChange={e => set('accion_resultante', e.target.value)} />
        </div>
      </div>
    )
    if (politicasTab === 2) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-tipo-ret">Tipo de Retiro</label>
          <input id="pol-tipo-ret" className="form-input" value={f.tipo_retiro || ''} onChange={e => set('tipo_retiro', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-sem-lim">Semana Límite</label>
          <input id="pol-sem-lim" type="number" className="form-input" value={f.semana_limite || ''} onChange={e => set('semana_limite', parseInt(e.target.value))} />
        </div>
      </div>
    )
    if (politicasTab === 3) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-max-cons">Máx. Períodos Consecutivos</label>
          <input id="pol-max-cons" type="number" className="form-input" value={f.max_periodos_consecutivos || ''} onChange={e => set('max_periodos_consecutivos', parseInt(e.target.value))} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-max-alt">Máx. Períodos Alternos</label>
          <input id="pol-max-alt" type="number" className="form-input" value={f.max_periodos_alternos || ''} onChange={e => set('max_periodos_alternos', parseInt(e.target.value))} />
        </div>
      </div>
    )
    if (politicasTab === 4) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-tipo-prom">Tipo de Promedio</label>
          <select id="pol-tipo-prom" className="form-select" value={f.tipo_promedio || ''} onChange={e => set('tipo_promedio', e.target.value)}>
            <option value="">Selecciona...</option>
            <option value="PPS">PPS</option>
            <option value="PPA">PPA</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-regla">Regla de Inclusión</label>
          <select id="pol-regla" className="form-select" value={f.regla_inclusion || ''} onChange={e => set('regla_inclusion', e.target.value)}>
            <option value="">Selecciona...</option>
            <option value="TODOS">TODOS</option>
            <option value="ULTIMO">ULTIMO</option>
            <option value="SOLO_APROBADOS">SOLO_APROBADOS</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-expr">Expresión de Cálculo</label>
          <input id="pol-expr" className="form-input" value={f.expresion_calculo || ''} onChange={e => set('expresion_calculo', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="pol-version">Versión</label>
          <input id="pol-version" className="form-input" value={f.version_formula || ''} onChange={e => set('version_formula', e.target.value)} />
        </div>
      </div>
    )
    if (politicasTab === 5) return (
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="pol-ciclos">Ciclos Máx. Dispersión</label>
          <input id="pol-ciclos" type="number" className="form-input" value={f.ciclos_max_dispersion || ''} onChange={e => set('ciclos_max_dispersion', parseInt(e.target.value))} />
        </div>
        <div className="form-group" style={{ justifyContent: 'center' }}>
          <label className="form-label">Prioridad Ciclo Atrasado</label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input type="checkbox" checked={!!f.prioridad_ciclo_atrasado} onChange={e => set('prioridad_ciclo_atrasado', e.target.checked)} />
            <span className="text-sm">Activar prioridad de ciclo atrasado</span>
          </label>
        </div>
      </div>
    )
    return null
  }

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Períodos Académicos</h1>
            <p className="page-subtitle">Creación, transición de estados y configuración de políticas</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <DataTable
          title="Períodos académicos"
          columns={columns}
          data={periodos}
          loading={loading}
          onAdd={() => { setShowModal(true); setForm({ nombre_periodo: '', fecha_inicio: '', fecha_fin: '' }) }}
          addLabel="Nuevo Período"
          actions={row => (
            <>
              <button
                id={`btn-politicas-${row.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => openPoliticas(row)}
              >
                Políticas
              </button>
              {nextEstado(row.estado) && (
                <button
                  id={`btn-trans-${row.id}`}
                  className="btn btn-primary btn-sm"
                  onClick={() => { setSelectedPeriodo(row); setTransEstado(nextEstado(row.estado)); setShowTransModal(true) }}
                >
                  {nextEstado(row.estado)}
                </button>
              )}
            </>
          )}
        />

        {/* Crear Período */}
        {showModal && (
          <Modal
            title="Nuevo Período Académico"
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-periodo" className="btn btn-primary" onClick={handleCrearPeriodo} disabled={saving}>
                  {saving ? 'Creando...' : 'Crear Período'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="form-group">
              <label className="form-label" htmlFor="periodo-nombre">Nombre del período</label>
              <input id="periodo-nombre" className="form-input" value={form.nombre_periodo} onChange={e => setForm({ ...form, nombre_periodo: e.target.value })} placeholder="ej: 2026-I" required />
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label" htmlFor="periodo-inicio">Fecha inicio</label>
                <input id="periodo-inicio" type="date" className="form-input" value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} required />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="periodo-fin">Fecha fin</label>
                <input id="periodo-fin" type="date" className="form-input" value={form.fecha_fin} onChange={e => setForm({ ...form, fecha_fin: e.target.value })} required />
              </div>
            </div>
          </Modal>
        )}

        {/* Transición de estado */}
        {showTransModal && selectedPeriodo && (
          <Modal
            title={`Transicionar Período`}
            onClose={() => setShowTransModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowTransModal(false)}>Cancelar</button>
                <button id="btn-confirm-trans" className="btn btn-primary" onClick={handleTransicion} disabled={saving}>
                  {saving ? 'Procesando...' : `Confirmar → ${transEstado}`}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <div className="alert alert-warning">
              <span>
                Vas a transicionar <strong>{selectedPeriodo.nombre_periodo}</strong> de{' '}
                <strong>{selectedPeriodo.estado}</strong> → <strong>{transEstado}</strong>.<br />
                Esta operación no se puede deshacer fácilmente.
              </span>
            </div>
          </Modal>
        )}

        {/* Políticas del período */}
        {showPoliticasModal && selectedPeriodo && (
          <Modal
            title={`Políticas — ${selectedPeriodo.nombre_periodo}`}
            onClose={() => setShowPoliticasModal(false)}
            size="lg"
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            <SuccessAlert message={success} onClose={() => setSuccess('')} />
            <div className="tabs" style={{ marginBottom: 16 }}>
              {TABS_POLITICAS.map((tab, i) => (
                <button
                  key={tab}
                  id={`tab-politica-${i}`}
                  className={`tab-btn${politicasTab === i ? ' active' : ''}`}
                  onClick={() => handleTabChange(i)}
                  style={{ fontSize: '0.78rem', padding: '7px 12px' }}
                >
                  {tab}
                </button>
              ))}
            </div>

            <form onSubmit={handleCrearPolitica}>
              {renderPolForm()}
              <button id="btn-add-politica" type="submit" className="btn btn-primary btn-sm" disabled={saving}>
                {saving ? 'Guardando...' : '+ Agregar política'}
              </button>
            </form>

            {politicasData.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <h4 style={{ marginBottom: 12 }}>Políticas configuradas</h4>
                {politicasData.map((p, i) => (
                  <div key={p.id || i} style={{
                    background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)',
                    padding: '12px 16px', marginBottom: 8, fontSize: '0.825rem',
                    border: '1px solid var(--border)'
                  }}>
                    {Object.entries(p).filter(([k]) => !['id','id_periodo','id_tenant','id_tipo_condicion','created_at'].includes(k)).map(([k, v]) => (
                      <span key={k} style={{ marginRight: 16, color: 'var(--text-secondary)' }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{k}:</strong> {String(v)}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </Modal>
        )}
      </div>
    </Layout>
  )
}
