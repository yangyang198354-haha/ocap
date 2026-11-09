// PHASE_09 E2E（替代口径：jsdom 中挂载真实页面 + 真实 store/api/http，uni.request 由“带状态的假服务端”应答）
// 溯源：US-075/077/078/079/086 小程序旅程；AC-075-01、AC-077-01/02、AC-078-02/03、AC-079-02、AC-086-01/02
import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mountPage } from './helpers.js'
import Login from '../pages/login/index.vue'
import Me from '../pages/me/index.vue'
import { useThemeStore } from '@/store/theme'

let accounts
function installServer() {
  const who = (header) => Object.values(accounts).find((a) => `Bearer ${a.token}` === header?.Authorization)
  uni.request.mockImplementation(({ url, method, data, header, success }) => {
    const path = url.replace(/^\/api\/v1/, '')
    const ok = (body) => success({ statusCode: 200, data: body })
    if (method === 'POST' && path === '/auth/login/password') {
      const a = accounts[data.identifier]
      return a ? ok({ token: a.token, user: { id: a.id }, is_new: false }) : success({ statusCode: 401, data: { code: 'LOGIN_FAILED', message: '账号或密码错误' } })
    }
    const me = who(header)
    if (!me) return success({ statusCode: 401, data: { code: 'UNAUTHORIZED', message: '请先登录' } })
    if (method === 'GET' && path === '/me') return ok({ profile: { id: me.id, nickname: `用户${me.id}`, phone: '138****0000' }, identities: { labels: ['户主'] } })
    if (method === 'GET' && path === '/me/theme') return ok({ theme: me.theme })
    if (method === 'PUT' && path === '/me/theme') { me.theme = data.theme; return ok({ theme: data.theme }) }
    if (method === 'GET' && path === '/ledger/reports') return ok({ results: [] })
    return success({ statusCode: 404, data: { code: 'NOT_FOUND', message: path } })
  })
}
async function loginAs(identifier) {
  const { wrapper } = await mountPage(Login, { token: '' })
  wrapper.vm.mode = 'password'
  wrapper.vm.identifier = identifier
  wrapper.vm.password = 'pw'
  await wrapper.vm.loginPassword()
  await flushPromises()
  return wrapper
}
const freshApp = () => setActivePinia(createPinia()) // 模拟重新打开小程序：store 从设备存储重建

beforeEach(() => {
  accounts = {
    alice: { id: 1, token: 'TA', theme: null },
    bob: { id: 2, token: 'TB', theme: null },
    carol: { id: 3, token: 'TC', theme: 'terminal' }
  }
  installServer()
})

describe('TC-E2E-201 小程序旅程', () => {
  it('默认 B → 选 A → 重启沿用 → 退出后登录页沿用 → 他人登录不串号', async () => {
    // 首次打开：登录页 B
    let { wrapper } = await mountPage(Login, { token: '' })
    expect(wrapper.find('.theme-root').classes()).toContain('theme-bento')
    // alice 登录（账号从未选择）→ B，已跳转首页
    await loginAs('alice')
    expect(useThemeStore().current).toBe('bento')
    expect(uni.reLaunch).toHaveBeenLastCalledWith({ url: '/pages/index/index' })
    // “我的”页选择 A
    ;({ wrapper } = await mountPage(Me, { token: 'TA' }))
    await wrapper.find('[data-theme-key=neon]').trigger('click')
    await flushPromises()
    expect(accounts.alice.theme).toBe('neon')
    expect(wrapper.find('.theme-root').classes()).toContain('theme-neon')
    // 退出登录后登录页仍是 A（本设备记忆）
    await wrapper.findAll('button').find((b) => b.text().includes('退出登录')).trigger('click')
    freshApp()
    ;({ wrapper } = await mountPage(Login, { token: '' }))
    expect(wrapper.find('.theme-root').classes()).toContain('theme-neon')
    // bob 在同一设备登录（账号从未选择）→ B；alice 的账号值不变
    await loginAs('bob')
    expect(useThemeStore().current).toBe('bento')
    expect(accounts.alice.theme).toBe('neon')
  })
  it('换设备：空设备记忆登录 carol → terminal；账号值已下线 → B 并可重选', async () => {
    await loginAs('carol')
    expect(useThemeStore().current).toBe('terminal')
    uni.setStorageSync('ocap_theme', '')
    accounts.alice.theme = 'retired-d'
    freshApp()
    await loginAs('alice')
    expect(useThemeStore().current).toBe('bento')
    const { wrapper } = await mountPage(Me, { token: 'TA' })
    expect(wrapper.findAll('.theme-option')).toHaveLength(3)
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(accounts.alice.theme).toBe('terminal')
    expect(wrapper.find('.theme-root').classes()).toContain('theme-terminal')
  })
})
