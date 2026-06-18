import api from './api'

export const periodoService = {
  listar: () => api.get('/periodos').then(r => r.data),
  activo: () => api.get('/periodos/activo').then(r => r.data),
  obtener: (id) => api.get(`/periodos/${id}`).then(r => r.data),
  crear: (data) => api.post('/periodos', data).then(r => r.data),
  transicionar: (id, estado_nuevo) => api.post(`/periodos/${id}/transicion`, { estado_nuevo }).then(r => r.data),

  // Políticas Crédito
  crearPoliticaCredito: (periodoId, data) => api.post(`/periodos/${periodoId}/politicas-credito`, data).then(r => r.data),
  listarPoliticasCredito: (periodoId) => api.get(`/periodos/${periodoId}/politicas-credito`).then(r => r.data),

  // Políticas Condición
  crearPoliticaCondicion: (periodoId, data) => api.post(`/periodos/${periodoId}/politicas-condicion`, data).then(r => r.data),
  listarPoliticasCondicion: (periodoId) => api.get(`/periodos/${periodoId}/politicas-condicion`).then(r => r.data),

  // Políticas Retiro
  crearPoliticaRetiro: (periodoId, data) => api.post(`/periodos/${periodoId}/politicas-retiro`, data).then(r => r.data),
  listarPoliticasRetiro: (periodoId) => api.get(`/periodos/${periodoId}/politicas-retiro`).then(r => r.data),

  // Políticas Reserva
  crearPoliticaReserva: (periodoId, data) => api.post(`/periodos/${periodoId}/politicas-reserva`, data).then(r => r.data),
  obtenerPoliticaReserva: (periodoId) => api.get(`/periodos/${periodoId}/politicas-reserva`).then(r => r.data),

  // Fórmulas Promedio
  crearFormula: (periodoId, data) => api.post(`/periodos/${periodoId}/formulas-promedio`, data).then(r => r.data),
  listarFormulas: (periodoId) => api.get(`/periodos/${periodoId}/formulas-promedio`).then(r => r.data),

  // Dispersión
  crearDispersion: (periodoId, data) => api.post(`/periodos/${periodoId}/politicas-dispersion`, data).then(r => r.data),
  obtenerDispersion: (periodoId) => api.get(`/periodos/${periodoId}/politicas-dispersion`).then(r => r.data),
}
