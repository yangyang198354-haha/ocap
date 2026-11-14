import { defineStore } from 'pinia'
import { api, setToken, getToken } from '@/utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), me: null }),
  getters: {
    // 业委会成员：主任、副主任、委员（业主代表不是成员），与接口权限一致（IFC-262 / REQ-FUNC-146）
    isCommittee: (s) => ['CHAIR', 'VICE_CHAIR', 'MEMBER'].includes(s.me?.identities?.committee?.position),
    // 汇总身份（IFC-262）：与 Web、管理端目录同口径
    identitySummary: (s) => s.me?.identities?.summary ?? { code: 'GUEST', label: '游客' }
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.me = user || null
      setToken(token)
    },
    async fetchMe() {
      if (!this.token) return null
      this.me = await api.me()
      return this.me
    },
    clear() {
      this.token = ''
      this.me = null
      setToken('')
    }
  }
})
