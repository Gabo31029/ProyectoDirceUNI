import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import Modal from '../../components/Modal'
import DataTable from '../../components/DataTable'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { tenantService } from '../../services/tenantService'

const TABS = ['Escalas', 'Tipos Evaluación', 'Tipos Condición', 'Tipos Evento']
const ADD_LABELS = ['Nueva Escala', 'Nuevo Tipo de Evaluación', 'Nuevo Tipo de Condición', 'Nuevo Tipo de Evento']

export default function CatalogosPage() {
  const [activeTab, setActiveTab] = useState(0)
  const [tenants, setTenants] = useState([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    tenantService.listar().then(list => {
      setTenants(list)
      if (list.length > 0) setSelectedTenant(list[0].id)
    }).catch(() => { })
  }, [])

  useEffect(() => {
    if (!selectedTenant) return
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTenant, activeTab])

  const loadData = async () => {
    if (!selectedTenant) return
    setLoading(true)
    setError('')
    try {
      let result = []
      if (activeTab === 0) result = await tenantService.listarEscalas(selectedTenant)
      else if (activeTab === 1) result = await tenantService.listarTiposEvaluacion(selectedTenant)
      else if (activeTab === 2) result = await tenantService.listarTiposCondicion(selectedTenant)
      else if (activeTab === 3) result = await tenantService.listarTiposEvento(selectedTenant)
      setData(result)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar datos')
      setData([])
    } finally {
      setLoading(false)
    }
  }

  const openCreate = () => {
    setForm({})
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (activeTab === 0) await tenantService.crearEscala(selectedTenant, form)
      else if (activeTab === 1) await tenantService.crearTipoEvaluacion(selectedTenant, form)
      else if (activeTab === 2) await tenantService.crearTipoCondicion(selectedTenant, form)
      else if (activeTab === 3) await tenantService.crearTipoEvento(selectedTenant, form)
      setSuccess('Ítem creado correctamente')
      setShowModal(false)
      loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const getColumns = () => {
    if (activeTab === 0) return [
      { accessor: 'nombre_escala', header: 'Nombre Escala', primary: true },
      { accessor: 'nota_minima', header: 'Nota Mínima' },
      { accessor: 'nota_maxima', header: 'Nota Máxima' },
      { accessor: 'nota_aprobatoria', header: 'Nota Aprobatoria' },
    ]
    if (activeTab === 3) return [
      { accessor: 'codigo', header: 'Código', primary: true },
      { accessor: 'nombre', header: 'Nombre' },
      { accessor: 'cuenta_objetivo', header: 'Cuenta Objetivo' },
      { accessor: 'operacion', header: 'Operación' },
    ]
    return [
      { accessor: 'codigo', header: 'Código', primary: true },
      { accessor: 'nombre', header: 'Nombre' },
      { accessor: 'descripcion', header: 'Descripción' },
    ]
  }

  const renderFormFields = () => {
    if (activeTab === 0) return (
      <>
        <div className="form-group">
          <label className="form-label" htmlFor="escala-nombre">Nombre de la escala</label>
          <input id="escala-nombre" className="form-input" value={form.nombre_escala || ''} onChange={e => setForm({ ...form, nombre_escala: e.target.value })} required />
        </div>
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="escala-min">Nota mínima</label>
            <input id="escala-min" type="number" className="form-input" value={form.nota_minima ?? ''} onChange={e => setForm({ ...form, nota_minima: e.target.value === '' ? '' : parseFloat(e.target.value) })} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="escala-max">Nota máxima</label>
            <input id="escala-max" type="number" className="form-input" value={form.nota_maxima ?? ''} onChange={e => setForm({ ...form, nota_maxima: e.target.value === '' ? '' : parseFloat(e.target.value) })} required />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="escala-aprob">Nota aprobatoria</label>
          <input id="escala-aprob" type="number" className="form-input" value={form.nota_aprobatoria ?? ''} onChange={e => setForm({ ...form, nota_aprobatoria: e.target.value === '' ? '' : parseFloat(e.target.value) })} required />
        </div>
      </>
    )
    return (
      <>
        <div className="form-group">
          <label className="form-label" htmlFor="catalogo-codigo">Código</label>
          <input id="catalogo-codigo" className="form-input" value={form.codigo || ''} onChange={e => setForm({ ...form, codigo: e.target.value })} required />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="catalogo-nombre">Nombre</label>
          <input id="catalogo-nombre" className="form-input" value={form.nombre || ''} onChange={e => setForm({ ...form, nombre: e.target.value })} required />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="catalogo-desc">Descripción</label>
          <input id="catalogo-desc" className="form-input" value={form.descripcion || ''} onChange={e => setForm({ ...form, descripcion: e.target.value })} />
        </div>
        {activeTab === 3 && (
          <>
            <div className="form-group">
              <label className="form-label" htmlFor="evento-cuenta">Cuenta objetivo</label>
              <select id="evento-cuenta" className="form-select" value={form.cuenta_objetivo || ''} onChange={e => setForm({ ...form, cuenta_objetivo: e.target.value || null })}>
                <option value="">Sin cuenta objetivo</option>
                <option value="CTA-DESAPROBACIONES">Cursos Desaprobados (CTA-DESAPROBACIONES)</option>
                <option value="CTA-CREDITOS-APROBADOS">Créditos Aprobados (CTA-CREDITOS-APROBADOS)</option>
                <option value="CTA-CREDITOS-INSCRITOS">Créditos Inscritos (CTA-CREDITOS-INSCRITOS)</option>
                <option value="CTA-RESERVAS-MATRICULA">Reservas de Matrícula (CTA-RESERVAS-MATRICULA)</option>
                <option value="CTA-CONDICION-ACADEMICA">Condición Académica (CTA-CONDICION-ACADEMICA)</option>
                <option value="CTA-PROMEDIO-SNAPSHOT">Snapshot de Promedio (CTA-PROMEDIO-SNAPSHOT)</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="evento-op">Operación</label>
              <select id="evento-op" className="form-select" value={form.operacion || ''} onChange={e => setForm({ ...form, operacion: e.target.value })}>
                <option value="">Sin operación</option>
                <option value="INCREMENTO">INCREMENTO</option>
                <option value="DECREMENTO">DECREMENTO</option>
                <option value="ASIGNACION">ASIGNACION</option>
              </select>
            </div>
          </>
        )}
      </>
    )
  }

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Catálogos Institucionales</h1>
            <p className="page-subtitle">Escalas, tipos de evaluación, condición y evento</p>
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <select
              id="select-tenant-catalogos"
              className="form-select"
              value={selectedTenant}
              onChange={e => setSelectedTenant(e.target.value)}
              style={{ minWidth: 220 }}
            >
              {tenants.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
            </select>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <div className="tabs">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              id={`tab-catalogo-${i}`}
              className={`tab-btn${activeTab === i ? ' active' : ''}`}
              onClick={() => setActiveTab(i)}
            >
              {tab}
            </button>
          ))}
        </div>

        <DataTable
          title={TABS[activeTab]}
          columns={getColumns()}
          data={data}
          loading={loading}
          onAdd={selectedTenant ? openCreate : undefined}
          addLabel={ADD_LABELS[activeTab]}
        />

        {showModal && (
          <Modal
            title={`Nuevo — ${TABS[activeTab]}`}
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-catalogo" className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Guardando...' : 'Crear'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            {renderFormFields()}
          </Modal>
        )}
      </div>
    </Layout>
  )
}
