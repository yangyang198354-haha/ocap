// REQ-FUNC-276~288：身份全称放大、公开决议分区、每页条数、房屋关系专有部分过滤。
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import UnitsIdentity from '@/portal/units/UnitsIdentity.vue'
import Resolutions from '@/portal/Resolutions.vue'
import AdminRegistry from '@/admin/AdminRegistry.vue'
import AdminMemberships from '@/admin/AdminMemberships.vue'

const { http, adminHttp } = mocked
const ME = { profile: { id: 1, nickname: '甲', phone: null }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
})

describe('US-282 我的身份与房屋', () => {
  it('汇总身份整行放大并使用大号标签，身份文案为后端全称', async () => {
    http.get.mockImplementation(routeTable({
      '/me/housing': { summary: { code: 'CHAIR', label: '业委会主任' }, units: [], real_names: ['业主甲'], pending_review_count: 0 }
    }))
    const { wrapper } = await mountPage(UnitsIdentity)
    const identity = wrapper.find('.summary-identity')
    expect(identity.exists()).toBe(true)
    expect(identity.text()).toContain('业委会主任')
    expect(wrapper.find('.summary-tag').text()).toBe('业委会主任')
  })
})

describe('US-283/US-284 公开决议分区', () => {
  const rows = [
    { id: 1, title: '进行中甲', status: 'PENDING', approval_mode: 'HALF_MAJORITY', vote_deadline: null, participation: null },
    { id: 2, title: '已结束乙', status: 'APPROVED', approval_mode: 'DESIGNATED' },
    { id: 3, title: '已结束丙', status: 'REJECTED', approval_mode: 'DESIGNATED' }
  ]

  it('公开决议分“进行中（n）/已结束（n）”两区，进行中在前', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions': { count: 3, results: rows }
    }))
    const { wrapper } = await mountPage(Resolutions)
    const headings = wrapper.findAll('.res-section-title').map((h) => h.text())
    expect(headings).toEqual(['进行中（1）', '已结束（2）'])
    expect(wrapper.findAll('.res-card')).toHaveLength(3)
  })

  it('“我发起的”分区不分组，且空结果不显示分区标题', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions': { count: 0, results: [] }
    }))
    const { wrapper } = await mountPage(Resolutions, { props: { section: 'mine' } })
    expect(wrapper.findAll('.res-section-title')).toHaveLength(0)
    expect(wrapper.text()).toContain('暂无决议')
  })
})

describe('US-285/US-286 业主清册', () => {
  it('分页可选每页条数：切换为 50 后回到第 1 页并按 page_size=50 请求', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/registry/units': { count: 120, results: [] },
      '/admin/registry/units/filter-options': { buildings: [], unit_nos: [] }
    }))
    const { wrapper } = await mountPage(AdminRegistry)
    const pagerSelect = wrapper.findAllComponents({ name: 'ElSelect' })
      .find((c) => c.classes().includes('pager-size'))
    expect(pagerSelect).toBeTruthy()
    pagerSelect.vm.$emit('change', 50)
    await flush()
    const calls = adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/registry/units')
    expect(calls.at(-1)[1].params).toMatchObject({ page: 1, page_size: 50 })
  })

  it('筛选区与表格共用 1160px 列宽容器，表宽固定为 1160px', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/registry/units': { count: 0, results: [] },
      '/admin/registry/units/filter-options': { buildings: [], unit_nos: [] }
    }))
    const { wrapper } = await mountPage(AdminRegistry)
    expect(wrapper.find('.filter-grid').exists()).toBe(true)
    expect(wrapper.find('.el-table').attributes('style')).toContain('width: 1160px')
  })
})

describe('US-288 用户房屋关系', () => {
  it('“专有部分标识 / 户号”作为独立参数 unit_keyword 传给后端，并与身份筛选并存', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/memberships': { count: 0, results: [] },
      '/admin/registry/unit-options': { options: [] }
    }))
    const { wrapper } = await mountPage(AdminMemberships)
    const input = wrapper.findAll('input').find((i) => i.attributes('placeholder') === '专有部分标识 / 户号')
    expect(input).toBeTruthy()
    await input.setValue('101')
    await input.trigger('keyup.enter')
    await flush()
    const call = adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/memberships').at(-1)
    expect(call[1].params).toMatchObject({ unit_keyword: '101', page: 1 })
  })

  it('原关键词框提示收窄为姓名/手机号（后 4 位起）', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/memberships': { count: 0, results: [] },
      '/admin/registry/unit-options': { options: [] }
    }))
    const { wrapper } = await mountPage(AdminMemberships)
    const placeholders = wrapper.findAll('input').map((i) => i.attributes('placeholder'))
    expect(placeholders).toContain('姓名 / 手机号（后 4 位起）')
    expect(placeholders).toContain('专有部分标识 / 户号')
  })
})
