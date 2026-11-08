import { defineStore } from 'pinia'
import { authApi, meApi } from '@/shared/api'
import { getToken, setToken } from '@/shared/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), me: null, loading: false }),
  getters: {
    isLogin: (s) => Boolean(s.token),
    identities: (s) => s.me?.identities || [],
    isCommittee: (s) => (s.me?.identities || []).some((x) => ['委员', '主任', '副主任'].includes(x))
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.me = user || this.me
      setToken(token)
    },
    async fetchMe() {
      if (!this.token) return null
      this.loading = true
      try {
        this.me = await meApi.me()
        return this.me
      } finally {
        this.loading = false
      }
    },
    async logout() {
      try {
        if (this.token) await authApi.logout()
      } catch (e) {
        /* 忽略登出接口异常，本地清理为准 */
      }
      this.token = ''
      this.me = null
      setToken('')
    }
  }
})
