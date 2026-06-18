import api from './api'

export const authService = {
  login: (email, password, dominio_tenant) =>
    api.post('/auth/login', { email, password, dominio_tenant }).then(r => r.data),

  logout: () =>
    api.post('/auth/logout').then(r => r.data).catch(() => {}),

  me: () =>
    api.get('/auth/me').then(r => r.data),
}
