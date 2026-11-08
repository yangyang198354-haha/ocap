import axios from 'axios'

const BASE = import.meta.env.BASE_URL || '/'

export const TOKEN_KEY = 'ocap_token'
export const ADMIN_TOKEN_KEY = 'ocap_admin_token'

export const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export function apiUrl(path) {
  return `${API_BASE}${path}`
}

export function getToken(admin = false) {
  return localStorage.getItem(admin ? ADMIN_TOKEN_KEY : TOKEN_KEY) || ''
}

export function setToken(token, admin = false) {
  const key = admin ? ADMIN_TOKEN_KEY : TOKEN_KEY
  if (token) localStorage.setItem(key, token)
  else localStorage.removeItem(key)
}

function makeClient(admin) {
  const client = axios.create({ baseURL: API_BASE, timeout: 15000 })
  client.interceptors.request.use((config) => {
    const token = getToken(admin)
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })
  client.interceptors.response.use(
    (resp) => resp.data,
    (error) => {
      const status = error.response?.status
      const body = error.response?.data || {}
      if (status === 401) {
        setToken('', admin)
        const loginPath = admin ? `${BASE}admin/login` : `${BASE}login`
        if (!location.pathname.startsWith(loginPath)) location.href = loginPath
      }
      const err = new Error(body.message || error.message || '请求失败')
      err.code = body.code || 'NETWORK_ERROR'
      err.details = body.details || {}
      err.status = status
      throw err
    }
  )
  return client
}

export const http = makeClient(false)
export const adminHttp = makeClient(true)
