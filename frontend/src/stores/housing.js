// MOD-123 / IFC-323：我的房屋状态仓库（侧栏角标与各分区共享同一数据源，ADR-127）。
import { defineStore } from 'pinia'
import { meApi, unitApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'

const emptyHousing = () => ({ summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 })
const listOf = (data) => data?.results || data || []

export const useHousingStore = defineStore('housing', {
  state: () => ({
    housing: emptyHousing(),
    toReview: [],
    myApplications: [],
    myAppeals: [],
    reviewLoaded: false,
    housingError: false,
    prefillOwnerName: ''
  }),
  getters: {
    // toReview 已加载 → 列表长度；否则取 /me/housing 的 pending_review_count
    pendingReviewCount: (s) => (s.reviewLoaded ? s.toReview.length : Number(s.housing.pending_review_count) || 0),
    // 是否至少是一个专有部分的有效产权业主（决定身份页底部"待我审批"卡片是否显示，仅用于展示；权限由后端 403 把关）
    ownsAnyUnit: (s) => s.housing.units.some((u) => u.role === 'HEAD' || u.role === 'OWNER')
  },
  actions: {
    async loadHousing() {
      try {
        this.housing = { ...emptyHousing(), ...(await meApi.housing()) }
        this.housingError = false
      } catch (e) {
        this.housingError = true
        throw e
      }
    },
    async loadLists() {
      const [review, applications, appeals] = await Promise.all([
        unitApi.residentApplicationsToReview(),
        unitApi.myResidentApplications(),
        unitApi.myAppeals()
      ])
      this.toReview = listOf(review)
      this.myApplications = listOf(applications)
      this.myAppeals = listOf(appeals)
      this.reviewLoaded = true
    },
    async refresh() {
      await Promise.all([this.loadHousing(), this.loadLists()])
    },
    // 静默刷新侧栏角标：仅产权业主有待审批；任何失败置 0，不提示（沿用 Home.vue 的静默策略）
    async refreshPendingBadge() {
      const units = useAuthStore().me?.identities?.units || []
      if (!units.some((u) => u.role === 'HEAD' || u.role === 'OWNER')) {
        this.housing.pending_review_count = 0
        this.reviewLoaded = false
        return
      }
      try {
        await this.loadHousing()
        this.reviewLoaded = false
      } catch (e) {
        this.housing.pending_review_count = 0
        this.reviewLoaded = false
      }
    },
    setPrefillOwnerName(name) {
      this.prefillOwnerName = typeof name === 'string' ? name : ''
    },
    consumePrefillOwnerName() {
      const name = this.prefillOwnerName
      this.prefillOwnerName = ''
      return name
    }
  }
})
