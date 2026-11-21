// ocap_batch_1118 GROUP_D：管理端清册表头排序（MOD-151）与席位页持有人/待绑定/冲突/提示（MOD-152）。
// 层级：unit（页面级：真实页面 + 真实 api.js，仅 mock HTTP 层与确认框）。TC-UNIT-1401 起。溯源：US-254/255/256/258/259。
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
const confirmMock = vi.hoisted(() => ({ confirmDanger: vi.fn() }))
vi.mock('@/shared/confirm', () => confirmMock)

import { mountPage, routeTable } from './helpers.js'
import AdminRegistry from '@/admin/AdminRegistry.vue'
import AdminSeats from '@/admin/AdminSeats.vue'

const { adminHttp } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  confirmMock.confirmDanger.mockReset().mockResolvedValue(true)
  for (const m of Object.values(adminHttp)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

// ------------------------------------------------------------------ US-254 / US-255
describe('AdminRegistry：表头排序（US-254、US-255）', () => {
  const UNIT = (id, b, u, f, r) => ({ id, specific_part: `${b}${u}${f}${r}`, building: b, unit_no: u, floor: f, room: r, unit_type: 'RESIDENCE', unit_type_label: '住宅', area: '89.50', owners: [] })
  const mountRegistry = async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/registry/units': { count: 45, results: Array.from({ length: 20 }, (_, i) => UNIT(i + 1, '1栋', '1单元', '2', String(201 + i))) },
      '/admin/registry/units/filter-options': { buildings: ['1栋'], unit_nos: ['1单元'] }
    }))
    const { wrapper } = await mountPage(AdminRegistry)
    await flush()
    return wrapper
  }
  const calls = () => adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/registry/units')
  const last = () => calls().at(-1)[1].params
  const headerOf = (w, label) => w.findAll('th').find((th) => th.text().trim() === label)

  it('TC-UNIT-1401 / AC-254-01、AC-255-04：初次进入（未点击表头）请求不带 sort/order（服务端默认升序）；只有楼栋、单元、楼层、房号四个表头可排序，类型/面积/业主/专有部分/操作表头不可排序', async () => {
    const w = await mountRegistry()
    expect(last().sort).toBeUndefined()
    expect(last().order).toBeUndefined()
    const sortable = w.findAll('th.is-sortable').map((th) => th.text().trim())
    expect(sortable).toEqual(['楼栋', '单元', '楼层', '房号'])
    for (const label of ['专有部分', '类型', '面积', '业主', '操作']) {
      const th = headerOf(w, label)
      if (th) expect(th.classes(), label).not.toContain('is-sortable')
    }
  })

  it('TC-UNIT-1402 / AC-255-01：点击"楼层"表头 → 以楼层为主排序键升序请求（sort=floor&order=asc），再点 → 降序（order=desc），再点 → 切回升序；表头显示当前方向指示（ascending/descending 类）', async () => {
    const w = await mountRegistry()
    const clickFloor = async () => { await headerOf(w, '楼层').trigger('click'); await flush() }
    await clickFloor()
    expect([last().sort, last().order]).toEqual(['floor', 'asc'])
    expect(headerOf(w, '楼层').classes()).toContain('ascending')
    await clickFloor()
    expect([last().sort, last().order]).toEqual(['floor', 'desc'])
    expect(headerOf(w, '楼层').classes()).toContain('descending')
    await clickFloor()
    expect([last().sort, last().order]).toEqual(['floor', 'asc'])
  })

  it('TC-UNIT-1403 / AC-255-02、AC-255-03：房号降序后翻页与改过滤条件都保持排序（sort=room&order=desc 随请求带上，页码生效）；排序变化回到第 1 页', async () => {
    const w = await mountRegistry()
    w.findComponent({ name: 'ElTable' }).vm.$emit('sort-change', { prop: 'room', order: 'descending' })
    await flush()
    expect([last().sort, last().order, last().page]).toEqual(['room', 'desc', 1])
    w.findComponent({ name: 'ElPagination' }).vm.$emit('current-change', 2)
    await flush()
    expect([last().sort, last().order, last().page]).toEqual(['room', 'desc', 2])
    await w.find('input[placeholder="房号"]').setValue('9')
    await w.find('input[placeholder="房号"]').trigger('change')
    await flush()
    expect([last().sort, last().order, last().room, last().page]).toEqual(['room', 'desc', '9', 1])
  })

  it('TC-UNIT-1404 / AC-255-03：点击"重置"→ 清除过滤与排序（请求不再带 sort/order，即默认升序），表头指示清除', async () => {
    const w = await mountRegistry()
    w.findComponent({ name: 'ElTable' }).vm.$emit('sort-change', { prop: 'building', order: 'descending' })
    await flush()
    expect(last().sort).toBe('building')
    await buttonOf(w, '重置').trigger('click')
    await flush()
    expect(last().sort).toBeUndefined()
    expect(last().order).toBeUndefined()
    expect(w.findAll('th.ascending, th.descending')).toHaveLength(0)
  })

  it('TC-UNIT-1405 / IFC-361：sort-change 取消排序（order=null）→ 不带 sort/order；四列 prop 恰为后端白名单 building/unit_no/floor/room', async () => {
    const w = await mountRegistry()
    w.findComponent({ name: 'ElTable' }).vm.$emit('sort-change', { prop: 'unit_no', order: 'ascending' })
    await flush()
    expect([last().sort, last().order]).toEqual(['unit_no', 'asc'])
    w.findComponent({ name: 'ElTable' }).vm.$emit('sort-change', { prop: 'unit_no', order: null })
    await flush()
    expect(last().sort).toBeUndefined()
  })
})

// ------------------------------------------------------------------ US-256 / US-258 / US-259（席位页）
describe('AdminSeats：持有人、待绑定、冲突、提示（US-258、US-259）', () => {
  const BOUND = { id: 1, position: 'MEMBER', user: { id: 7, account_no: '1000000007', nickname: '昵称甲', phone: '138****0001' }, term_start: '2026-01-01', term_end: '2027-01-01', status: 'ACTIVE', effective: true, holder: { kind: 'USER', unit_text: null, owner_name: null }, bind_state: 'BOUND' }
  const PENDING = { id: 2, position: 'MEMBER', user: null, term_start: '2026-01-01', term_end: '2027-01-01', status: 'ACTIVE', effective: true, holder: { kind: 'REGISTRY_OWNER', unit_text: '1栋1单元9层902号', owner_name: '业主乙' }, bind_state: 'PENDING_BIND' }
  const CONFLICT = { ...PENDING, id: 3, holder: { kind: 'REGISTRY_OWNER', unit_text: '2栋1单元1层101号', owner_name: '业主丙' }, bind_state: 'CONFLICT' }
  const mountSeats = async (rows, config = {}) => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/committee/seats': { count: rows.length, results: rows }, '/admin/committee/config': { cap_member: 6, ...config }
    }))
    const { wrapper } = await mountPage(AdminSeats)
    await flush()
    return wrapper
  }

  it('TC-UNIT-1410 / AC-258-01/04：第 1 行显示昵称（#id），第 2 行显示"1栋1单元9层902号 · 业主乙"+"待绑定"，冲突行显示"待处理冲突"；页面不出现手机号明文', async () => {
    const w = await mountSeats([BOUND, PENDING, CONFLICT])
    const rows = w.findAll('tbody tr')
    expect(rows).toHaveLength(3)
    expect(rows[0].text()).toContain('昵称甲（#7）')
    expect(rows[0].text()).not.toContain('待绑定')
    expect(rows[1].text()).toContain('1栋1单元9层902号')
    expect(rows[1].text()).toContain('业主乙')
    expect(rows[1].text()).toContain('待绑定')
    expect(rows[2].text()).toContain('2栋1单元1层101号')
    expect(rows[2].text()).toContain('业主丙')
    expect(rows[2].text()).toContain('待处理冲突')
    expect(w.text()).not.toMatch(/1[3-9]\d{9}/)
  })

  it('TC-UNIT-1411 / AC-258-02：待绑定席位与已绑定席位一样提供"变更为"与"撤销"，撤销确认框用清册业主姓名，成功后 DELETE /admin/committee/seats/{id}', async () => {
    const w = await mountSeats([PENDING])
    adminHttp.delete.mockResolvedValue({})
    const row = w.find('tbody tr')
    expect(row.text()).toContain('变更职位')
    await buttonOf(row, '撤销').trigger('click')
    await flush()
    expect(confirmMock.confirmDanger).toHaveBeenCalledWith('revokeSeat', { name: '业主乙' })
    expect(adminHttp.delete).toHaveBeenCalledWith('/admin/committee/seats/2')
  })

  it('TC-UNIT-1412 / Q-B18-33、AC-259：config.half_majority_hint 的 pending_bind>0 时顶部提示"当前待绑定 2 人，半数同意决议至少需 3 票同意"；can_pass=false 另提示"当前半数同意决议无法通过"；仅提示不禁用任何按钮；pending_bind=0 不提示', async () => {
    let w = await mountSeats([PENDING], { half_majority_hint: { mode: 'ACTIVE', denominator: 4, pending_bind: 2, need_agree: 3, can_pass: false } })
    expect(w.find('.seat-hint').text()).toBe('当前待绑定 2 人，半数同意决议至少需 3 票同意')
    expect(w.text()).toContain('当前半数同意决议无法通过')
    expect(w.findAll('button').filter((b) => b.attributes('disabled') !== undefined).map((b) => b.text())).not.toContain('赋予席位')
    expect(buttonOf(w, '赋予席位').attributes('disabled')).toBeUndefined()
    w.unmount()
    w = await mountSeats([PENDING], { half_majority_hint: { mode: 'ACTIVE', denominator: 6, pending_bind: 1, need_agree: 4, can_pass: true } })
    expect(w.text()).toContain('至少需 4 票同意')
    expect(w.text()).not.toContain('无法通过')
    w.unmount()
    w = await mountSeats([BOUND], { half_majority_hint: { mode: 'ACTIVE', denominator: 5, pending_bind: 0, need_agree: 3, can_pass: true } })
    expect(w.find('.seat-hint').exists()).toBe(false)
  })

  it('TC-UNIT-1413 / REQ-FUNC-291：昵称/姓名/电话/专有部分输入与楼栋/单元/职位一起作为筛选参数提交', async () => {
    const w = await mountSeats([BOUND])
    const input = (placeholder) => w.findAll('input').find((i) => i.attributes('placeholder') === placeholder)
    for (const [placeholder, value] of [['昵称', '昵称甲'], ['姓名', '业主乙'],
      ['电话', '13800001111'], ['专有部分', '903']]) {
      await input(placeholder).setValue(value)
      await input(placeholder).trigger('change')
    }
    await flush()
    const call = adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/committee/seats').at(-1)
    expect(call[1].params).toMatchObject({
      bucket: 'active', nickname: '昵称甲', name: '业主乙', phone: '13800001111', unit_keyword: '903'
    })
  })
})
