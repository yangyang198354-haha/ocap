// ocap_identity_property GROUP_D：手机号匹配清册引导面板、注册/绑定后的跳转、认证产权页与同住人申请页（MOD-137，IFC-342/343）。
// 层级：unit（页面级：单个组件 + 真实 store + 真实 api.js，仅 mock HTTP 层；TC-WEB-* 一律计入 unit 层）。TC-WEB-920 起。
// 溯源：US-236、US-238、US-239、US-240、US-241、US-243。合成数据（C-73）。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import RegistryMatchPanel from '@/portal/parts/RegistryMatchPanel.vue'
import UnitsPick from '@/portal/units/UnitsPick.vue'
import UnitsApplications from '@/portal/units/UnitsApplications.vue'
import Register from '@/portal/Register.vue'
import MePhone from '@/portal/me/MePhone.vue'

const { http } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const ME = { profile: { id: 1, nickname: '合成用户', phone: '138****0000' }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }
const HOUSING = { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 }
const mk = (n, type = '车位') => Array.from({ length: n }, (_, i) => ({ unit_id: 1000 + i, specific_part: `车库B-${i + 1}`, unit_type_label: type }))

function panelTable(units, over = {}) {
  return routeTable({
    '/me/registry-matches': { pending: units.length > 0, total: units.length, units },
    '/me': ME, '/me/housing': HOUSING, '/resident-applications/to-review': [], '/resident-applications/mine': [], '/appeals/mine': [], ...over
  })
}
const rows = (wrapper) => wrapper.findAll('.registry-match .row .el-checkbox')
const confirmPosts = () => http.post.mock.calls.filter((c) => c[0] === '/me/registry-matches/confirm')

beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

describe('引导面板展示（US-239）', () => {
  it('TC-WEB-920 / AC-239-01、AC-239-07：1 套——询问文案含坐落与类型；两个按钮"是，确认认证""不是"；不渲染接口多给的姓名/手机号', async () => {
    const unit = { unit_id: 1, specific_part: '1栋1单元9层902号', unit_type_label: '住宅', owner_name: '测试清册业主甲', phone: '13900000001' }
    http.get.mockImplementation(panelTable([unit]))
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    const text = wrapper.text()
    expect(text).toContain('我们发现您的手机号登记在 1栋1单元9层902号（住宅）名下，您是该专有部分的业主吗？')
    expect(buttonOf(wrapper, '是，确认认证')).toBeTruthy()
    expect(buttonOf(wrapper, '不是')).toBeTruthy()
    expect(text).not.toContain('测试清册业主甲')
    expect(text).not.toContain('13900000001')
    expect(wrapper.find('input').exists()).toBe(false) // 无需输入姓名（Q-IP-08=A）
  })

  it('TC-WEB-921 / AC-239-03、AC-239-08：pending=false 或接口失败——面板不渲染、不抛错', async () => {
    http.get.mockImplementation(panelTable([]))
    const none = await mountPage(RegistryMatchPanel)
    await flush()
    expect(none.wrapper.find('.registry-match').exists()).toBe(false)
    none.wrapper.unmount()
    document.body.innerHTML = ''
    http.get.mockReset()
    http.get.mockImplementation(async () => { throw { code: 'X', message: '失败' } })
    const failed = await mountPage(RegistryMatchPanel)
    await flush()
    expect(failed.wrapper.find('.registry-match').exists()).toBe(false)
  })

  it('TC-WEB-922 / AC-239-10：12 套——先显示 10 套 +"展开更多（还有 2 套）"，默认全选"已选 12 套"，展开后 12 套全显示且按钮消失', async () => {
    http.get.mockImplementation(panelTable(mk(12)))
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    expect(rows(wrapper)).toHaveLength(10)
    expect(wrapper.text()).toContain('展开更多（还有 2 套）')
    expect(wrapper.text()).toContain('已选 12 套')
    await buttonOf(wrapper, '展开更多').trigger('click')
    await flush()
    expect(rows(wrapper)).toHaveLength(12)
    expect(wrapper.text()).not.toContain('展开更多')
    expect(wrapper.findAll('.registry-match input[type=checkbox]').every((i) => i.element.checked)).toBe(true)
    expect(wrapper.text()).toContain('已选 12 套')
  })

  it('TC-WEB-923 / AC-239-11：恰 10 套不折叠（无"展开更多"）；11 套折叠 1 套；1 套为单句，2 套为列表', async () => {
    for (const [n, shown, more] of [[10, 10, null], [11, 10, '展开更多（还有 1 套）'], [2, 2, null]]) {
      document.body.innerHTML = ''
      http.get.mockReset()
      http.get.mockImplementation(panelTable(mk(n)))
      const { wrapper } = await mountPage(RegistryMatchPanel)
      await flush()
      expect(rows(wrapper), String(n)).toHaveLength(shown)
      if (more) expect(wrapper.text()).toContain(more)
      else expect(wrapper.text()).not.toContain('展开更多')
      expect(wrapper.text()).toContain(`已选 ${n} 套`)
      wrapper.unmount()
    }
    document.body.innerHTML = ''
    http.get.mockReset()
    http.get.mockImplementation(panelTable(mk(1)))
    const single = await mountPage(RegistryMatchPanel)
    await flush()
    expect(rows(single.wrapper)).toHaveLength(0)
    expect(single.wrapper.text()).toContain('您是该专有部分的业主吗')
  })
})

describe('引导面板操作（US-240）', () => {
  it('TC-WEB-924 / AC-240-02：3 套取消勾选第 3 套——"已选 2 套"，确认只提交 2 个 unit_ids（请求体只含 unit_ids，无姓名/手机号）', async () => {
    vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const units = mk(3, '住宅')
    http.get.mockImplementation(panelTable(units))
    http.post.mockResolvedValue({ succeeded: 2, failed: 0, results: [] })
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    await wrapper.findAll('.registry-match input[type=checkbox]')[2].setValue(false)
    await flush()
    expect(wrapper.text()).toContain('已选 2 套')
    await buttonOf(wrapper, '是，确认认证').trigger('click')
    await flush()
    expect(confirmPosts()).toEqual([['/me/registry-matches/confirm', { unit_ids: [1000, 1001] }]])
  })

  it('TC-WEB-925 / AC-240-03：取消勾选全部——"是，确认认证"禁用，点击不发请求', async () => {
    http.get.mockImplementation(panelTable(mk(2)))
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    for (const box of wrapper.findAll('.registry-match input[type=checkbox]')) await box.setValue(false)
    await flush()
    const btn = buttonOf(wrapper, '是，确认认证')
    expect(btn.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('已选 0 套')
    await btn.trigger('click')
    await flush()
    expect(confirmPosts()).toHaveLength(0)
  })

  it('TC-WEB-926 / AC-240-01、AC-241-02：单套确认成功——提示"认证成功，身份：产权业主"，刷新 /me 与房屋数据，面板消失并 emit resolved', async () => {
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    http.get.mockImplementation(panelTable(mk(1, '住宅')))
    http.post.mockResolvedValue({ succeeded: 1, failed: 0, results: [{ unit_id: 1000, specific_part: '车库B-1', ok: true, role: 'HEAD', code: null }] })
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    http.get.mockClear()
    await buttonOf(wrapper, '是，确认认证').trigger('click')
    await flush()
    expect(success).toHaveBeenCalledWith('认证成功，身份：产权业主')
    expect(http.get.mock.calls.map((c) => c[0])).toEqual(expect.arrayContaining(['/me', '/me/housing']))
    expect(wrapper.find('.registry-match').exists()).toBe(false)
    expect(wrapper.emitted('resolved')).toHaveLength(1)
    expect(wrapper.text()).not.toContain('户主')
  })

  it('TC-WEB-927 / AC-240-04：部分成功——警告"成功 1 套，未成功 1 套"，不弹错误；多套全成功提示"认证成功，共认证 N 套"', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    http.get.mockImplementation(panelTable(mk(2)))
    http.post.mockResolvedValueOnce({ succeeded: 1, failed: 1, results: [] })
    const first = await mountPage(RegistryMatchPanel)
    await flush()
    await buttonOf(first.wrapper, '是，确认认证').trigger('click')
    await flush()
    expect(warn).toHaveBeenCalledWith('成功 1 套，未成功 1 套')
    expect(error).not.toHaveBeenCalled()
    first.wrapper.unmount()
    document.body.innerHTML = ''
    http.post.mockResolvedValueOnce({ succeeded: 2, failed: 0, results: [] })
    const second = await mountPage(RegistryMatchPanel)
    await flush()
    await buttonOf(second.wrapper, '是，确认认证').trigger('click')
    await flush()
    expect(success).toHaveBeenCalledWith('认证成功，共认证 2 套')
  })

  it('TC-WEB-928 / AC-239-06：点"不是"——只 POST dismiss，不发 confirm，不绑定；面板关闭并 emit resolved', async () => {
    http.get.mockImplementation(panelTable(mk(1)))
    http.post.mockResolvedValue(null)
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    await buttonOf(wrapper, '不是').trigger('click')
    await flush()
    expect(http.post.mock.calls.map((c) => c[0])).toEqual(['/me/registry-matches/dismiss'])
    expect(wrapper.find('.registry-match').exists()).toBe(false)
    expect(wrapper.emitted('resolved')).toHaveLength(1)
  })

  it('TC-WEB-929 / AC-240-06：确认被服务端拒绝（422）——提示服务端文案，面板保留可再次操作，按钮恢复可点', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    http.get.mockImplementation(panelTable(mk(1)))
    http.post.mockRejectedValue({ code: 'OWNER_NOT_MATCHED', message: '未能通过清册核对', status: 422 })
    const { wrapper } = await mountPage(RegistryMatchPanel)
    await flush()
    await buttonOf(wrapper, '是，确认认证').trigger('click')
    await flush()
    expect(error).toHaveBeenCalled()
    expect(wrapper.find('.registry-match').exists()).toBe(true)
    expect(buttonOf(wrapper, '是，确认认证').attributes('disabled')).toBeUndefined()
  })
})

describe('注册 / 绑定手机号后的跳转（US-239、US-241）', () => {
  const submitRegister = async (result) => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    http.get.mockImplementation(routeTable({ '/me/theme': { theme: null } }))
    http.post.mockResolvedValue(result)
    const mounted = await mountPage(Register, { path: '/register' })
    mounted.wrapper.vm.form.phone = '13900000002'
    mounted.wrapper.vm.form.code = '123456'
    await mounted.wrapper.vm.submit()
    await flush()
    return mounted
  }

  it('TC-WEB-930 / AC-239-01、AC-241-01：注册返回 registry_match.pending → 提示"注册成功"并进入 /units/pick；不再出现"自动认证"提示', async () => {
    const { router } = await submitRegister({ token: 'T', user: { id: 2 }, auto_bound: [], registry_match: { pending: true, count: 1 } })
    expect(ElMessage.success).toHaveBeenCalledWith('注册成功')
    expect(ElMessage.success.mock.calls.flat().join('|')).not.toContain('自动认证')
    expect(router.currentRoute.value.path).toBe('/units/pick')
  })

  it('TC-WEB-931 / AC-239-03：注册无匹配（pending=false 或缺字段）→ 直接进入主页 /', async () => {
    for (const result of [{ token: 'T', user: { id: 2 }, auto_bound: [], registry_match: { pending: false, count: 0 } }, { token: 'T', user: { id: 2 } }]) {
      document.body.innerHTML = ''
      const { router } = await submitRegister(result)
      expect(router.currentRoute.value.path).toBe('/')
    }
  })

  it('TC-WEB-932 / AC-239-05、AC-239-12：首次绑定手机号匹配 → 进入 /units/pick；合并（merged=true）或无匹配 → 不跳转；换号不跳转', async () => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const run = async (result, hasPhone = false) => {
      document.body.innerHTML = ''
      http.get.mockReset()
      http.get.mockImplementation(routeTable({ '/me/profile': { nickname: '微信用户', gender: 0, phone: hasPhone ? '138****0000' : null, email: null }, '/me': ME }))
      http.post.mockResolvedValue(result)
      const mounted = await mountPage(MePhone, { path: '/me/phone' })
      if (hasPhone) {
        Object.assign(mounted.wrapper.vm.change, { oldPhone: '13800000000', newPhone: '13900000003', oldCode: '1', newCode: '2' })
        await mounted.wrapper.vm.changePhone()
      } else {
        Object.assign(mounted.wrapper.vm.bind, { phone: '13900000003', code: '123456' })
        await mounted.wrapper.vm.bindPhone()
      }
      await flush()
      return mounted.router.currentRoute.value.path
    }
    expect(await run({ merged: false, auto_bound: [], registry_match: { pending: true, count: 2 } })).toBe('/units/pick')
    // 客户端自身也须守住合并场景：即使响应误带 pending=true，merged=true 时也不跳转（AC-239-12）
    expect(await run({ merged: true, token: 'NEW', auto_bound: [], registry_match: { pending: true, count: 1 } })).toBe('/me/phone')
    expect(await run({ merged: false, auto_bound: [], registry_match: { pending: false, count: 0 } })).toBe('/me/phone')
    expect(await run({ merged: false, phone: '139****0003' }, true)).toBe('/me/phone')
    expect(ElMessage.success.mock.calls.flat().join('|')).not.toContain('自动认证')
  })
})

describe('认证产权页与同住人申请页（US-236、US-238、US-243）', () => {
  const pickTable = (over = {}) => panelTable([], { '/units/options': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }] }, ...over })

  it('TC-WEB-940 / AC-236-02、AC-238-01、AC-238-02：认证产权页——标题"认证产权"、姓名标签/占位为本人姓名、无"申请成为同住人"按钮、无"户主"、含指向 /units/applications 的提示链接', async () => {
    http.get.mockImplementation(pickTable())
    const { wrapper } = await mountPage(UnitsPick)
    await flush()
    expect(wrapper.find('h1').text()).toBe('认证产权')
    expect(wrapper.text()).toContain('您本人的姓名')
    expect(wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="请输入姓名"]').exists()).toBe(false)
    expect(buttonOf(wrapper, '申请成为同住人')).toBeUndefined()
    expect(wrapper.text()).not.toContain('户主')
    expect(wrapper.text()).not.toContain('选择房屋')
    const link = wrapper.findAll('a').find((a) => a.text().includes('我的同住人申请'))
    expect(link.attributes('href')).toBe('/units/applications')
    expect(wrapper.text()).toContain('如需申请成为同住人，请前往「我的同住人申请」')
  })

  it('TC-WEB-941 / AC-238-03、AC-238-04：姓名全空格——提示"请输入姓名"不发请求；OWNER_NOT_MATCHED——转申诉页并带入姓名，不显示清册信息', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    http.get.mockImplementation(pickTable())
    const { wrapper, router } = await mountPage(UnitsPick)
    await flush()
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 7)
    const input = wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]')
    await input.setValue('   ')
    await buttonOf(wrapper, '认证产权').trigger('click')
    await flush()
    expect(warn).toHaveBeenCalledWith('请输入姓名')
    expect(http.post.mock.calls.filter((c) => c[0] === '/certifications')).toHaveLength(0)
    await input.setValue('合成姓名')
    http.post.mockRejectedValue({ code: 'OWNER_NOT_MATCHED', message: '服务端文案', status: 422 })
    await buttonOf(wrapper, '认证产权').trigger('click')
    await flush()
    expect(warn).toHaveBeenCalledWith('姓名与手机号未能通过核对，请上传产权证明提交申诉')
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/units/appeal'))
  })

  it('TC-WEB-942 / AC-243-01、AC-243-02、AC-243-03、AC-297-01：我的同住人申请页——标题不变，发起区含实名说明与按钮；未选房屋按钮禁用；选定并填写实名后提交含 {unit_id, applicant_name}，成功提示并刷新列表', async () => {
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    let mine = []
    http.get.mockImplementation(pickTable({ '/resident-applications/mine': () => mine }))
    http.post.mockImplementation(async () => { mine = [{ id: 5, unit: { unit_id: 42, specific_part: '2栋2单元3层301号' }, status: 'PENDING', applicant_name: '张三', created_at: '2026-11-17T10:00:00+08:00', decided_at: null }]; return { id: 5, status: 'PENDING' } })
    const { wrapper } = await mountPage(UnitsApplications)
    await flush()
    expect(wrapper.find('h1').text()).toBe('我的同住人申请')
    expect(wrapper.text()).toContain('申请成为同住人须填写本人实名；同住人须先有产权业主，由产权业主审批')
    expect(wrapper.text()).toContain('暂无同住人申请')
    expect(wrapper.findAll('input').filter((i) => (i.attributes('placeholder') || '').includes('本人实名'))).toHaveLength(1)
    const btn = () => buttonOf(wrapper, '申请成为同住人')
    expect(btn().attributes('disabled')).toBeDefined()
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 42)
    await flush()
    expect(btn().attributes('disabled')).toBeUndefined()
    await wrapper.find('input[placeholder="本人实名"]').setValue('张三')
    await btn().trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/resident-applications', { unit_id: 42, applicant_name: '张三' })
    expect(success).toHaveBeenCalledWith('申请已提交，等待产权业主审批')
    expect(wrapper.text()).toContain('2栋2单元3层301号')
    expect(wrapper.text()).toContain('待审批')
  })

  it('TC-WEB-943 / AC-243-04、AC-243-05、AC-243-06：后端 409 三种拒绝（无产权业主 / 已是产权业主 / 已有待审）——提示后端文案，列表行数不变', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    http.get.mockImplementation(pickTable())
    const { wrapper } = await mountPage(UnitsApplications)
    await flush()
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 42)
    await flush()
    await wrapper.find('input[placeholder="本人实名"]').setValue('张三')
    for (const [code, message] of [['UNIT_HAS_NO_OWNER', '该专有部分暂无有效产权业主'], ['ALREADY_CERTIFIED', '已是该专有部分产权业主'], ['APPLICATION_PENDING', '已有待审申请']]) {
      http.post.mockRejectedValueOnce({ code, message, status: 409 })
      await buttonOf(wrapper, '申请成为同住人').trigger('click')
      await flush()
      expect(error.mock.calls.flat().join('|')).toContain(message)
    }
    expect(wrapper.text()).toContain('暂无同住人申请')
    expect(wrapper.text()).not.toContain('申请已提交')
  })
})
