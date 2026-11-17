// ocap_identity_property GROUP_D：小程序"我的房屋"页、首页、绑定手机号页、引导卡片（MOD-138，IFC-344）。
// 页面脚本与模板经 @vue/test-utils 编译挂载；uni 为桩（setup.js），不代表微信真机行为；小程序构建与真机未验证（M-SD-006，见 e2e_test_report 人工验证清单）。
// 层级：unit（页面级：单个页面/组件 + 真实 api.js，uni.request 为桩；TC-MP-* 一律计入 unit 层）。
// 溯源：US-232、US-234、US-236~243 的小程序部分（US-242）。TC-MP-901 起。合成数据（C-73）。
import { describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { byText, mountPage, requests, respondWith } from './helpers.js'
import Units from '../pages/units/index.vue'
import Index from '../pages/index/index.vue'
import Phone from '../pages/phone/index.vue'
import RegistryMatchCard from '../components/RegistryMatchCard.vue'
import UnitPicker from '../components/UnitPicker.vue'

const toasts = () => uni.showToast.mock.calls.map((c) => c[0].title)
const OWNED = {
  unit_id: 107, specific_part: '1栋1单元9层902号', role: 'HEAD', role_label: '产权业主', unit_type_label: '住宅', area_display: '89.50 ㎡',
  residents: [{ user_id: 9, nickname: '合成同住人', account_no: '1000000009', joined_at: '2026-02-03T09:05:00+08:00' }], pending_application_count: 0
}
const RESIDENT = { unit_id: 108, specific_part: '2栋1单元3层301号', role: 'RESIDENT', role_label: '同住人', unit_type_label: '公寓', area_display: '未登记', residents: [], pending_application_count: 0 }
const housing = (units, pending = 0) => ({ summary: units.some((u) => u.role !== 'RESIDENT') ? { code: 'OWNER', label: '产权业主' } : units.length ? { code: 'RESIDENT', label: '同住人' } : { code: 'GUEST', label: '游客' }, units, pending_review_count: pending })
const ME = (units = []) => ({ profile: { id: 1, nickname: '合成用户', phone: '138****0000' }, identities: { is_guest: !units.length, units, labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } })
const NO_MATCH = { pending: false, total: 0, units: [] }
const base = (over = {}) => ({
  'GET /me': ME(), 'GET /me/housing': housing([]), 'GET /me/registry-matches': NO_MATCH, 'GET /resident-applications/to-review': [],
  'GET /resident-applications/mine': [], 'GET /appeals/mine': [], 'GET /units/options': { options: [] }, ...over
})
const titles = (wrapper) => wrapper.findAll('.title').map((t) => t.text().replace(/（\d+）$/, ''))

describe('我的房屋页：房屋明细与待审批卡片（US-232、US-234、US-242）', () => {
  it('TC-MP-901 / AC-242-01：已有 1 套住宅（产权业主）+ 1 套公寓（同住人）——汇总身份 + 2 行，含名称/类型/面积（未登记）/关系；同住人名单与"移除"、"退出"', async () => {
    respondWith(base({ 'GET /me/housing': housing([OWNED, RESIDENT]) }))
    const { wrapper } = await mountPage(Units)
    const text = wrapper.text()
    expect(text).toContain('汇总身份：产权业主')
    const rows = wrapper.findAll('.list-item').filter((r) => r.text().includes('号'))
    expect(text).toContain('1栋1单元9层902号')
    expect(text).toContain('住宅 · 89.50 ㎡')
    expect(text).toContain('2栋1单元3层301号')
    expect(text).toContain('公寓 · 未登记')
    expect(text).toContain('合成同住人')
    expect(byText(wrapper, 'button', '移除')).toBeTruthy()
    expect(byText(wrapper, 'button', '退出')).toBeTruthy()
    expect(rows.length).toBeGreaterThanOrEqual(2)
    expect(text).not.toContain('户主')
    expect(text).not.toContain('暂无已认证房屋')
  })

  it('TC-MP-902 / AC-242-03、AC-237-02、AC-237-03：无任何有效房屋——提醒"您还没有认证任何专有部分，请先认证产权"；有房屋则不显示提醒；"认证产权"按钮始终在', async () => {
    respondWith(base())
    const guest = await mountPage(Units)
    expect(guest.wrapper.text()).toContain('暂无已认证房屋')
    expect(guest.wrapper.text()).toContain('您还没有认证任何专有部分，请先认证产权')
    expect(guest.wrapper.findAll('button').some((b) => b.text() === '认证产权')).toBe(true)
    guest.wrapper.unmount()
    respondWith(base({ 'GET /me/housing': housing([RESIDENT]) }))
    const resident = await mountPage(Units)
    expect(resident.wrapper.text()).not.toContain('您还没有认证任何专有部分')
    const button = resident.wrapper.findAll('button').find((b) => b.text() === '认证产权')
    expect(button).toBeTruthy()
    uni.pageScrollTo = vi.fn()
    try {
      await button.trigger('click')
      expect(uni.pageScrollTo).toHaveBeenCalledWith({ selector: '#certify' }) // AC-237-01：滚动到本页"认证产权"卡片
    } finally {
      delete uni.pageScrollTo
    }
    expect(resident.wrapper.find('#certify').exists()).toBe(true)
  })

  it('TC-MP-903 / AC-242-02、AC-234-04、AC-234-01、AC-234-03：游客与仅同住人无"待我审批"卡片；产权业主在页面底部看到并可通过', async () => {
    for (const units of [[], [RESIDENT]]) {
      respondWith(base({ 'GET /me/housing': housing(units) }))
      const { wrapper } = await mountPage(Units)
      expect(wrapper.text()).not.toContain('待我审批的同住人申请')
      expect(wrapper.find('#review').exists()).toBe(false)
      wrapper.unmount()
    }
    let pending = [{ id: 4, applicant: { nickname: '申请人甲' }, unit: { specific_part: '1栋1单元9层902号' }, created_at: '2026-11-13T20:30:00+08:00' }]
    respondWith(base({
      'GET /me/housing': housing([{ ...OWNED, residents: [] }], 1),
      'GET /resident-applications/to-review': () => pending,
      'POST /resident-applications/4/decision': () => { pending = []; return {} }
    }))
    const { wrapper } = await mountPage(Units)
    expect(titles(wrapper).at(-1)).toBe('待我审批的同住人申请')
    expect(wrapper.find('#review').text()).toContain('申请人甲 → 1栋1单元9层902号')
    await byText(wrapper.find('#review'), 'button', '通过').trigger('click')
    await flushPromises()
    expect(toasts()).toContain('已处理')
    expect(wrapper.find('#review').text()).toContain('暂无待审批的同住人申请')
  })
})

describe('认证产权卡片与同住人申请（US-236、US-238、US-242、US-243）', () => {
  it('TC-MP-904 / AC-242-03、AC-236-02、AC-238-01：卡片标题"认证产权"、姓名占位为本人姓名；无"申请成为同住人"出现在认证产权卡片；无"选择房屋""户主"文案', async () => {
    respondWith(base())
    const { wrapper } = await mountPage(Units)
    expect(titles(wrapper)).toEqual(expect.arrayContaining(['我的身份与房屋', '认证产权', '认证申诉', '我的同住人申请', '我的申诉']))
    expect(titles(wrapper)).not.toContain('选择房屋')
    expect(wrapper.findAll('input').map((i) => i.attributes('placeholder'))).toContain('请输入您本人的姓名（须与业主清册登记的姓名一致）')
    expect(wrapper.findAll('input').map((i) => i.attributes('placeholder'))).not.toContain('请输入姓名')
    const certifyCard = wrapper.find('#certify')
    expect(byText(certifyCard, 'button', '申请成为同住人')).toBeUndefined()
    expect(wrapper.text()).not.toContain('户主')
    expect(wrapper.text()).not.toContain('选择房屋')
  })

  it('TC-MP-905 / AC-242-06、AC-243-01、AC-243-03：未选房号点"申请成为同住人"提示"请先选择房号"不发请求；选定后只提交 {unit_id}，提示并出现在申请列表', async () => {
    let mine = []
    respondWith(base({
      'GET /resident-applications/mine': () => mine,
      'POST /resident-applications': () => { mine = [{ id: 9, unit: { specific_part: '2栋2单元3层301号' }, status: 'PENDING', created_at: '2026-11-17T10:00:00+08:00' }]; return { id: 9, status: 'PENDING' } }
    }))
    const { wrapper } = await mountPage(Units)
    await byText(wrapper, 'button', '申请成为同住人').trigger('click')
    await flushPromises()
    expect(toasts()).toContain('请先选择房号')
    expect(requests().filter((r) => r.path === '/resident-applications' && r.method === 'POST')).toHaveLength(0)
    wrapper.findAllComponents(UnitPicker)[1].vm.$emit('update:modelValue', 42)
    await flushPromises()
    await byText(wrapper, 'button', '申请成为同住人').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'POST' && r.path === '/resident-applications').data).toEqual({ unit_id: 42 })
    expect(toasts()).toContain('申请已提交，等待产权业主审批')
    expect(wrapper.text()).toContain('2栋2单元3层301号')
    expect(wrapper.text()).toContain('待审批')
  })
})

describe('首页（US-232 小程序部分）', () => {
  it('TC-MP-906 / AC-232-04：首页游客显示"共 0 套"与"去认证产权"空状态；"待审批同住人申请"链接指向我的房屋页 review 定位；游客无该链接', async () => {
    const table = (units, pending) => ({ 'GET /me': ME(units), 'GET /me/housing': housing(units, pending), 'GET /approval/tasks': { results: [] }, 'GET /resolutions': { results: [] }, 'GET /polls': { results: [] } })
    respondWith(table([], 0))
    const guest = await mountPage(Index)
    expect(guest.wrapper.text()).toContain('共 0 套')
    expect(guest.wrapper.text()).toContain('暂无已认证房屋，去认证产权')
    expect(guest.wrapper.text()).not.toContain('待审批同住人申请')
    guest.wrapper.unmount()
    respondWith(table([OWNED], 2))
    const owner = await mountPage(Index)
    const link = owner.wrapper.findAll('.home-meta').find((e) => e.text().includes('待审批同住人申请：2'))
    expect(link).toBeTruthy()
    await link.trigger('click')
    expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/units/index?review=1' })
  })
})

describe('绑定手机号页（US-239、US-241、US-242）', () => {
  const bindWith = async (result) => {
    respondWith({ 'GET /me': { profile: { id: 1, nickname: '微信用户', phone: null }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }, 'POST /me/phone/bind': result })
    const { wrapper } = await mountPage(Phone)
    await wrapper.findAll('input')[0].setValue('13900000004')
    await wrapper.findAll('input')[1].setValue('123456')
    await byText(wrapper, 'button', '绑定').trigger('click')
    await flushPromises()
  }

  it('TC-MP-907 / AC-242-04、AC-241-01：绑定成功且 registry_match.pending → 跳转"我的房屋"页；不再提示"已绑定并按清册自动认证 N 个专有部分"', async () => {
    await bindWith({ merged: false, phone: '139****0004', auto_bound: [], registry_match: { pending: true, count: 2 } })
    expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/units/index' })
    expect(toasts().join('|')).not.toContain('自动认证')
    expect(toasts()).toContain('已完成')
  })

  it('TC-MP-908 / AC-242-04、AC-239-12：无匹配或账号合并——不跳转、不引导', async () => {
    await bindWith({ merged: false, phone: '139****0004', auto_bound: [], registry_match: { pending: false, count: 0 } })
    expect(uni.navigateTo).not.toHaveBeenCalled()
    uni.showToast.mockClear()
    // 客户端自身也须守住合并场景：即使响应误带 pending=true，merged=true 时也不跳转（AC-239-12）
    await bindWith({ merged: true, token: 'NEWTOK', auto_bound: [], registry_match: { pending: true, count: 1 } })
    expect(uni.navigateTo).not.toHaveBeenCalled()
    expect(toasts()).toContain('账号已合并')
  })
})

describe('引导卡片 RegistryMatchCard（US-239、US-240、US-242）', () => {
  const mk = (n) => Array.from({ length: n }, (_, i) => ({ unit_id: 3000 + i, specific_part: `车库B-${i + 1}`, unit_type_label: '车位' }))
  const mountCard = async (units, over = {}) => {
    respondWith({ 'GET /me/registry-matches': { pending: units.length > 0, total: units.length, units }, ...over })
    return mountPage(RegistryMatchCard)
  }

  it('TC-MP-909 / AC-242-04、AC-242-05、AC-239-07：1 套——询问文案、两个按钮、已选 1 套；不渲染接口多给的姓名/手机号；无需输入姓名', async () => {
    const { wrapper } = await mountCard([{ unit_id: 1, specific_part: '1栋1单元9层902号', unit_type_label: '住宅', owner_name: '测试清册业主甲', phone: '13900000001' }])
    const text = wrapper.text()
    expect(text).toContain('我们发现您的手机号登记在 1栋1单元9层902号（住宅）名下，您是该专有部分的业主吗？')
    expect(byText(wrapper, 'button', '是，确认认证')).toBeTruthy()
    expect(byText(wrapper, 'button', '不是')).toBeTruthy()
    expect(text).not.toContain('测试清册业主甲')
    expect(text).not.toContain('13900000001')
    expect(wrapper.find('input').exists()).toBe(false)
  })

  it('TC-MP-910 / AC-239-03：pending=false 或接口失败——卡片不渲染', async () => {
    const none = await mountCard([])
    expect(none.wrapper.find('#registry-match').exists()).toBe(false)
    none.wrapper.unmount()
    respondWith({})
    const failed = await mountPage(RegistryMatchCard)
    expect(failed.wrapper.find('#registry-match').exists()).toBe(false)
  })

  it('TC-MP-911 / AC-239-10、AC-239-11：12 套折叠 10 + "展开更多（还有 2 套）"，默认全选"已选 12 套"，展开后 12 套；恰 10 套不折叠', async () => {
    const twelve = await mountCard(mk(12))
    expect(twelve.wrapper.findAll('.list-item')).toHaveLength(10)
    expect(twelve.wrapper.text()).toContain('展开更多（还有 2 套）')
    expect(twelve.wrapper.text()).toContain('已选 12 套')
    await twelve.wrapper.findAll('.link').find((e) => e.text().includes('展开更多')).trigger('click')
    await flushPromises()
    expect(twelve.wrapper.findAll('.list-item')).toHaveLength(12)
    expect(twelve.wrapper.text()).not.toContain('展开更多')
    twelve.wrapper.unmount()
    const ten = await mountCard(mk(10))
    expect(ten.wrapper.findAll('.list-item')).toHaveLength(10)
    expect(ten.wrapper.text()).not.toContain('展开更多')
    expect(ten.wrapper.text()).toContain('已选 10 套')
  })

  it('TC-MP-912 / AC-240-02、AC-240-03：取消勾选 1 套——已选 2 套，确认只提交 2 个 unit_ids；全部取消后确认按钮禁用且不发请求', async () => {
    const { wrapper } = await mountCard(mk(3), { 'POST /me/registry-matches/confirm': { succeeded: 2, failed: 0, results: [] } })
    await wrapper.findAll('.list-item')[2].trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('已选 2 套')
    await byText(wrapper, 'button', '是，确认认证').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.path === '/me/registry-matches/confirm').data).toEqual({ unit_ids: [3000, 3001] })
    expect(toasts()).toContain('认证成功，共认证 2 套')
    expect(wrapper.emitted('resolved')).toHaveLength(1)
    expect(wrapper.find('#registry-match').exists()).toBe(false)
    wrapper.unmount()
    uni.request.mockClear()
    const again = await mountCard(mk(2))
    for (const item of again.wrapper.findAll('.list-item')) await item.trigger('click')
    await flushPromises()
    const confirm = byText(again.wrapper, 'button', '是，确认认证')
    expect(confirm.attributes('disabled')).toBeDefined()
    await confirm.trigger('click')
    expect(requests().filter((r) => r.path === '/me/registry-matches/confirm')).toHaveLength(0)
  })

  it('TC-MP-913 / AC-240-01、AC-240-04：单套确认成功提示"认证成功，身份：产权业主"；部分失败提示"成功 1 套，未成功 1 套"', async () => {
    const one = await mountCard(mk(1), { 'POST /me/registry-matches/confirm': { succeeded: 1, failed: 0, results: [] } })
    await byText(one.wrapper, 'button', '是，确认认证').trigger('click')
    await flushPromises()
    expect(toasts()).toContain('认证成功，身份：产权业主')
    one.wrapper.unmount()
    const two = await mountCard(mk(2), { 'POST /me/registry-matches/confirm': { succeeded: 1, failed: 1, results: [] } })
    await byText(two.wrapper, 'button', '是，确认认证').trigger('click')
    await flushPromises()
    expect(toasts()).toContain('成功 1 套，未成功 1 套')
  })

  it('TC-MP-914 / AC-239-06：点"不是"——只调用 dismiss，不发 confirm，卡片关闭并 emit resolved', async () => {
    const { wrapper } = await mountCard(mk(1), { 'POST /me/registry-matches/dismiss': null })
    await byText(wrapper, 'button', '不是').trigger('click')
    await flushPromises()
    const posts = requests().filter((r) => r.method === 'POST').map((r) => r.path)
    expect(posts).toEqual(['/me/registry-matches/dismiss'])
    expect(wrapper.find('#registry-match').exists()).toBe(false)
    expect(wrapper.emitted('resolved')).toHaveLength(1)
  })
})
