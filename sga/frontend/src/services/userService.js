import api from './api'

export const userService = {
  listar: (tenantId) => {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return api.get('/usuarios', { params }).then(r => r.data)
  },
  crear: (data, tenantId) => {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return api.post('/usuarios', data, { params }).then(r => r.data)
  },
  obtener: (id, tenantId) => {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return api.get(`/usuarios/${id}`, { params }).then(r => r.data)
  },
  actualizar: (id, data, tenantId) => {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return api.put(`/usuarios/${id}`, data, { params }).then(r => r.data)
  },
  desactivar: (id, confirmar = true, tenantId) => {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return api.patch(`/usuarios/${id}/desactivar`, { confirmar }, { params }).then(r => r.data)
  },
}
