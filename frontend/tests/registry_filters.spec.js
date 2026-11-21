// GROUP_D：后台业主清册过滤器（MOD-108）。US-189（AC-189-01~09）、US-190、US-191（AC-191-01~03）、CR-002。
// TC-UNIT-640 ~ 647、TC-E2E-515（critical path 替代口径：jsdom 挂载真实页面 + 带状态假服务端）。
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import AdminRegistry from '@/admin/AdminRegistry.vue'
import { admin } from '@/shared/api'

const { adminHttp } = mocked

const BUILDINGS = ['1', '2', '10', '11', '地下车位']
const UNIT_NOS = ['1', '2', '10']
const FLOORS = { '1': { '2': ['9', '10'] }, '10': { '2': ['9'] }, '2': { '1': ['1', '2'] } }

beforeAll(() => {
  if (!global.ResizeObserver) {
    global.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  }
})

beforeEach(() => {
  vi.clearAllMocks()
  adminHttp.get.mockReset()
})
afterEach(() => { document.body.innerHTML = '' })

function route({
  list = { results: [], count: 0 },
  buildings = BUILDINGS,
  unitNos = UNIT_NOS,
  floors = FLOORS,
  failOptions = false
} = {}) {
  adminHttp.get.mockImplementation(async (url, arg) => {
    if (url === '/admin/registry/units') return typeof list === 'function' ? list(arg.params) : list
    if (url === '/admin/registry/unit-options') {
      if (failOptions) throw new Error('boom')
      const params = arg?.params || {}
      if (!params.building) return { level: 'building', options: buildings.map((value) => ({ value })) }
      if (!params.unit_no) return { level: 'unit_no', options: unitNos.map((value) => ({ value })) }
      return { level: 'floor', options: (floors[params.building]?.[params.unit_no] || []).map((value) => ({ value })) }
    }
    throw new Error(`未预期的 GET ${url}`)
  })
}

async function mountPage() {
  const wrapper = mount(AdminRegistry, { global: { plugins: [ElementPlus] }, attachTo: document.body })
  await flushPromises()
  return wrapper
}

function listCalls() {
  return adminHttp.get.mock.calls.filter(([url]) => url === '/admin/registry/units')
}

function placeholders(wrapper) {
  // el-input 的占位在 input[placeholder]；el-select 的占位在 .el-select__placeholder 的文字里（DOM 顺序）
  // 只看筛选区：分页区的"每页条数"选择不属于过滤控件（REQ-FUNC-283）
  const scope = wrapper.find('.filter-grid')
  return scope.findAll('input[placeholder], .el-select__placeholder')
    .map((n) => (n.element.tagName === 'INPUT' ? n.attributes('placeholder') : n.text()))
    .filter(Boolean)
}

async function typeInto(wrapper, placeholder, value) {
  const input = wrapper.findAll('input').find((i) => i.attributes('placeholder') === placeholder)
  expect(input, `找不到占位文字为 ${placeholder} 的输入框`).toBeTruthy()
  await input.setValue(value)
  await input.trigger('change')
  await flushPromises()
}

function selectByPlaceholder(wrapper, placeholder) {
  const select = wrapper.findAllComponents({ name: 'ElSelect' })
    .find((s) => s.props('placeholder') === placeholder)
  expect(select, `找不到占位文字为 ${placeholder} 的下拉框`).toBeTruthy()
  return select
}

async function choose(wrapper, placeholder, value) {
  const select = selectByPlaceholder(wrapper, placeholder)
  select.vm.$emit('update:modelValue', value)
  select.vm.$emit('change', value)
  await flushPromises()
}

describe('后台业主清册过滤器：中文界面（US-191）', () => {
  it('TC-UNIT-640 / AC-191-01、AC-189-09：过滤区占位文字为中文，含楼层级联筛选，无英文 select', async () => {
    route()
    const wrapper = await mountPage()
    expect(placeholders(wrapper)).toEqual([
      '专有部分标识', '楼栋', '单元', '楼层', '房号', '类型', '业主姓名', '业主电话'
    ])
    const visible = wrapper.text() + ' ' + placeholders(wrapper).join(' ')
    expect(/select/i.test(visible)).toBe(false)
    const labels = wrapper.findAll('[aria-label],[title]').map((n) => `${n.attributes('aria-label') || ''}${n.attributes('title') || ''}`)
    expect(labels.some((t) => /select/i.test(t))).toBe(false)
    wrapper.unmount()
  })

  it('TC-UNIT-641 / AC-191-02：类型下拉选项依次为 全部类型、未登记类型、住宅、公寓、商铺、车位、其他', async () => {
    route()
    const wrapper = await mountPage()
    const typeSelect = selectByPlaceholder(wrapper, '类型')
    const labels = typeSelect.findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))
    expect(labels).toEqual(['全部类型', '未登记类型', '住宅', '公寓', '商铺', '车位', '其他'])
    expect(labels.some((t) => /select/i.test(t))).toBe(false)
    wrapper.unmount()
  })

  it('TC-UNIT-642 / AC-191-03、AC-189-06：过滤结果为空时表格空状态为中文“暂无数据”，不显示 No Data', async () => {
    route({ list: { results: [], count: 0 } })
    const wrapper = await mountPage()
    expect(wrapper.find('.el-table__empty-text').text()).toBe('暂无数据')
    expect(wrapper.text()).not.toMatch(/No Data/i)
    expect(wrapper.text()).toContain('共 0 条')
    wrapper.unmount()
  })

  it('TC-UNIT-643 / AC-191-01：楼栋、单元下拉无选项时无数据文案为中文“暂无数据”', async () => {
    route({ buildings: [], unitNos: [] })
    const wrapper = await mountPage()
    for (const placeholder of ['楼栋', '单元', '类型']) {
      expect(selectByPlaceholder(wrapper, placeholder).props('noDataText')).toBe('暂无数据')
    }
    wrapper.unmount()
  })
})

describe('后台业主清册过滤器：参数传递与行为（US-189/190）', () => {
  it('TC-UNIT-644 / AC-189-08：首次加载只传分页，空条件不传；楼栋取自 unit-options，未选楼栋时单元无选项且禁用', async () => {
    route()
    const wrapper = await mountPage()
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/registry/unit-options', { params: {} })
    expect(listCalls()).toHaveLength(1)
    const params = listCalls()[0][1].params
    expect(params.page).toBe(1)
    expect(params.page_size).toBe(20)
    for (const key of ['q', 'unit_type', 'building', 'unit_no', 'floor', 'room', 'owner_name', 'owner_phone']) {
      expect(params[key]).toBeUndefined()
    }
    const buildingSelect = selectByPlaceholder(wrapper, '楼栋')
    expect(buildingSelect.findAllComponents({ name: 'ElOption' }).map((o) => o.props('value'))).toEqual(BUILDINGS)
    const unitSelect = selectByPlaceholder(wrapper, '单元')
    expect(unitSelect.findAllComponents({ name: 'ElOption' })).toHaveLength(0)
    expect(unitSelect.props('disabled')).toBe(true)
    await choose(wrapper, '楼栋', '10')
    expect(selectByPlaceholder(wrapper, '单元').findAllComponents({ name: 'ElOption' }).map((o) => o.props('value')))
      .toEqual(UNIT_NOS)
    wrapper.unmount()
  })

  it('TC-UNIT-645 / AC-189-01~05、AC-190-02：每个过滤器的取值以对应参数名传给 admin.registryUnits，并回到第 1 页', async () => {
    route()
    const wrapper = await mountPage()
    await choose(wrapper, '楼栋', '10')
    expect(listCalls().at(-1)[1].params).toMatchObject({ building: '10', page: 1 })
    await choose(wrapper, '单元', '2')
    await choose(wrapper, '楼层', '9')
    await typeInto(wrapper, '房号', '902')
    await choose(wrapper, '类型', 'PARKING')
    await typeInto(wrapper, '业主姓名', '张三')
    await typeInto(wrapper, '业主电话', '1234')
    await typeInto(wrapper, '专有部分标识', '902')
    expect(listCalls().at(-1)[1].params).toEqual({
      page: 1, page_size: 20, q: '902', unit_type: 'PARKING', building: '10', unit_no: '2', floor: '9',
      room: '902', owner_name: '张三', owner_phone: '1234'
    })
    wrapper.unmount()
  })

  it('TC-UNIT-646 / AC-189-05：电话过滤只保留数字，最多 11 位输入限制属性', async () => {
    route()
    const wrapper = await mountPage()
    const phone = wrapper.findAll('input').find((i) => i.attributes('placeholder') === '业主电话')
    expect(phone.attributes('maxlength')).toBe('11')
    await typeInto(wrapper, '业主电话', '13a8-00')
    expect(listCalls().at(-1)[1].params.owner_phone).toBe('13800')
    wrapper.unmount()
  })

  it('TC-UNIT-647 / AC-189-08：点“重置”清空全部条件，重新查询且不再带任何过滤参数；总数恢复', async () => {
    const all = Array.from({ length: 3 }, (_, i) => ({ id: i + 1, specific_part: `${i + 1}栋`, owners: [] }))
    route({ list: (p) => (p.building ? { results: [], count: 0 } : { results: all, count: 3 }) })
    const wrapper = await mountPage()
    await choose(wrapper, '楼栋', '地下车位')
    expect(wrapper.text()).toContain('共 0 条')
    const reset = wrapper.findAll('button').find((b) => b.text() === '重置')
    expect(reset).toBeTruthy()
    await reset.trigger('click')
    await flushPromises()
    const params = listCalls().at(-1)[1].params
    expect(params).toEqual({ page: 1, page_size: 20, q: undefined, unit_type: undefined, building: undefined,
      unit_no: undefined, room: undefined, owner_name: undefined, owner_phone: undefined })
    expect(wrapper.text()).toContain('共 3 条')
    wrapper.unmount()
  })

  it('TC-UNIT-648 / MOD-108：下拉取值请求失败时不阻塞列表，列表仍加载', async () => {
    route({ failOptions: true, list: { results: [{ id: 1, specific_part: '1栋1单元1层101号', owners: [] }], count: 1 } })
    const wrapper = await mountPage()
    expect(wrapper.text()).toContain('1栋1单元1层101号')
    expect(wrapper.text()).toContain('共 1 条')
    wrapper.unmount()
  })

  it('TC-UNIT-649 / IFC-293：api.js 的 registryFilterOptions 为管理端 GET /admin/registry/units/filter-options，registryUnits 透传 params', async () => {
    adminHttp.get.mockResolvedValue({ buildings: [], unit_nos: [] })
    await admin.registryFilterOptions()
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/registry/units/filter-options')
    await admin.registryUnits({ building: '1', owner_phone: '1234' })
    expect(adminHttp.get).toHaveBeenLastCalledWith('/admin/registry/units', { params: { building: '1', owner_phone: '1234' } })
  })
})

// ---- 带状态假服务端：与后端 IFC-291 同语义（精确/包含/交集），驱动真实页面 ----
const DATASET = [
  { id: 1, building: '1', unit_no: '2', floor: '9', room: '902', unit_type: 'RESIDENCE', unit_type_label: '住宅', specific_part: '1栋2单元9层902号', owners: [{ name: '张三丰', phones: ['13800001234'] }] },
  { id: 2, building: '10', unit_no: '2', floor: '9', room: '902', unit_type: 'RESIDENCE', unit_type_label: '住宅', specific_part: '10栋2单元9层902号', owners: [{ name: '李四光', phones: ['13900005678'] }] },
  { id: 3, building: '地下车位', unit_no: '', floor: '负一', room: '7', unit_type: 'PARKING', unit_type_label: '车位', specific_part: '地下车位负一7号', owners: [] }
]

function fakeServer(params) {
  const rows = DATASET.filter((u) =>
    (!params.building || u.building === params.building) &&
    (!params.unit_no || u.unit_no === params.unit_no) &&
    (!params.floor || u.floor === params.floor) &&
    (!params.room || u.room === params.room) &&
    (!params.unit_type || u.unit_type === params.unit_type) &&
    (!params.q || u.specific_part.includes(params.q)) &&
    (!params.owner_name || u.owners.some((o) => o.name.includes(params.owner_name))) &&
    (!params.owner_phone || u.owners.some((o) => o.phones.some((p) => p.includes(params.owner_phone)))))
  return { results: rows, count: rows.length }
}

describe('TC-E2E-515 管理员过滤旅程（critical path 替代口径：真实页面 + 带状态假服务端）', () => {
  it('US-189/190/191：打开页面→按楼栋过滤→叠加类型无结果（空状态）→改按姓名/电话→重置恢复全部，页面始终中文', async () => {
    route({ list: fakeServer })
    const wrapper = await mountPage()
    expect(wrapper.text()).toContain('共 3 条')
    // 楼栋 1：精确，不含 10
    await choose(wrapper, '楼栋', '1')
    expect(wrapper.text()).toContain('1栋2单元9层902号')
    expect(wrapper.text()).not.toContain('10栋2单元9层902号')
    expect(wrapper.text()).toContain('共 1 条')
    // 叠加类型车位 → 无同时满足 → 空状态中文
    await choose(wrapper, '类型', 'PARKING')
    expect(wrapper.find('.el-table__empty-text').text()).toBe('暂无数据')
    expect(wrapper.text()).toContain('共 0 条')
    // 清空类型与楼栋，改按姓名“张三”（包含匹配）
    await choose(wrapper, '类型', '')
    await choose(wrapper, '楼栋', '')
    await typeInto(wrapper, '业主姓名', '张三')
    expect(wrapper.text()).toContain('张三丰（13800001234）')
    expect(wrapper.text()).toContain('共 1 条')
    await typeInto(wrapper, '业主姓名', '李四')
    expect(wrapper.text()).not.toContain('张三丰')
    // 电话“9999”无结果；“5678”命中 10 栋
    await typeInto(wrapper, '业主姓名', '')
    await typeInto(wrapper, '业主电话', '9999')
    expect(wrapper.text()).toContain('共 0 条')
    await typeInto(wrapper, '业主电话', '5678')
    expect(wrapper.text()).toContain('10栋2单元9层902号')
    // 重置 → 恢复全部
    await wrapper.findAll('button').find((b) => b.text() === '重置').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('共 3 条')
    const visible = wrapper.text() + ' ' + placeholders(wrapper).join(' ')
    expect(/select|No Data/i.test(visible)).toBe(false)
    wrapper.unmount()
  })
})
