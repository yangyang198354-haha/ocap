import { defineStore } from 'pinia'
import { authApi, meApi } from '@/shared/api'
import { getToken, setToken } from '@/shared/http'

// 并发去重：布局与页面同时需要 /me 时只发一次请求，缩短首屏身份等待
let mePending = null

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), me: null, loading: false }),
  getters: {
    isLogin: (s) => Boolean(s.token),
    // /me 的 identities 是对象 { is_guest, units, committee, labels }（module_design IFC-070）
    identities: (s) => s.me?.identities?.labels || [],
    position: (s) => s.me?.identities?.committee?.position || '',
    // 业委会成员：主任、副主任、委员（业主代表不是业委会成员）
    isCommittee: (s) => ['CHAIR', 'VICE_CHAIR', 'MEMBER'].includes(s.me?.identities?.committee?.position),
    // 业主代表：仅 REPRESENTATIVE（MOD-215 / IFC-436，与 CommitteeQuery.is_representative 同口径）
    isRepresentative: (s) => s.me?.identities?.committee?.position === 'REPRESENTATIVE',
    // 户主/产权业主房屋（HEAD/OWNER）；用于“待我处理”与是否请求 /me/housing
    ownerUnits: (s) => (s.me?.identities?.units || []).filter((u) => u.role === 'HEAD' || u.role === 'OWNER'),
    hasOwnerUnit() { return this.ownerUnits.length > 0 },
    // 同住人房屋；与产权业主同版式（REQ-FUNC-367）
    residentUnits: (s) => (s.me?.identities?.units || []).filter((u) => u.role === 'RESIDENT'),
    hasResidentUnit() { return this.residentUnits.length > 0 },
    // 游客：无任何房屋与席位（/me 的 is_guest 口径）
    isGuest: (s) => Boolean(s.me?.identities?.is_guest),
    // 汇总身份（IFC-262 / IFC-282）：与管理端注册用户目录同口径
    // 无 summary 时回退到单一身份 labels（C-34：labels 恒为单元素，与 summary 同口径）
    identitySummary: (s) => s.me?.identities?.summary ?? { code: 'GUEST', label: (s.me?.identities?.labels || []).join('、') || '游客' },
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
      if (mePending) return mePending
      this.loading = true
      const request = meApi.me()
      mePending = request
      try {
        this.me = await request
        return this.me
      } finally {
        mePending = null
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
