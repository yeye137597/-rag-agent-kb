const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

let authToken = localStorage.getItem('token') || ''

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (authToken) headers.set('Authorization', `Bearer ${authToken}`)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || '请求失败')
  }
  return data
}

export const api = {
  setToken(token) {
    authToken = token
  },
  login(payload) {
    return request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  me() {
    return request('/api/auth/me')
  },
  listKbs() {
    return request('/api/kbs')
  },
  createKb(name) {
    return request('/api/kbs', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
  },
  uploadFiles(kbId, files) {
    const form = new FormData()
    Array.from(files).forEach((file) => form.append('files', file))
    return request(`/api/kbs/${kbId}/upload`, {
      method: 'POST',
      body: form,
    })
  },
  buildKb(kbId) {
    return request(`/api/kbs/${kbId}/build`, {
      method: 'POST',
      body: JSON.stringify({ use_cleaned: false }),
    })
  },
  buildKbWithOptions(kbId, options) {
    return request(`/api/kbs/${kbId}/build`, {
      method: 'POST',
      body: JSON.stringify(options),
    })
  },
  deleteKb(kbId) {
    return request(`/api/kbs/${kbId}`, { method: 'DELETE' })
  },
  listKbFiles(kbId) {
    return request(`/api/kbs/${kbId}/files`)
  },
  cleanKbFiles(kbId, filenames = null) {
    return request(`/api/kbs/${kbId}/clean`, {
      method: 'POST',
      body: JSON.stringify({ filenames }),
    })
  },
  chat(payload) {
    return request('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  register(payload) {
    return request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  listUsers() {
    return request('/api/users')
  },
  createUser(payload) {
    return request('/api/users', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  setUserActive(userId, isActive) {
    return request(`/api/users/${userId}/active`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: isActive }),
    })
  },
  resetUserPassword(userId, password) {
    return request(`/api/users/${userId}/password`, {
      method: 'PUT',
      body: JSON.stringify({ password }),
    })
  },
  updateUserPermissions(userId, kbIds) {
    return request(`/api/users/${userId}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({ kb_ids: kbIds }),
    })
  },
  auditLogs() {
    return request('/api/logs/audit')
  },
  queryLogs() {
    return request('/api/logs/queries')
  },
}
