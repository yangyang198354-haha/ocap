import { defineStore } from 'pinia'
import { authApi, meApi } from '@/shared/api'
import { getToken, setToken } from '@/shared/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), me: null, loading: false }),
  getters: {
    isLogin: (s) => Boolean(s.token),
    // /me 的 identities 是对象 { is_guest, units, committee, labels }（module_design IFC-070）
    identities: (s) => s.me?.identities?.labels || [],
    position: (s) => s.me?.identities?.committee?.position || '',
    // 业委会成员：主任、副主任、委员（业主代表不是业委会成员）
    isCommittee: (s) => ['CHAIR', 'VICE_CHAIR', 'MEMBER'].includes(s.me?.identities?.committee?.position),
    isChairOrVice: (s) => ['CHAIR', 'VICE_CHAIR'].includes(s.me?.identities?.committee?.position)
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
