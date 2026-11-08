// HTTP 层替身：api.js 保持真实实现，仅替换 axios 客户端 `@/shared/http`
import { vi } from 'vitest'

function client() {
  return { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() }
}

export function createHttpMock() {
  return {
    http: client(),
    adminHttp: client(),
    TOKEN_KEY: 'ocap_token',
    ADMIN_TOKEN_KEY: 'ocap_admin_token',
    getToken: (admin = false) => localStorage.getItem(admin ? 'ocap_admin_token' : 'ocap_token') || '',
    setToken: (token, admin = false) => {
      const key = admin ? 'ocap_admin_token' : 'ocap_token'
      if (token) localStorage.setItem(key, token)
      else localStorage.removeItem(key)
    }
  }
}
