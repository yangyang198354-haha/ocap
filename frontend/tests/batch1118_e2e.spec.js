// ocap_batch_1118 GROUP_D：Web 端到端旅程（jsdom 挂载真实页面 + 真实路由 + 带状态假服务端；无浏览器 E2E 框架，画像 P3，M-TE-007）。
// critical path 口径：替代（jsdom 组件旅程 + 后端多步 API 旅程）。TC-E2E-1611 起。溯源：US-244/245/246、US-249/251/252、US-253、US-254/255。
// 带状态假服务端：列表接口返回数组副本（M-TE-036）；假服务端的排序是独立于产品代码的自然数序实现（不用被测代码输出作期望）。
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus, { ElMessage } from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import UnitsAppeal from '@/portal/units/UnitsAppeal.vue'
import Resolutions from '@/portal/Resolutions.vue'
import ResolutionDetail from '@/portal/ResolutionDetail.vue'
import AdminRegistry from '@/admin/AdminRegistry.vue'
import SideNav from '@/layout/SideNav.vue'
import { PORTAL_MENU, visibleMenu } from '@/layout/menus'

const { http, adminHttp } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

async function mountApp(routes, path, components) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.push(path)
  await router.isReady()
  const root = { template: '<router-view />' }
  const wrapper = mount(root, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
  await flush()
  return { wrapper, router, ...components }
}

describe('旅程：申诉一次提交（US-244/245/246）', () => {
  it('TC-E2E-1611 / US-244、US-245、US-246：逐级选房（户号输入"55"检索）→ 暂存 2 个文件（服务器附件数 0）→ 缺名字提示且服务器申诉 0 → 补名字提交 → 服务器恰有 1 条申诉含 2 个文件 → 页面清空；再次进入为空', async () => {
    const server = { appeals: [], attachmentsUploaded: 0 }
    const ROOMS = ['55', '551', '552', '553', '155', '60'].map((v, i) => ({ value: v, unit_id: 100 + i, label: `${v}（住宅 89.5 ㎡）`, unit_type_label: '住宅', area: '89.5' }))
    http.get.mockImplementation(async (url, arg) => {
      const p = arg?.params || {}
      if (url === '/units/options') {
        if (p.floor !== undefined) return { level: 'room', skipped: [], has_empty: false, options: ROOMS }
        if (p.unit_no !== undefined) return { level: 'floor', skipped: [], has_empty: false, options: [{ value: '5' }] }
        if (p.building !== undefined) return { level: 'unit_no', skipped: [], has_empty: false, options: [{ value: '1' }] }
        return { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }] }
      }
      if (url === '/me/housing') return { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0, real_names: [] }
      if (['/appeals/mine', '/resident-applications/mine', '/resident-applications/to-review'].includes(url)) return []
      if (url === '/me') return { profile: { id: 1 }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }
      if (url === '/me/registry-matches') return { pending: false, total: 0, units: [] }
      throw new Error(`未预期的请求 ${url}`)
    })
    http.post.mockImplementation(async (url, body) => {
      if (url === '/attachments') { server.attachmentsUploaded += 1; return { id: 'x' } }
      if (url === '/appeals') {
        server.appeals.push({ unit_id: body.get('unit_id'), owner_name: body.get('owner_name'), files: body.getAll('files').map((f) => f.name) })
        return { id: server.appeals.length, status: 'PENDING' }
      }
      throw new Error(`未预期的请求 ${url}`)
    })
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountApp([{ path: '/', component: UnitsAppeal }], '/')
    const selects = () => wrapper.findAllComponents({ name: 'ElSelect' })
    const choose = async (s, v) => { s.vm.$emit('update:modelValue', v); s.vm.$emit('change', v); await flush() }
    await choose(selects()[0], '1')
    await choose(selects()[1], '1')
    await choose(selects()[2], '5')
    selects()[3].props('filterMethod')('55')
    await flush()
    const roomOptions = wrapper.findAllComponents({ name: 'ElOption' }).filter((o) => ROOMS.some((r) => r.unit_id === o.props('value')))
    expect(roomOptions.map((o) => o.props('label').split('（')[0])).toEqual(['55', '551', '552', '553', '155'])
    await choose(selects()[3], 102)
    expect(wrapper.text()).toContain('住宅 · 89.5 ㎡')
    const onChange = wrapper.findComponent({ name: 'ElUpload' }).props('onChange')
    onChange({ raw: new File(['x'], 'a.png', { type: 'image/png' }), status: 'ready' })
    onChange({ raw: new File(['x'], 'b.pdf', { type: 'application/pdf' }), status: 'ready' })
    await flush()
    expect(wrapper.text()).toContain('已选 2 份')
    expect(server.attachmentsUploaded).toBe(0)
    await buttonOf(wrapper, '提交申诉').trigger('click')
    expect(warn).toHaveBeenLastCalledWith('请输入产权人名字')
    expect(server.appeals).toHaveLength(0)
    await wrapper.find('input[placeholder="产权人名字"]').setValue('业主甲')
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(server.appeals).toEqual([{ unit_id: '102', owner_name: '业主甲', files: ['a.png', 'b.pdf'] }])
    expect(server.attachmentsUploaded).toBe(0)
    expect(success).toHaveBeenCalledWith('申诉已提交，等待管理员审核')
    expect(wrapper.text()).toContain('已选 0 份')
    wrapper.unmount()
    const again = await mountApp([{ path: '/', component: UnitsAppeal }], '/')
    expect(again.wrapper.text()).toContain('已选 0 份')
  })
})

describe('旅程：决议卡片进入详情并看到参与人（US-249/250/251/252）', () => {
  it('TC-E2E-1612 / US-249、US-250、US-251、US-252：公开决议列表（进行中半数同意 + 已结束）→ 点击卡片链接进入 /resolutions/{id} → 详情显示"已参与 N 人"与参与人（无选项）→ 返回列表', async () => {
    const rows = [
      { id: 31, title: '车库照明改造', status: 'PENDING', approval_mode: 'HALF_MAJORITY', vote_deadline: '2026-12-01T18:00:00+08:00', initiator: { id: 2, labels: ['主任'], display_name: '发起人甲' },
        vote_counts: { agree: 3, disagree: 1, abstain: 0 }, participation: { voted: 4, expected: 7 }, content: '正文', attachments: [] },
      { id: 28, title: '地胶更换', status: 'APPROVED', approval_mode: 'DESIGNATED', vote_deadline: null, initiator: { id: 3, labels: ['委员'], display_name: '8000000028' }, participation: null, content: '正文', attachments: [] }
    ]
    http.get.mockImplementation(async (url, arg) => {
      if (url === '/me') return { profile: { id: 9, nickname: '合成用户' }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }
      if (url === '/resolutions') return { count: 2, results: [...rows] }
      if (url === '/approval/flows') return { results: [] }
      const m = url.match(/^\/resolutions\/(\d+)$/)
      if (m) return rows.find((r) => r.id === Number(m[1]))
      if (url === '/resolutions/31/participants') {
        return { mode: 'HALF_MAJORITY', count: 4, results: ['委员甲', '委员乙', '委员丙', '委员丁'].map((n, i) => ({ display_name: n, avatar_url: null, voted_at: `2026-11-18T0${i + 1}:00:00+08:00` })) }
      }
      throw new Error(`未预期的请求 ${url} ${JSON.stringify(arg)}`)
    })
    const { wrapper, router } = await mountApp([
      { path: '/resolutions', component: Resolutions, props: { section: 'public' } },
      { path: '/resolutions/:id(\\d+)', component: ResolutionDetail }
    ], '/resolutions')
    const cards = wrapper.findAll('.res-card')
    expect(cards).toHaveLength(2)
    expect(cards[0].text()).toContain('进行中')
    expect(cards[0].text()).toContain('已参与 4 / 7 · 57%')
    expect(cards[1].text()).toContain('已结束')
    await cards[0].find('a.res-title').trigger('click')
    await flush()
    expect(router.currentRoute.value.fullPath).toBe('/resolutions/31')
    expect(wrapper.text()).toContain('车库照明改造')
    expect(wrapper.text()).toContain('已参与 4 人')
    for (const n of ['委员甲', '委员乙', '委员丙', '委员丁']) expect(wrapper.text()).toContain(n)
    expect(wrapper.text()).not.toContain('决议不存在或无权查看')
    expect(wrapper.find('.participant-list').text()).not.toMatch(/同意|反对|弃权/)
    await router.push('/resolutions')
    await flush()
    expect(wrapper.findAll('.res-card')).toHaveLength(2)
  })
})

describe('旅程：左侧导航二级菜单（US-253）', () => {
  it('TC-E2E-1613 / US-253：点击"我的房屋"展开 → 点击"认证申诉"导航并仅该项选中 → 点击"决议"时前一个收起 → 在二级项上按 Esc 收起并还焦点', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: { template: '<i />' } }] })
    router.push('/')
    await router.isReady()
    const w = mount(SideNav, { props: { menu: visibleMenu(PORTAL_MENU, { isCommittee: true }) }, global: { plugins: [router], stubs: { transition: false } }, attachTo: document.body })
    await flushPromises()
    const toggle = (label) => w.findAll('button.side-group-toggle').find((b) => b.text().includes(label))
    await toggle('我的房屋').trigger('click')
    expect(toggle('我的房屋').attributes('aria-expanded')).toBe('true')
    await w.findAll('.side-sub-item').find((a) => a.text().includes('认证申诉')).trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/units/appeal')
    expect(w.findAll('.side-sub-item.is-active').map((a) => a.text())).toEqual(['认证申诉'])
    await toggle('决议').trigger('click')
    expect(toggle('我的房屋').attributes('aria-expanded')).toBe('false')
    expect(toggle('决议').attributes('aria-expanded')).toBe('true')
    await w.find('.side-sub-item').trigger('keydown', { key: 'Escape' })
    await flushPromises()
    expect(w.find('.side-sub').exists()).toBe(false)
    expect(document.activeElement).toBe(toggle('决议').element)
  })
})

describe('旅程：管理端清册默认顺序与表头排序（US-254/255）', () => {
  // 独立于产品代码的自然数序假服务端（只处理纯数字楼栋"N栋"、单元、楼层、房号）
  const num = (s) => Number(String(s).replace(/\D/g, ''))
  const DATA = [['2栋', '1单元', '1', '101'], ['1栋', '2单元', '10', '1001'], ['1栋', '1单元', '2', '201'], ['10栋', '1单元', '3', '301'], ['1栋', '1单元', '10', '1001'], ['2栋', '1单元', '1', '102']]
    .map((r, i) => ({ id: i + 1, building: r[0], unit_no: r[1], floor: r[2], room: r[3], specific_part: r.join(''), unit_type: 'RESIDENCE', unit_type_label: '住宅', area: '89.50', owners: [] }))
  const KEYS = ['building', 'unit_no', 'floor', 'room']
  const cmp = (a, b) => { for (const k of KEYS) { const d = num(a[k]) - num(b[k]); if (d) return d } return a.id - b.id }
  const serve = (p) => {
    let rows = [...DATA].sort(cmp)
    if (p.sort) {
      const sign = p.order === 'desc' ? -1 : 1
      rows = rows.sort((a, b) => sign * (num(a[p.sort]) - num(b[p.sort])) || cmp(a, b) * (p.order === 'desc' ? 1 : 1))
    }
    const size = p.page_size || 20
    return { count: rows.length, results: rows.slice(((p.page || 1) - 1) * size, (p.page || 1) * size) }
  }

  it('TC-E2E-1614 / US-254、US-255：进入页面按楼栋/单元/楼层/房号自然顺序升序（2 在 10 之前）→ 点"楼层"降序 → 再点升序 → 点"房号"降序首行为最大房号 → "重置"回默认；类型/业主列表头不可排序', async () => {
    adminHttp.get.mockImplementation(async (url, arg) => {
      if (url === '/admin/registry/units') return serve(arg.params)
      if (url === '/admin/registry/units/filter-options') return { buildings: ['1栋', '2栋', '10栋'], unit_nos: ['1单元', '2单元'] }
      throw new Error(`未预期的请求 ${url}`)
    })
    const { wrapper } = await mountApp([{ path: '/', component: AdminRegistry }], '/')
    const parts = () => wrapper.findAll('tbody tr').map((tr) => tr.findAll('td')[0].text())
    const defaultOrder = ['1栋1单元2201', '1栋1单元101001', '1栋2单元101001', '2栋1单元1101', '2栋1单元1102', '10栋1单元3301']
    expect(parts()).toEqual(defaultOrder)
    const th = (label) => wrapper.findAll('th').find((x) => x.text().trim() === label)
    expect(th('楼层').classes()).toContain('is-sortable')
    expect(th('类型')?.classes() || []).not.toContain('is-sortable')
    await th('楼层').trigger('click')
    await flush()
    await th('楼层').trigger('click')
    await flush()
    expect(wrapper.findAll('tbody tr').map((tr) => tr.findAll('td')[3].text())).toEqual(['10', '10', '3', '2', '1', '1'])
    await th('楼层').trigger('click')
    await flush()
    expect(wrapper.findAll('tbody tr').map((tr) => tr.findAll('td')[3].text())).toEqual(['1', '1', '2', '3', '10', '10'])
    await th('房号').trigger('click')
    await flush()
    await th('房号').trigger('click')
    await flush()
    expect(wrapper.findAll('tbody tr')[0].findAll('td')[4].text()).toBe('1001')
    await buttonOf(wrapper, '重置').trigger('click')
    await flush()
    expect(parts()).toEqual(defaultOrder)
    expect(wrapper.findAll('th.ascending, th.descending')).toHaveLength(0)
  })
})
