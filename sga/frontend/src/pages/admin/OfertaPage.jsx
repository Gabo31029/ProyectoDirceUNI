import { useState, useEffect } from 'react'
import Layout from '../../components/Layout'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Badge from '../../components/Badge'
import ErrorAlert, { SuccessAlert } from '../../components/ErrorAlert'
import { ofertaService } from '../../services/ofertaService'
import { periodoService } from '../../services/periodoService'

const TABS = ['Planes de Estudio', 'Cursos', 'Secciones']

export default function OfertaPage() {
  const [activeTab, setActiveTab] = useState(0)
  const [planes, setPlanes] = useState([])
  const [cursos, setCursos] = useState([])
  const [secciones, setSecciones] = useState([])
  const [periodos, setPeriodos] = useState([])
  const [selectedPeriodo, setSelectedPeriodo] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState('')
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      if (activeTab === 0) setPlanes(await ofertaService.listarPlanes())
      else if (activeTab === 1) setCursos(await ofertaService.listarCursos())
      else if (activeTab === 2 && selectedPeriodo) setSecciones(await ofertaService.listarSecciones(selectedPeriodo))
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    periodoService.listar().then(list => {
      setPeriodos(list)
      if (list.length > 0) setSelectedPeriodo(list[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => { load() }, [activeTab, selectedPeriodo])

  const openModal = (type) => {
    setModalType(type)
    setForm({})
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (modalType === 'plan') {
        await ofertaService.crearPlan(form)
        setSuccess('Plan de estudios creado')
      } else if (modalType === 'curso') {
        await ofertaService.crearCurso(form)
        setSuccess('Curso creado')
      } else if (modalType === 'seccion') {
        await ofertaService.crearSeccion({ ...form, id_periodo: selectedPeriodo })
        setSuccess('Sección creada')
      }
      setShowModal(false)
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const activarPlan = async (planId) => {
    try {
      await ofertaService.activarPlan(planId)
      setSuccess('Plan activado')
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  const planesColumns = [
    { accessor: 'carrera', header: 'Carrera', primary: true },
    { accessor: 'version_plan', header: 'Versión' },
    { accessor: 'creditos_totales', header: 'Créditos Totales' },
    { key: 'estado', header: 'Estado', render: r => <Badge value={r.estado} dot /> },
  ]

  const cursosColumns = [
    { accessor: 'codigo_curso', header: 'Código', primary: true },
    { accessor: 'nombre_curso', header: 'Nombre del Curso' },
    { accessor: 'creditos', header: 'Créditos' },
    { key: 'tipo', header: 'Tipo', render: r => <Badge value={r.tipo_curso} /> },
    { accessor: 'ciclo_sugerido', header: 'Ciclo' },
  ]

  const seccionesColumns = [
    { accessor: 'codigo_seccion', header: 'Código Sección', primary: true },
    { key: 'estado', header: 'Estado', render: r => <Badge value={r.estado} dot /> },
    { accessor: 'vacantes_maximas', header: 'Vacantes Máx.' },
    { accessor: 'vacantes_disponibles', header: 'Disponibles' },
  ]

  return (
    <Layout>
      <div className="page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Oferta Académica</h1>
            <p className="page-subtitle">Planes de estudio, cursos y secciones por período</p>
          </div>
        </div>

        <ErrorAlert message={error} onClose={() => setError('')} />
        <SuccessAlert message={success} onClose={() => setSuccess('')} />

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 24 }}>
          <div className="tabs" style={{ margin: 0 }}>
            {TABS.map((tab, i) => (
              <button
                key={tab}
                id={`tab-oferta-${i}`}
                className={`tab-btn${activeTab === i ? ' active' : ''}`}
                onClick={() => setActiveTab(i)}
              >
                {tab}
              </button>
            ))}
          </div>
          {activeTab === 2 && (
            <select
              id="select-periodo-oferta"
              className="form-select"
              style={{ width: 200 }}
              value={selectedPeriodo}
              onChange={e => setSelectedPeriodo(e.target.value)}
            >
              {periodos.map(p => <option key={p.id} value={p.id}>{p.nombre_periodo}</option>)}
            </select>
          )}
        </div>

        {activeTab === 0 && (
          <DataTable
            title="Planes de Estudio"
            columns={planesColumns}
            data={planes}
            loading={loading}
            onAdd={() => openModal('plan')}
            addLabel="Nuevo Plan"
            actions={row => (
              row.estado === 'BORRADOR' && (
                <button
                  id={`btn-activar-plan-${row.id}`}
                  className="btn btn-primary btn-sm"
                  onClick={() => activarPlan(row.id)}
                >
                  ✅ Activar Plan
                </button>
              )
            )}
          />
        )}

        {activeTab === 1 && (
          <DataTable
            title="Catálogo de Cursos"
            columns={cursosColumns}
            data={cursos}
            loading={loading}
            onAdd={() => openModal('curso')}
            addLabel="Nuevo Curso"
          />
        )}

        {activeTab === 2 && (
          <DataTable
            title="Secciones del Período"
            columns={seccionesColumns}
            data={secciones}
            loading={loading}
            onAdd={() => openModal('seccion')}
            addLabel="Nueva Sección"
          />
        )}

        {showModal && (
          <Modal
            title={
              modalType === 'plan' ? 'Nuevo Plan de Estudios' :
              modalType === 'curso' ? 'Nuevo Curso' : 'Nueva Sección'
            }
            onClose={() => setShowModal(false)}
            footer={
              <>
                <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
                <button id="btn-save-oferta" className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Guardando...' : 'Crear'}
                </button>
              </>
            }
          >
            <ErrorAlert message={error} onClose={() => setError('')} />
            {modalType === 'plan' && (
              <>
                <div className="form-group">
                  <label className="form-label" htmlFor="plan-carrera">Carrera</label>
                  <input id="plan-carrera" className="form-input" value={form.carrera || ''} onChange={e => setForm({ ...form, carrera: e.target.value })} required />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="plan-version">Versión del Plan</label>
                    <input id="plan-version" className="form-input" value={form.version_plan || ''} onChange={e => setForm({ ...form, version_plan: e.target.value })} placeholder="ej: 2024" required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="plan-creditos">Créditos Totales</label>
                    <input id="plan-creditos" type="number" className="form-input" value={form.creditos_totales || ''} onChange={e => setForm({ ...form, creditos_totales: parseInt(e.target.value) })} required />
                  </div>
                </div>
              </>
            )}
            {modalType === 'curso' && (
              <>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-codigo">Código del Curso</label>
                    <input id="curso-codigo" className="form-input" value={form.codigo_curso || ''} onChange={e => setForm({ ...form, codigo_curso: e.target.value })} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-creditos">Créditos</label>
                    <input id="curso-creditos" type="number" className="form-input" value={form.creditos || ''} onChange={e => setForm({ ...form, creditos: parseInt(e.target.value) })} required />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="curso-nombre">Nombre del Curso</label>
                  <input id="curso-nombre" className="form-input" value={form.nombre_curso || ''} onChange={e => setForm({ ...form, nombre_curso: e.target.value })} required />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-tipo">Tipo</label>
                    <select id="curso-tipo" className="form-select" value={form.tipo_curso || ''} onChange={e => setForm({ ...form, tipo_curso: e.target.value })}>
                      <option value="">Selecciona...</option>
                      <option value="OBLIGATORIO">OBLIGATORIO</option>
                      <option value="ELECTIVO">ELECTIVO</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="curso-ciclo">Ciclo Sugerido</label>
                    <input id="curso-ciclo" type="number" className="form-input" value={form.ciclo_sugerido || ''} onChange={e => setForm({ ...form, ciclo_sugerido: parseInt(e.target.value) })} />
                  </div>
                </div>
              </>
            )}
            {modalType === 'seccion' && (
              <>
                <div className="form-group">
                  <label className="form-label" htmlFor="sec-curso">Seleccionar Curso</label>
                  <select id="sec-curso" className="form-select" value={form.id_curso || ''} onChange={e => setForm({ ...form, id_curso: e.target.value })}>
                    <option value="">Selecciona un curso...</option>
                    {cursos.map(c => <option key={c.id} value={c.id}>{c.codigo_curso} — {c.nombre_curso}</option>)}
                  </select>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="sec-codigo">Código de Sección</label>
                    <input id="sec-codigo" className="form-input" value={form.codigo_seccion || ''} onChange={e => setForm({ ...form, codigo_seccion: e.target.value })} placeholder="ej: A" required />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="sec-vacantes">Vacantes Máximas</label>
                    <input id="sec-vacantes" type="number" className="form-input" value={form.vacantes_maximas || ''} onChange={e => setForm({ ...form, vacantes_maximas: parseInt(e.target.value) })} required />
                  </div>
                </div>
              </>
            )}
          </Modal>
        )}
      </div>
    </Layout>
  )
}
