// TC-WEB-501~504：主页身份与认证房屋明细（US-145~147 / AC-145-01/02、AC-146-01~08、AC-147-01/02）
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import Home from '@/portal/Home.vue'

const { http } = mocked

const ME = (labels, units = []) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: labels.includes('游客'),
    units,
    committee: null,
    labels
  }
})

const UNIT_A = {
  unit_id: 107, specific_part: '1栋1单元9层902号', role: 'HEAD', role_label: '产权业主',
  unit_type: 'RESIDENCE', unit_type_label: '住宅', area: '89.50', area_display: '89.50 ㎡'
}
const UNIT_B = {
  unit_id: 108, specific_part: '2栋1单元3层301号', role: 'RESIDENT', role_label: '同住人',
  unit_type: 'APARTMENT', unit_type_label: '公寓', area: null, area_display: '未登记'
}

const others = { results: [] }

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

// 改写（ocap_identity_property GR-C-001-a，REQ-FUNC-226、AC-232-04）：主页不再有逐套明细大卡片，只保留"认证房屋"小卡片；
// 名称/类型/面积/关系的明细断言迁至"我的身份与房屋"页（见 identity_property_web.spec.js TC-WEB-901）。
const statOf = (wrapper, label) => wrapper.findAll('section.home-stat').find((s) => s.find('.label').text() === label)

describe('主页认证房屋小卡片（US-146 → US-232）', () => {
  it('TC-WEB-501 只展示数量，且可点击进入"我的身份与房屋"；不再逐套展示名称、类型、面积', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME(['产权业主'], [UNIT_A, UNIT_B]),
      '/resolutions': others,
      '/approval/tasks': others,
      '/polls': others
    }))
    const { wrapper, router } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：产权业主')
    // 旧断言：含"共 2 套"与 902/301 号、住宅/公寓/面积 → 新断言：只有数量 2，明细全部不在主页
    const card = statOf(wrapper, '认证房屋')
    expect(card.find('.stat-value').text()).toBe('2')
    expect(card.text()).toContain('已绑定的房屋数')
    expect(text).not.toContain('共 2 套')
    for (const detail of ['1栋1单元9层902号', '2栋1单元3层301号', '89.50 ㎡', '住宅', '公寓']) expect(text).not.toContain(detail)
    expect(wrapper.find('section.home-units').exists()).toBe(false)
    await card.trigger('click')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units'))
  })

  it('TC-WEB-502 游客：数量 0，空状态显示"去认证产权"链接指向认证产权页（AC-237-05）', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME(['游客']), '/resolutions': others, '/approval/tasks': others, '/polls': others
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：游客')
    // 旧断言："共 0 套"+"暂无已认证房屋" → 新断言：数量 0 + "去认证产权"链接（指向 /units/pick）
    expect(statOf(wrapper, '认证房屋').find('.stat-value').text()).toBe('0')
    const link = wrapper.findAll('a').find((a) => a.text() === '去认证产权')
    expect(link).toBeTruthy()
    expect(link.attributes('href')).toBe('/units/pick')
    expect(text).not.toContain('共 0 套')
  })
})

describe('主页加载态（US-147）', () => {
  it('TC-WEB-503 /me 未返回时显示加载中，不显示游客；认证房屋数量为"—"，不显示 0 与"去认证产权"', async () => {
    http.get.mockImplementation(routeTable({
      '/me': () => new Promise(() => {}),
      '/resolutions': others,
      '/approval/tasks': others,
      '/polls': others
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：加载中…')
    expect(text).not.toContain('当前身份：游客')
    // 旧断言："共 — 套" → 新断言：小卡片数值为"—"，且加载中不提示去认证
    expect(statOf(wrapper, '认证房屋').find('.stat-value').text()).toBe('—')
    expect(text).not.toContain('去认证产权')
  })

  it('TC-WEB-504 /me 失败时显示加载失败与重试', async () => {
    http.get.mockImplementation(routeTable({
      '/me': () => Promise.reject(new Error('network')),
      '/resolutions': others,
      '/approval/tasks': others,
      '/polls': others
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：加载失败，请重试')
    expect(text).not.toContain('当前身份：游客')
    expect(wrapper.findAll('button').some((b) => b.text().includes('重试'))).toBe(true)
  })
})
