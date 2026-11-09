import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/shared/http'
import { useThemeStore } from '@/theme/store'

const routes = [
  { path: '/login', component: () => import('@/portal/Login.vue'), meta: { public: true } },
  { path: '/register', component: () => import('@/portal/Register.vue'), meta: { public: true } },
  { path: '/login/wechat', component: () => import('@/portal/WechatCallback.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/portal/PortalLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/portal/Home.vue') },
      { path: 'me', component: () => import('@/portal/Me.vue') },
      { path: 'units', component: () => import('@/portal/Units.vue') },
      { path: 'resolutions', component: () => import('@/portal/Resolutions.vue') },
      { path: 'resolutions/:id', component: () => import('@/portal/ResolutionDetail.vue') },
      { path: 'tasks', component: () => import('@/portal/Tasks.vue') },
      { path: 'claims', component: () => import('@/portal/Claims.vue') },
      { path: 'income', component: () => import('@/portal/Income.vue') },
      { path: 'polls', component: () => import('@/portal/Polls.vue') },
      { path: 'polls/:id', component: () => import('@/portal/PollDetail.vue') },
      { path: 'reports', component: () => import('@/portal/Reports.vue') }
    ]
  },
  { path: '/admin/login', component: () => import('@/admin/AdminLogin.vue'), meta: { public: true, admin: true } },
  {
    path: '/admin',
    component: () => import('@/admin/AdminLayout.vue'),
    meta: { admin: true },
    children: [
      { path: '', redirect: '/admin/registry' },
      { path: 'registry', component: () => import('@/admin/AdminRegistry.vue') },
      { path: 'appeals', component: () => import('@/admin/AdminAppeals.vue') },
      { path: 'memberships', component: () => import('@/admin/AdminMemberships.vue') },
      { path: 'seats', component: () => import('@/admin/AdminSeats.vue') },
      { path: 'flows', component: () => import('@/admin/AdminFlows.vue') },
      { path: 'finance', component: () => import('@/admin/AdminFinance.vue') },
      { path: 'users', component: () => import('@/admin/AdminUsers.vue') },
      { path: 'audit', component: () => import('@/admin/AdminAudit.vue') }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (to.meta.admin) {
    return getToken(true) ? true : '/admin/login'
  }
  return getToken() ? true : { path: '/login', query: { redirect: to.fullPath } }
})

// 风格（ADR-027/030）：管理端固定 bento；用户端按设备记忆，登录态下再与账号偏好对账
router.afterEach((to, from) => {
  const theme = useThemeStore()
  if (to.meta.admin) {
    theme.forAdminRoute()
    return
  }
  if (!theme.ready || from.meta.admin) theme.initFromDevice()
  if (getToken() && !theme.reconciled) theme.reconcileAfterLogin()
})

export default router
