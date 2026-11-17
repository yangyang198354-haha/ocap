// ocap_identity_property GROUP_D PHASE_09：小程序端到端旅程（替代口径）。
// critical path 口径：替代——无微信开发者工具/真机（画像 P4），用 vitest + 真实页面脚本/模板 + 真实 api.js，uni.request 为带状态的假服务端；
// 页面间跳转由测试按 uni.navigateTo 的目标挂载下一页来模拟。真机行为见 e2e_test_report 人工验证清单。
// 溯源：US-239、US-240、US-241、US-242。TC-E2E-920 起。合成数据（C-73）。
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { byText, mountPage, requests, respondWith } from './helpers.js'
import Phone from '../pages/phone/index.vue'
import Units from '../pages/units/index.vue'

const toasts = () => uni.showToast.mock.calls.map((c) => c[0].title)
const POOL = (n) => Array.from({ length: n }, (_, i) => ({ unit_id: 4000 + i, specific_part: `车库B-${i + 1}`, unit_type_label: '车位', area_display: `${10 + i}.00 ㎡` }))

function server({ matches, prompt = 'PENDING' }) {
  const S = { owned: [], prompt, confirms: [], dismissed: 0, phone: null }
  const open = () => (S.prompt === 'PENDING' ? matches.filter((m) => !S.owned.some((o) => o.unit_id === m.unit_id)) : [])
  const units = () => S.owned.map((u) => ({ ...u, role: 'HEAD', role_label: '产权业主', residents: [], pending_application_count: 0 }))
  const me = () => ({ profile: { id: 7, nickname: '微信用户', phone: S.phone }, identities: { is_guest: !S.owned.length, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } })
  respondWith({
    'GET /me': () => me(),
    'GET /me/housing': () => ({ summary: S.owned.length ? { code: 'OWNER', label: '产权业主' } : { code: 'GUEST', label: '游客' }, units: units(), pending_review_count: 0 }),
    'GET /me/registry-matches': () => { const o = open(); return { pending: o.length > 0, total: o.length, units: o.map(({ unit_id, specific_part, unit_type_label }) => ({ unit_id, specific_part, unit_type_label })) } },
    'GET /resident-applications/to-review': () => [],
    'GET /resident-applications/mine': () => [],
    'GET /appeals/mine': () => [],
    'GET /units/options': () => ({ options: [] }),
    'POST /me/phone/bind': () => { S.phone = '139****0005'; return { merged: false, phone: '139****0005', auto_bound: [], registry_match: { pending: matches.length > 0, count: matches.length } } },
    'POST /me/registry-matches/confirm': (body) => {
      S.confirms.push(body)
      const chosen = matches.filter((m) => body.unit_ids.includes(m.unit_id))
      S.owned.push(...chosen)
      S.prompt = 'DONE'
      return { succeeded: chosen.length, failed: 0, results: [] }
    },
    'POST /me/registry-matches/dismiss': () => { S.dismissed += 1; S.prompt = 'DISMISSED'; return null }
  })
  return S
}

describe('TC-E2E-920 微信用户绑定手机号 → 引导 → 确认', () => {
  it('绑定（匹配 12 套）→ 跳转我的房屋页 → 引导卡片置顶：折叠 10 + 已选 12 → 取消 2 套确认 10 套 → 房屋明细 10 行含类型与面积、引导与"无绑定"提醒消失、无"自动认证"提示', async () => {
    const S = server({ matches: POOL(12) })
    const phone = await mountPage(Phone)
    await phone.wrapper.findAll('input')[0].setValue('13900000005')
    await phone.wrapper.findAll('input')[1].setValue('123456')
    await byText(phone.wrapper, 'button', '绑定').trigger('click')
    await flushPromises()
    expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/units/index' })
    expect(toasts().join('|')).not.toContain('自动认证')
    expect(S.owned).toHaveLength(0)
    phone.wrapper.unmount()

    const { wrapper } = await mountPage(Units)
    expect(wrapper.find('#registry-match').exists()).toBe(true)
    expect(wrapper.findAll('.title')[0].text()).toBe('发现您名下的专有部分') // 置顶
    expect(wrapper.text()).toContain('您还没有认证任何专有部分，请先认证产权')
    expect(wrapper.find('#registry-match').findAll('.list-item')).toHaveLength(10)
    expect(wrapper.find('#registry-match').text()).toContain('展开更多（还有 2 套）')
    await wrapper.find('#registry-match').findAll('.link').find((e) => e.text().includes('展开更多')).trigger('click')
    await flushPromises()
    const items = wrapper.find('#registry-match').findAll('.list-item')
    expect(items).toHaveLength(12)
    await items[10].trigger('click')
    await items[11].trigger('click')
    await flushPromises()
    expect(wrapper.find('#registry-match').text()).toContain('已选 10 套')
    await byText(wrapper.find('#registry-match'), 'button', '是，确认认证').trigger('click')
    await flushPromises()
    expect(S.confirms).toEqual([{ unit_ids: POOL(12).slice(0, 10).map((u) => u.unit_id) }])
    expect(wrapper.find('#registry-match').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('您还没有认证任何专有部分')
    expect(wrapper.text()).toContain('汇总身份：产权业主')
    expect(wrapper.text()).toContain('车库B-1')
    expect(wrapper.text()).toContain('车位 · 10.00 ㎡')
    expect(wrapper.find('#review').exists()).toBe(true) // 产权业主：底部待审批卡片
  })
})

describe('TC-E2E-921 选择"不是"后不再弹出', () => {
  it('引导卡片点"不是"→ 无绑定且提醒仍在；再次进入"我的房屋"页（新实例）不再出现引导卡片，认证产权入口仍可用', async () => {
    const S = server({ matches: POOL(1) })
    const first = await mountPage(Units)
    expect(first.wrapper.text()).toContain('我们发现您的手机号登记在 车库B-1（车位）名下，您是该专有部分的业主吗？')
    await byText(first.wrapper.find('#registry-match'), 'button', '不是').trigger('click')
    await flushPromises()
    expect(S.dismissed).toBe(1)
    expect(S.owned).toHaveLength(0)
    expect(first.wrapper.find('#registry-match').exists()).toBe(false)
    expect(first.wrapper.text()).toContain('您还没有认证任何专有部分，请先认证产权')
    first.wrapper.unmount()
    const again = await mountPage(Units)
    expect(again.wrapper.find('#registry-match').exists()).toBe(false)
    expect(requests().filter((r) => r.path === '/me/registry-matches/confirm')).toHaveLength(0)
    expect(again.wrapper.find('#certify').exists()).toBe(true)
  })
})
