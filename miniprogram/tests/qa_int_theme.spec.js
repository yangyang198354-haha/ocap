// PHASE_08 集成测试（ocap_ui_theme / 小程序）：真实页面 + 真实 store + 真实 utils/api.js + 真实 http.js，仅替换 uni 桩
// 溯源：AC-075-01、AC-077-01/02/04、AC-078-03、AC-079-01/02/03、AC-083-03、AC-086-01/02、AC-090-03
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mountPage, respondWith, requests } from './helpers.js'
import Login from '../pages/login/index.vue'
import Me from '../pages/me/index.vue'
import { useThemeStore } from '@/store/theme'

const ME = { profile: { id: 1, nickname: '张三', phone: '138****0000' }, identities: { labels: ['户主'] } }

async function loginWith(account, device) {
  if (device) uni.setStorageSync('ocap_theme', device)
  respondWith({
    'POST /auth/login/password': { token: 'T', user: { id: 1 }, is_new: false },
    'GET /me': ME,
    'GET /me/theme': () => (account instanceof Error ? undefined : { theme: account })
  })
  if (account instanceof Error) {
    // 偏好读取失败：令该路径返回 500
    const base = uni.request.getMockImplementation()
    uni.request.mockImplementation((opt) => (opt.url.endsWith('/me/theme') ? opt.success({ statusCode: 500, data: { code: 'X', message: 'err' } }) : base(opt)))
  }
  const { wrapper } = await mountPage(Login, { token: '' })
  wrapper.vm.mode = 'password'
  wrapper.vm.identifier = 'acc'
  wrapper.vm.password = 'pw'
  await wrapper.vm.loginPassword()
  await flushPromises()
  return wrapper
}

describe('TC-INT-201 登录后对账（AC-075-01、AC-077-02、AC-086-01、AC-090-03）', () => {
  it('账号值优先：设备记忆 terminal、账号 neon → neon；对账发生在 reLaunch 之前，且带 Authorization', async () => {
    await loginWith('neon', 'terminal')
    expect(useThemeStore().current).toBe('neon')
    expect(uni.getStorageSync('ocap_theme')).toBe('neon')
    const reqs = requests()
    const idx = reqs.findIndex((r) => r.path === '/me/theme')
    expect(idx).toBeGreaterThan(-1)
    expect(reqs[idx].method).toBe('GET')
    expect(reqs[idx].header.Authorization).toBe('Bearer T')
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/index/index' })
    expect(uni.reLaunch.mock.invocationCallOrder[0]).toBeGreaterThan(uni.request.mock.invocationCallOrder[idx])
  })
  it('账号值 null → bento（并覆盖设备记忆）', async () => {
    await loginWith(null, 'terminal')
    expect(useThemeStore().current).toBe('bento')
    expect(uni.getStorageSync('ocap_theme')).toBe('bento')
  })
  it('账号值已下线 → bento，仍正常跳转', async () => {
    await loginWith('retired-d', 'neon')
    expect(useThemeStore().current).toBe('bento')
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/index/index' })
  })
  it('偏好读取失败 → 保持设备记忆风格并跳转', async () => {
    await loginWith(new Error('boom'), 'terminal')
    expect(useThemeStore().current).toBe('terminal')
    expect(uni.getStorageSync('ocap_theme')).toBe('terminal')
    expect(uni.reLaunch).toHaveBeenCalled()
  })
})

describe('TC-INT-202 登录页（AC-079-01/02/03、AC-083-03）', () => {
  it('无设备记忆 → B；有记忆 terminal → terminal；页面没有任何风格入口', async () => {
    respondWith({})
    let { wrapper } = await mountPage(Login, { token: '' })
    expect(wrapper.find('.theme-root').classes()).toContain('theme-bento')
    expect(wrapper.find('.theme-option').exists()).toBe(false)
    uni.setStorageSync('ocap_theme', 'terminal')
    ;({ wrapper } = await mountPage(Login, { token: '' }))
    expect(wrapper.find('.theme-root').classes()).toContain('theme-terminal')
    expect(wrapper.find('.theme-option').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('界面风格')
  })
  it('设备记忆已下线 → B', async () => {
    uni.setStorageSync('ocap_theme', 'retired-d')
    const { wrapper } = await mountPage(Login, { token: '' })
    expect(wrapper.find('.theme-root').classes()).toContain('theme-bento')
  })
})

describe('TC-INT-203 “我的”页风格选择（AC-074-01、AC-077-01/04、AC-086-02）', () => {
  const base = { 'GET /me': ME, 'GET /ledger/reports': { results: [] } }
  it('默认（无记忆）B 选中，列表恰为 3 项且名称依次正确；来回切换发出 PUT /me/theme {theme}', async () => {
    respondWith({ ...base, 'PUT /me/theme': (d) => ({ theme: d.theme }) })
    const { wrapper } = await mountPage(Me)
    expect(wrapper.findAll('.theme-option').map((o) => o.find('.theme-name').text())).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端'])
    expect(wrapper.find('[data-theme-key=bento]').classes()).toContain('is-selected')
    for (const key of ['neon', 'terminal', 'neon']) {
      await wrapper.find(`[data-theme-key=${key}]`).trigger('click')
      await flushPromises()
      expect(wrapper.find('.theme-root').classes()).toContain(`theme-${key}`)
      expect(wrapper.findAll('.theme-option.is-selected')).toHaveLength(1)
    }
    const puts = requests().filter((r) => r.method === 'PUT')
    expect(puts.map((p) => [p.path, p.data])).toEqual([
      ['/me/theme', { theme: 'neon' }], ['/me/theme', { theme: 'terminal' }], ['/me/theme', { theme: 'neon' }]
    ])
    expect(puts[0].header.Authorization).toBe('Bearer tok')
    expect(uni.setTabBarStyle).toHaveBeenCalled()
  })
  it('设备记忆已下线 → 选中 B；列表不含下线风格', async () => {
    uni.setStorageSync('ocap_theme', 'retired-d')
    respondWith(base)
    const { wrapper } = await mountPage(Me)
    expect(wrapper.find('[data-theme-key=bento]').classes()).toContain('is-selected')
    expect(wrapper.find('[data-theme-key=retired-d]').exists()).toBe(false)
  })
  it('保存失败：toast“保存失败”，回滚到保存前的风格与设备记忆', async () => {
    uni.setStorageSync('ocap_theme', 'neon')
    respondWith(base)
    const { wrapper } = await mountPage(Me)
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(uni.showToast).toHaveBeenCalledWith(expect.objectContaining({ title: '保存失败' }))
    expect(wrapper.find('[data-theme-key=neon]').classes()).toContain('is-selected')
    expect(uni.getStorageSync('ocap_theme')).toBe('neon')
  })
  it('退出登录保留设备记忆（AC-079-02）', async () => {
    uni.setStorageSync('ocap_theme', 'terminal')
    respondWith(base)
    const { wrapper } = await mountPage(Me)
    await wrapper.findAll('button').find((b) => b.text().includes('退出登录')).trigger('click')
    expect(uni.getStorageSync('ocap_token')).toBeFalsy()
    expect(uni.getStorageSync('ocap_theme')).toBe('terminal')
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/login/index' })
    setActivePinia(createPinia())
    expect(useThemeStore().current).toBe('terminal')
  })
})
