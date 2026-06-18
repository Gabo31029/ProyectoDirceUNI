import api from './api'

export const tenantService = {
  listar: () => api.get('/tenants').then(r => r.data),
  crear: (data) => api.post('/tenants', data).then(r => r.data),
  obtener: (id) => api.get(`/tenants/${id}`).then(r => r.data),
  actualizar: (id, data) => api.put(`/tenants/${id}`, data).then(r => r.data),

  // Catálogos
  listarEscalas: (tenantId) => api.get(`/tenants/${tenantId}/catalogos/escalas-evaluacion`).then(r => r.data),
  crearEscala: (tenantId, data) => api.post(`/tenants/${tenantId}/catalogos/escalas-evaluacion`, data).then(r => r.data),

  listarTiposComponente: (tenantId) => api.get(`/tenants/${tenantId}/catalogos/tipos-componente`).then(r => r.data),
  crearTipoComponente: (tenantId, data) => api.post(`/tenants/${tenantId}/catalogos/tipos-componente`, data).then(r => r.data),

  listarTiposCondicion: (tenantId) => api.get(`/tenants/${tenantId}/catalogos/tipos-condicion`).then(r => r.data),
  crearTipoCondicion: (tenantId, data) => api.post(`/tenants/${tenantId}/catalogos/tipos-condicion`, data).then(r => r.data),

  listarTiposEvento: (tenantId) => api.get(`/tenants/${tenantId}/catalogos/tipos-evento`).then(r => r.data),
  crearTipoEvento: (tenantId, data) => api.post(`/tenants/${tenantId}/catalogos/tipos-evento`, data).then(r => r.data),
}
