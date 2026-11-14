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

describe('主页认证房屋明细（US-146）', () => {
  it('TC-WEB-501 展示数量、名称、类型、面积与关系标签', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME(['产权业主'], [UNIT_A, UNIT_B]),
      '/resolutions': others,
      '/approval/tasks': others,
      '/polls': others
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：产权业主')
    expect(text).toContain('共 2 套')
    expect(text).toContain('1栋1单元9层902号')
    expect(text).toContain('住宅')
    expect(text).toContain('89.50 ㎡')
    expect(text).toContain('2栋1单元3层301号')
    expect(text).toContain('公寓')
    expect(text).toContain('未登记')
    expect(text).toContain('同住人')
  })

  it('TC-WEB-502 游客：数量 0 与空状态', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME(['游客']), '/resolutions': others, '/approval/tasks': others, '/polls': others
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：游客')
    expect(text).toContain('共 0 套')
    expect(text).toContain('暂无已认证房屋')
  })
})

describe('主页加载态（US-147）', () => {
  it('TC-WEB-503 /me 未返回时显示加载中，不显示游客或 0 套', async () => {
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
    expect(text).toContain('共 — 套')
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
