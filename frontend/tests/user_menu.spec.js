// ocap_brand_layout GROUP_D（MOD-131）：PortalUserMenu / AdminUserMenu（IFC-321/326）。
// 层级：integration（真实 el-dropdown + 真实 store + 真实 api.js，仅 mock HTTP 层）。TC-INT-841 起。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus, { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import PortalUserMenu from '@/portal/PortalUserMenu.vue'
import AdminUserMenu from '@/admin/AdminUserMenu.vue'
import { useAuthStore } from '@/stores/auth'
import { useAdminThemeStore } from '@/theme/adminStore'
import { useHousingStore } from '@/stores/housing'
import { ADMIN_NAME_KEY, saveAdminName } from '@/admin/adminSession'

const { http, adminHttp } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const items = () => [...document.body.querySelectorAll('.el-dropdown-menu__item')]
const itemTexts = () => items().map((e) => e.textContent.replace(/\s+/g, '').trim())

async function mountMenu(component, { path = '/', me = null, pinia = createPinia() } = {}) {
  setActivePinia(pinia)
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }]
  })
  router.push(path)
  await router.isReady()
  if (me) useAuthStore(pinia).me = me
  const wrapper = mount(component, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
  await flush()
  return { wrapper, router, pinia }
}
const ME = (nickname) => ({ profile: { id: 1, nickname }, identities: { is_guest: true, units: [], labels: [], committee: null } })

beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  document.body.innerHTML = ''
  document.documentElement.setAttribute('data-theme', 'bento')
})
afterEach(() => { document.body.innerHTML = '' })

describe('PortalUserMenu（US-212）', () => {
  it('TC-INT-841 / AC-302-01、AC-302-02、AC-303-01：昵称"小明"显示在触发器；展开后按“个人设置→系统设置→退出登录”依次 7 项，无“手机号/我的身份与房屋”', async () => {
    localStorage.setItem('ocap_token', 'tok')
    const { wrapper } = await mountMenu(PortalUserMenu, { me: ME('小明') })
    const trigger = wrapper.find('button.user-menu-trigger')
    expect(trigger.text()).toBe('小明')
    await trigger.trigger('click')
    await flush()
    // 改写（ocap_navigation_ia REQ-FUNC-305~310）：7 项平铺 → 个人设置 5 项 + 系统设置 1 项 + 退出登录
    expect(itemTexts()).toEqual(['个人资料', '绑定手机', '设置密码', '邮箱验证', '账号注销', '界面风格', '退出登录'])
    expect(itemTexts()).not.toContain('手机号')
    expect(itemTexts()).not.toContain('我的身份与房屋')
    expect(items()).toHaveLength(7)
    expect(items().at(-1).textContent).toContain('退出登录')
    // 两个分组标题可见
    const groupTitles = [...document.body.querySelectorAll('.user-menu-group-title')].map((e) => e.textContent.trim())
    expect(groupTitles).toEqual(['个人设置', '系统设置'])
    wrapper.unmount()
  })

  it('TC-INT-842 / AC-212-01：触发方式同时含 hover 与 click（触屏仅点击亦可展开）', async () => {
    const { wrapper } = await mountMenu(PortalUserMenu, { me: ME('小明') })
    const dropdown = wrapper.findComponent({ name: 'ElDropdown' })
    expect(dropdown.props('trigger')).toEqual(['hover', 'click'])
    wrapper.unmount()
  })

  it('TC-INT-843 / AC-212-04：昵称为空显示"业主"；me 未返回同样显示"业主"；菜单项仍为 7 项可用', async () => {
    const empty = await mountMenu(PortalUserMenu, { me: ME('') })
    expect(empty.wrapper.find('.user-menu-name').text()).toBe('业主')
    expect(empty.wrapper.find('button.user-menu-trigger').attributes('title')).toBe('业主')
    expect(items()).toHaveLength(7)
    empty.wrapper.unmount()
    document.body.innerHTML = ''
    const none = await mountMenu(PortalUserMenu, { me: null })
    expect(none.wrapper.find('.user-menu-name').text()).toBe('业主')
    none.wrapper.unmount()
  })

  it('TC-INT-844 / AC-212-04：昵称超过 12 个字截断并加省略号，title 保留完整昵称；恰 12 个字不截断', async () => {
    const full = '一二三四五六七八九十甲乙丙丁'
    const long = await mountMenu(PortalUserMenu, { me: ME(full) })
    expect(long.wrapper.find('.user-menu-name').text()).toBe('一二三四五六七八九十甲乙…')
    expect(long.wrapper.find('button.user-menu-trigger').attributes('title')).toBe(full)
    long.wrapper.unmount()
    document.body.innerHTML = ''
    const exact = await mountMenu(PortalUserMenu, { me: ME('一二三四五六七八九十甲乙') })
    expect(exact.wrapper.find('.user-menu-name').text()).toBe('一二三四五六七八九十甲乙')
    exact.wrapper.unmount()
  })

  it('TC-INT-845 / AC-213-01、AC-212-05：点击菜单项进入对应独立页面（如"设置密码"→/me/password）；昵称随 auth.me 变化即时更新', async () => {
    const { wrapper, router, pinia } = await mountMenu(PortalUserMenu, { me: ME('小明') })
    items().find((e) => e.textContent.includes('设置密码')).click()
    await flush()
    expect(router.currentRoute.value.path).toBe('/me/password')
    items().find((e) => e.textContent.includes('个人资料')).click()
    await flush()
    expect(router.currentRoute.value.path).toBe('/me/profile')
    useAuthStore(pinia).me = ME('小红') // 保存资料后 fetchMe 的效果（MeProfile 保存成功即调用）
    await flush()
    expect(wrapper.find('.user-menu-name').text()).toBe('小红')
    wrapper.unmount()
  })

  it('TC-INT-846 / AC-212-03：点击"退出登录"——清除登录态、重置房屋仓库并跳 /login；此后访问 /units 无令牌', async () => {
    localStorage.setItem('ocap_token', 'tok')
    http.post.mockResolvedValue({})
    const { wrapper, router, pinia } = await mountMenu(PortalUserMenu, { me: ME('小明'), path: '/units/review' })
    const auth = useAuthStore(pinia)
    auth.token = 'tok'
    useHousingStore(pinia).prefillOwnerName = '残留'
    items().find((e) => e.textContent.includes('退出登录')).click()
    await flush()
    expect(http.post).toHaveBeenCalledWith('/auth/logout', expect.anything())
    expect(localStorage.getItem('ocap_token')).toBeNull()
    expect(auth.me).toBeNull()
    expect(useHousingStore(pinia).prefillOwnerName).toBe('')
    expect(router.currentRoute.value.path).toBe('/login')
    wrapper.unmount()
  })

  it('TC-INT-847 / AC-212-03：退出接口失败时本地仍清除登录态并回到 /login（以本地清理为准）', async () => {
    localStorage.setItem('ocap_token', 'tok')
    http.post.mockRejectedValue(new Error('offline'))
    const { wrapper, router, pinia } = await mountMenu(PortalUserMenu, { me: ME('小明') })
    useAuthStore(pinia).token = 'tok'
    items().find((e) => e.textContent.includes('退出登录')).click()
    await flush()
    expect(localStorage.getItem('ocap_token')).toBeNull()
    expect(router.currentRoute.value.path).toBe('/login')
    wrapper.unmount()
  })
})

describe('AdminUserMenu（US-226）', () => {
  const adminLogin = () => { localStorage.setItem('ocap_admin_token', 'atok'); saveAdminName('admin01') }

  it('TC-INT-848 / AC-226-01：已登录且保存过账号名——触发器显示"admin01"，刷新（重新挂载）后仍显示', async () => {
    adminLogin()
    const first = await mountMenu(AdminUserMenu)
    expect(first.wrapper.find('.user-menu-name').text()).toBe('admin01')
    first.wrapper.unmount()
    document.body.innerHTML = ''
    const again = await mountMenu(AdminUserMenu)
    expect(again.wrapper.find('.user-menu-name').text()).toBe('admin01')
    expect(again.wrapper.findComponent({ name: 'ElDropdown' }).props('trigger')).toEqual(['hover', 'click'])
    again.wrapper.unmount()
  })

  it('TC-INT-849 / AC-226-02：菜单恰 4 项——霓虹玻璃、极光 Bento、赛博终端（当前项标"已选"）、退出登录；不含个人资料类项', async () => {
    adminLogin()
    const { wrapper } = await mountMenu(AdminUserMenu)
    expect(itemTexts()).toEqual(['霓虹玻璃', '极光Bento已选', '赛博终端', '退出登录'])
    expect(items().at(-1).textContent).toContain('退出登录')
    expect(document.body.textContent).not.toMatch(/个人资料|手机号|设置密码|账号注销/)
    expect(items().filter((e) => e.textContent.includes('已选'))).toHaveLength(1)
    wrapper.unmount()
  })

  it('TC-INT-850 / AC-226-03：选"赛博终端"保存成功——PUT /admin/me/theme，管理端立即切换，"已选"移到该项；用户端设备键不被改写', async () => {
    adminLogin()
    localStorage.setItem('ocap_theme', 'neon')
    adminHttp.put.mockResolvedValue({ theme: 'terminal' })
    const { wrapper, pinia } = await mountMenu(AdminUserMenu)
    items().find((e) => e.textContent.includes('赛博终端')).click()
    await flush()
    expect(adminHttp.put).toHaveBeenCalledWith('/admin/me/theme', { theme: 'terminal' })
    expect(useAdminThemeStore(pinia).current).toBe('terminal')
    expect(localStorage.getItem('ocap_admin_theme')).toBe('terminal')
    expect(localStorage.getItem('ocap_theme')).toBe('neon')
    expect(itemTexts()).toContain('赛博终端已选')
    wrapper.unmount()
  })

  it('TC-INT-851 / AC-226-03：保存失败——提示"保存失败，已恢复原风格，请稍后重试"，风格与设备记忆回到原值', async () => {
    adminLogin()
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    adminHttp.put.mockRejectedValue(new Error('offline'))
    const { wrapper, pinia } = await mountMenu(AdminUserMenu)
    const before = useAdminThemeStore(pinia).current
    items().find((e) => e.textContent.includes('霓虹玻璃')).click()
    await flush()
    expect(error).toHaveBeenCalledWith('保存失败，已恢复原风格，请稍后重试')
    expect(useAdminThemeStore(pinia).current).toBe(before)
    expect(localStorage.getItem('ocap_admin_theme')).toBe(before)
    expect(itemTexts()).toContain('极光Bento已选')
    wrapper.unmount()
  })

  it('TC-INT-852 / AC-226-03：点击当前已选风格不发请求', async () => {
    adminLogin()
    const { wrapper } = await mountMenu(AdminUserMenu)
    items().find((e) => e.textContent.includes('极光 Bento')).click()
    await flush()
    expect(adminHttp.put).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('TC-INT-853 / AC-226-04：退出登录——清除管理端令牌与账号名，重置对账标记，跳 /admin/login；用户端令牌不受影响', async () => {
    adminLogin()
    localStorage.setItem('ocap_token', 'user-tok')
    const { wrapper, router, pinia } = await mountMenu(AdminUserMenu, { path: '/admin/registry' })
    useAdminThemeStore(pinia).reconciled = true
    items().find((e) => e.textContent.includes('退出登录')).click()
    await flush()
    expect(localStorage.getItem('ocap_admin_token')).toBeNull()
    expect(localStorage.getItem(ADMIN_NAME_KEY)).toBeNull()
    expect(localStorage.getItem('ocap_token')).toBe('user-tok')
    expect(useAdminThemeStore(pinia).reconciled).toBe(false)
    expect(router.currentRoute.value.path).toBe('/admin/login')
    wrapper.unmount()
  })

  it('TC-INT-854 / AC-226-05：无账号名记录显示"管理员"，菜单仍可用；账号名超过 12 个字截断，title 为全名', async () => {
    localStorage.setItem('ocap_admin_token', 'atok')
    const none = await mountMenu(AdminUserMenu)
    expect(none.wrapper.find('.user-menu-name').text()).toBe('管理员')
    expect(items()).toHaveLength(4)
    none.wrapper.unmount()
    document.body.innerHTML = ''
    const full = 'administrator_account_01'
    saveAdminName(full)
    const long = await mountMenu(AdminUserMenu)
    expect(long.wrapper.find('.user-menu-name').text()).toBe('administrato…')
    expect(long.wrapper.find('button.user-menu-trigger').attributes('title')).toBe(full)
    long.wrapper.unmount()
  })
})
