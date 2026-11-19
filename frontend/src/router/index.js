import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/shared/http'
import { useThemeStore } from '@/theme/store'
import { useAdminThemeStore } from '@/theme/adminStore'
import { LEGACY_UNITS_HASH } from '@/layout/menus'
import { isWideNow } from '@/layout/useBreakpoint'

// 同一组件按 section 对应多条路由：各只 import 一次（兄弟路由复用同一组件实例，ADR-119）
const UnitsPage = () => import('@/portal/Units.vue')
const ResolutionsPage = () => import('@/portal/Resolutions.vue')
const ClaimsPage = () => import('@/portal/Claims.vue')
const AdminFinancePage = () => import('@/admin/AdminFinance.vue')
const AdminUsersPage = () => import('@/admin/AdminUsers.vue')
const AdminAuditPage = () => import('@/admin/AdminAudit.vue')
const AdminAiServicesPage = () => import('@/admin/AdminAiServices.vue')

const routes = [
  { path: '/login', component: () => import('@/portal/Login.vue'), meta: { public: true } },
  { path: '/register', component: () => import('@/portal/Register.vue'), meta: { public: true } },
  { path: '/login/wechat', component: () => import('@/portal/WechatCallback.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/portal/PortalLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/portal/Home.vue') },
      // /me：宽屏进个人资料页，窄屏停在"我的"总览页（Q-BL-13/23；jsdom 无 matchMedia 时按窄屏）
      { path: 'me', component: () => import('@/portal/Me.vue'), beforeEnter: () => (isWideNow() ? { path: '/me/profile', replace: true } : true) },
      { path: 'me/style', component: () => import('@/portal/me/MeStyle.vue') },
      { path: 'me/identity', component: UnitsPage, props: { section: 'identity' } },
      { path: 'me/profile', component: () => import('@/portal/me/MeProfile.vue') },
      // MOD-162 / IFC-375：他人 profile 页（需登录，入口见各用户展示位）
      { path: 'users/:user_id(\\d+)/profile', component: () => import('@/portal/UserProfile.vue') },
      { path: 'me/phone', component: () => import('@/portal/me/MePhone.vue') },
      { path: 'me/password', component: () => import('@/portal/me/MePassword.vue') },
      { path: 'me/email', component: () => import('@/portal/me/MeEmail.vue') },
      { path: 'me/cancel', component: () => import('@/portal/me/MeCancel.vue') },
      // 旧地址 /units#appeal 重定向到对应二级页；/units#review 即身份页底部卡片（REQ-FUNC-215、ADR-133）
      {
        path: 'units',
        component: UnitsPage,
        props: { section: 'identity' },
        beforeEnter: (to) => (LEGACY_UNITS_HASH[to.hash] ? { path: LEGACY_UNITS_HASH[to.hash], replace: true } : true)
      },
      // 旧地址 /units/review → 身份页并定位到底部卡片（非产权业主无该卡片，AC-235-03）
      { path: 'units/review', redirect: { path: '/units', hash: '#review' } },
      ...['pick', 'appeal', 'applications', 'appeals'].map((section) => ({
        path: `units/${section}`, component: UnitsPage, props: { section }
      })),
      { path: 'resolutions', component: ResolutionsPage, props: { section: 'public' } },
      { path: 'resolutions/mine', component: ResolutionsPage, props: { section: 'mine' } },
      { path: 'resolutions/todo', component: ResolutionsPage, props: { section: 'todo' } },
      { path: 'resolutions/:id(\\d+)', component: () => import('@/portal/ResolutionDetail.vue') },
      { path: 'tasks', component: () => import('@/portal/Tasks.vue') },
      { path: 'claims', component: ClaimsPage, props: { section: 'mine' } },
      { path: 'claims/todo', component: ClaimsPage, props: { section: 'todo' } },
      { path: 'income', component: () => import('@/portal/Income.vue') },
      { path: 'polls', component: () => import('@/portal/Polls.vue') },
      { path: 'polls/:id', component: () => import('@/portal/PollDetail.vue') },
      { path: 'reports', component: () => import('@/portal/Reports.vue') },
      { path: 'info', component: () => import('@/portal/InfoList.vue') },
      { path: 'info/:id', component: () => import('@/portal/InfoDetail.vue') }
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
      { path: 'finance', component: AdminFinancePage, props: { section: 'claims' } },
      { path: 'finance/limit', component: AdminFinancePage, props: { section: 'limit' } },
      { path: 'users', component: AdminUsersPage, props: { section: 'admins' } },
      { path: 'users/registered', component: AdminUsersPage, props: { section: 'registered' } },
      { path: 'audit', component: AdminAuditPage, props: { section: 'config' } },
      { path: 'audit/logs', component: AdminAuditPage, props: { section: 'logs' } },
      { path: 'content/posts', component: () => import('@/admin/AdminContentPosts.vue') },
      { path: 'content/posts/:id', component: () => import('@/admin/AdminContentEditor.vue') },
      { path: 'content/styles', component: () => import('@/admin/AdminStyleTemplates.vue') },
      { path: 'content/media', component: () => import('@/admin/AdminMedia.vue') },
      { path: 'content/services', component: AdminAiServicesPage, props: { section: 'models' } },
      { path: 'content/services/prompts', component: AdminAiServicesPage, props: { section: 'prompts' } },
      { path: 'content/platforms', component: () => import('@/admin/AdminPlatforms.vue') },
      { path: 'content/settings', component: () => import('@/admin/AdminContentSettings.vue') }
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

// 风格（ADR-027/073/076）：管理端与用户端各自读取设备记忆；登录态下再与账号偏好对账
router.afterEach((to, from) => {
  if (to.meta.admin) {
    const adminTheme = useAdminThemeStore()
    adminTheme.enter()
    if (getToken(true) && !adminTheme.reconciled) adminTheme.reconcile()
    return
  }
  const theme = useThemeStore()
  if (!theme.ready || from.meta.admin) theme.initFromDevice()
  if (getToken() && !theme.reconciled) theme.reconcileAfterLogin()
})

export default router
