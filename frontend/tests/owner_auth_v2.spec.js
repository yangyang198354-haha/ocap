// ocap_owner_auth_v2 GROUP_D：Web 前端组件测试（真实页面 + 真实 api.js + 真实 store，仅 mock HTTP 层）。
// 覆盖 MOD-117：Units（姓名输入/转申诉/多附件）、UnitCascader（level_label）、AdminAppeals、ProofThumbs（懒加载/弹窗/pdf/权限）、AdminSeats（待生效）。
// TC-UNIT-667 起。jsdom 无 createImageBitmap / IntersectionObserver / URL.createObjectURL：用桩，行为不代表真实浏览器（CR-001，需 E2 人工核对）。
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import UnitsPick from '@/portal/units/UnitsPick.vue'
import UnitsAppeal from '@/portal/units/UnitsAppeal.vue'
import { useHousingStore } from '@/stores/housing'
import UnitCascader from '@/portal/parts/UnitCascader.vue'
import AdminAppeals from '@/admin/AdminAppeals.vue'
import AdminSeats from '@/admin/AdminSeats.vue'
import ProofThumbs from '@/admin/parts/ProofThumbs.vue'

const { http, adminHttp } = mocked
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }

const HEAD_UNIT = { unit_id: 1, specific_part: '1栋1单元3层301号', role: 'HEAD', role_label: '户主', certified_at: '2026-01-01T00:00:00+08:00' }
const HOUSING = { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 }
const unitsTable = (over = {}) => routeTable({
  '/me': { profile: { id: 1, nickname: '张三' }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } },
  '/me/housing': HOUSING, '/me/registry-matches': { pending: false, total: 0, units: [] }, '/resident-applications/to-review': [], '/resident-applications/mine': [], '/appeals/mine': [],
  '/units/options': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }] }, ...over
})

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})

let objectUrls = 0
beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
  objectUrls = 0
  URL.createObjectURL = vi.fn(() => `blob:mock/${++objectUrls}`)
  URL.revokeObjectURL = vi.fn()
})

// ------------------------------------------------------------------ 我的房屋：姓名输入与转申诉（US-199~202）
// 改写（ocap_identity_property GR-C-001-a，AC-238-01）：姓名框占位由"请输入姓名"改为"请输入您本人的姓名（须与业主清册登记的姓名一致）"，
// 旧断言按旧占位取元素 → 新断言按新占位取元素；"请输入姓名"仍是姓名为空时的提示文案（AC-238-03），原断言不变。
// 分区同步（ocap_brand_layout MOD-123）：原 Units.vue 整页拆为 UnitsPick（认证产权）与 UnitsAppeal（认证申诉，自带房屋选择），
// 用例原意与断言不变，仅改挂载对象；TC-669 的"已选房屋保留"按 OQ-B03 改为"只带姓名、房屋需重选、未选房屋禁用提交"。
describe('Units 分区页 姓名核对与申诉（UnitsPick / UnitsAppeal）', () => {
  const mountWithUnit = async (component, unitId = 7, over = {}) => {
    http.get.mockImplementation(unitsTable(over))
    const { wrapper, router, pinia } = await mountPage(component)
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', unitId)
    await flush()
    return { wrapper, router, pinia }
  }
  const certifyPosts = () => http.post.mock.calls.filter((c) => c[0] === '/certifications')

  it('TC-UNIT-667 / AC-200-02：姓名为空或纯空格点"认证产权"——提示"请输入姓名"，不发起认证请求', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const { wrapper } = await mountWithUnit(UnitsPick)
    await buttonOf(wrapper, '认证产权').trigger('click')
    await flush()
    await wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]').setValue('   ')
    await buttonOf(wrapper, '认证产权').trigger('click')
    await flush()
    expect(warn).toHaveBeenCalledWith('请输入姓名')
    expect(warn).toHaveBeenCalledTimes(2)
    expect(certifyPosts()).toHaveLength(0)
  })

  it('TC-UNIT-668 / AC-200-01：姓名去首尾空格后随 unit_id 提交 POST /certifications {unit_id, name}', async () => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountWithUnit(UnitsPick, 7)
    http.post.mockResolvedValue({ unit_id: 7, role: 'HEAD' })
    await wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]').setValue('  张三 ')
    await buttonOf(wrapper, '认证产权').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/certifications', { unit_id: 7, name: '张三' })
  })

  it('TC-UNIT-669 / AC-201-01/02、AC-199-04：OWNER_NOT_MATCHED → 提示转申诉页，只带姓名（房屋需重选，OQ-B03），姓名带入"产权人名字"，未选房屋时禁用提交，不弹错误、不显示服务端文案里的清册信息', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper, router, pinia } = await mountWithUnit(UnitsPick, 7)
    http.post.mockRejectedValue({ code: 'OWNER_NOT_MATCHED', message: '清册该户业主为李某某 138****0001', details: { appeal_available: true } })
    await wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]').setValue('张三')
    await buttonOf(wrapper, '认证产权').trigger('click')
    await flush()
    expect(warn).toHaveBeenCalledWith('姓名与手机号未能通过核对，请上传产权证明提交申诉')
    expect(error).not.toHaveBeenCalled()
    expect(router.currentRoute.value.path).toBe('/units/appeal')
    expect(useHousingStore(pinia).prefillOwnerName).toBe('张三')
    expect(wrapper.text()).not.toContain('李某某')
    expect(JSON.stringify(warn.mock.calls)).not.toContain('138')
    // 跳转后的申诉页：姓名已带入，仓库预填被消费，房屋需重新选择 → 提交申诉禁用，选房后可用
    const next = await mountPage(UnitsAppeal, { pinia })
    expect(next.wrapper.find('input[placeholder="产权人名字"]').element.value).toBe('张三')
    expect(useHousingStore(pinia).prefillOwnerName).toBe('')
    expect(buttonOf(next.wrapper, '提交申诉').attributes('disabled')).toBeDefined()
    next.wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 7)
    await flush()
    expect(buttonOf(next.wrapper, '提交申诉').attributes('disabled')).toBeUndefined()
  })

  it('TC-UNIT-670 / AC-199-02、AC-201-04：申诉——产权人名字为空提示"请输入产权人名字"；有名字但未上传资料提示"请先上传产权证明"；都不发 POST /appeals', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const { wrapper } = await mountWithUnit(UnitsAppeal, 7)
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(warn).toHaveBeenLastCalledWith('请输入产权人名字')
    await wrapper.find('input[placeholder="产权人名字"]').setValue('王五')
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(warn).toHaveBeenLastCalledWith('请先上传产权证明')
    expect(http.post.mock.calls.filter((c) => c[0] === '/appeals')).toHaveLength(0)
  })

  const upload = async (wrapper, name) => {
    const handler = wrapper.findComponent({ name: 'ElUpload' }).props('httpRequest')
    await handler({ file: new File(['x'], name, { type: 'image/png' }) })
    await flush()
  }

  it('TC-UNIT-671 / AC-199-01、AC-201-01：多附件——上传 2 份后提交 POST /appeals {unit_id, owner_name, proof_ids:[a1,a2]}；提交后清空已选附件', async () => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountWithUnit(UnitsAppeal, 7)
    let n = 0
    http.post.mockImplementation(async (url) => (url === '/attachments' ? { id: `a${++n}` } : { id: 99, status: 'PENDING' }))
    await upload(wrapper, 'p1.png')
    await upload(wrapper, 'p2.pdf')
    expect(wrapper.text()).toContain('已上传 2 份')
    await wrapper.find('input[placeholder="产权人名字"]').setValue(' 王五 ')
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/appeals', { unit_id: 7, owner_name: '王五', proof_ids: ['a1', 'a2'] })
    expect(wrapper.text()).not.toContain('已上传 2 份')
    const uploads = http.post.mock.calls.filter((c) => c[0] === '/attachments')
    expect(uploads.map((c) => c[1].get('purpose'))).toEqual(['APPEAL_PROOF', 'APPEAL_PROOF'])
  })

  it('TC-UNIT-672 / AC-198-03、C-62：最多 5 份——第 6 份被拦并提示"最多上传 5 份产权证明"，不再发上传请求', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountWithUnit(UnitsAppeal, 7)
    let n = 0
    http.post.mockImplementation(async () => ({ id: `a${++n}` }))
    for (let i = 0; i < 6; i += 1) await upload(wrapper, `p${i}.png`)
    expect(http.post.mock.calls.filter((c) => c[0] === '/attachments')).toHaveLength(5)
    expect(warn).toHaveBeenCalledWith('最多上传 5 份产权证明')
    expect(wrapper.text()).toContain('已上传 5 份')
  })

  it('TC-UNIT-673 / AC-199-03、IFC-313：提示文案不再要求先绑定手机号，改为无手机号也可申诉（文案由"下方产权申诉"改为"认证申诉"二级页）', async () => {
    const pick = await mountWithUnit(UnitsPick, 7)
    expect(pick.wrapper.text()).toContain('没有手机号时，请改用"认证申诉"')
    expect(pick.wrapper.text()).toContain('无手机号也可申诉')
    expect(pick.wrapper.text()).not.toMatch(/请先绑定手机号|先绑定手机/)
    const appeal = await mountWithUnit(UnitsAppeal, 7)
    expect(appeal.wrapper.text()).not.toMatch(/请先绑定手机号|先绑定手机/)
    expect(appeal.wrapper.text()).toContain('jpg/png/pdf')
  })
})

// ------------------------------------------------------------------ 逐级选房（US-193/194）
describe('UnitCascader.vue 商铺第二级', () => {
  const optionsTable = {
    '': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }, { value: '2' }, { value: '地下车位' }, { value: '商铺' }] },
    '商铺': { level: 'unit_no', skipped: [], has_empty: false, level_label: '楼栋/门牌', options: [{ value: '1栋' }, { value: '2栋' }, { value: '建设南路142号' }] },
    '2': { level: 'unit_no', skipped: [], has_empty: true, options: [{ value: '1' }] },
    '商铺|建设南路142号': { level: 'room', skipped: ['floor'], has_empty: false, options: [{ value: '1', unit_id: 55, label: '1（商铺）' }] }
  }
  const mountCascader = async () => {
    http.get.mockImplementation(async (url, arg) => {
      const p = arg?.params || {}
      const key = [p.building, p.unit_no].filter((v) => v !== undefined).join('|')
      const hit = optionsTable[key]
      if (!hit) throw new Error(`未预期的 options 请求 ${JSON.stringify(p)}`)
      return hit
    })
    const { wrapper } = await mountPage(UnitCascader)
    await flush()
    return wrapper
  }
  const selects = (wrapper) => wrapper.findAllComponents({ name: 'ElSelect' })
  const choose = async (select, value) => {
    select.vm.$emit('update:modelValue', value)
    select.vm.$emit('change', value)
    await flush()
  }

  it('TC-UNIT-674 / AC-193-01、AC-194-01：第一级选项依次为 1、2、地下车位、商铺；选"商铺"后第二级占位为"楼栋/门牌"，选项为原楼栋/门牌', async () => {
    const wrapper = await mountCascader()
    expect(selects(wrapper)).toHaveLength(1)
    await choose(selects(wrapper)[0], '商铺')
    expect(selects(wrapper)).toHaveLength(2)
    expect(selects(wrapper)[1].props('placeholder')).toBe('楼栋/门牌')
    const labels = wrapper.findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))
    expect(labels).toEqual(expect.arrayContaining(['1', '2', '地下车位', '商铺', '1栋', '2栋', '建设南路142号']))
    expect(labels.indexOf('地下车位')).toBeLessThan(labels.indexOf('商铺'))
  })

  it('TC-UNIT-675 / AC-194-04：选"商铺"后改选 2 栋——第二级占位复位为"单元"，不残留商铺的原楼栋选项', async () => {
    const wrapper = await mountCascader()
    await choose(selects(wrapper)[0], '商铺')
    await choose(selects(wrapper)[0], '2')
    expect(selects(wrapper)[1].props('placeholder')).toBe('单元')
    const labels = wrapper.findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))
    expect(labels).not.toContain('建设南路142号')
    expect(labels).not.toContain('1栋')
  })

  it('TC-UNIT-676 / AC-194-02：门牌型商铺（无楼层）——选定原楼栋/门牌后空楼层自动跳过，直接出现户号选择，选定后得到 unit_id', async () => {
    const wrapper = await mountCascader()
    await choose(selects(wrapper)[0], '商铺')
    await choose(selects(wrapper)[1], '建设南路142号')
    expect(selects(wrapper)).toHaveLength(3) // 楼栋、楼栋/门牌、户号；无楼层
    expect(selects(wrapper)[2].props('placeholder')).toBe('户号')
    await choose(selects(wrapper)[2], 55)
    expect(wrapper.emitted('update:modelValue').pop()).toEqual([55])
  })
})

// ------------------------------------------------------------------ 后台申诉列表（US-197/198/203）
describe('AdminAppeals.vue', () => {
  const FULL = {
    id: 123, status: 'PENDING', submitted_at: '2026-11-16T10:00:00+08:00', decided_at: null, reject_reason: null,
    unit: { unit_id: 5, specific_part: '商铺建设南路142号1号' }, owner_name: '张三',
    applicant: { id: 9, account_no: 'A001', nickname: '小明', phone: '138****0009', has_phone: true },
    proof: [{ id: 'f1', name: 'a.png', size: 10, content_type: 'image/png' }, { id: 'f2', name: 'b.png', size: 10, content_type: 'image/png' },
      { id: 'f3', name: 'c.pdf', size: 10, content_type: 'application/pdf' }]
  }
  const LEGACY = {
    id: 124, status: 'PENDING', submitted_at: '2026-11-01T09:00:00+08:00', decided_at: null, reject_reason: null,
    unit: { unit_id: 6, specific_part: '1栋1单元3层302号' }, owner_name: null,
    applicant: { id: 10, account_no: 'A002', nickname: null, phone: null, has_phone: false }, proof: []
  }
  const mountAppeals = async (rows = [FULL, LEGACY]) => {
    adminHttp.get.mockImplementation(async (url) => {
      if (url === '/admin/appeals') return { count: rows.length, results: rows }
      if (url.startsWith('/attachments/')) return new Blob(['x'])
      throw new Error(`未预期的请求 ${url}`)
    })
    const { wrapper } = await mountPage(AdminAppeals)
    await flush()
    return wrapper
  }

  it('TC-UNIT-677 / AC-197-01：每条申诉显示"申诉编码 #123"、账号、昵称、产权人名字、申诉时间、专有部分坐落、缩略图格数=资料数；无完整手机号', async () => {
    const wrapper = await mountAppeals()
    const first = wrapper.findAll('.list-item')[0]
    expect(first.text()).toContain('申诉编码 #123')
    expect(first.text()).toContain('账号：A001')
    expect(first.text()).toContain('昵称：小明')
    expect(first.text()).toContain('产权人名字：张三')
    expect(first.text()).toContain('申诉时间：2026-11-16 10:00')
    expect(first.text()).toContain('商铺建设南路142号1号')
    expect(first.findAll('.proof-cell')).toHaveLength(3)
    expect(wrapper.text()).not.toMatch(/1[3-9]\d{9}/)
  })

  it('TC-UNIT-678 / AC-197-02/03：无昵称显示"未设置"；旧申诉无产权人名字显示"未提供"；无资料不渲染缩略图区；页面无报错', async () => {
    const wrapper = await mountAppeals()
    const second = wrapper.findAll('.list-item')[1]
    expect(second.text()).toContain('昵称：未设置')
    expect(second.text()).toContain('产权人名字：未提供')
    expect(second.findAll('.proof-cell')).toHaveLength(0)
  })

  it('TC-UNIT-679 / AC-203-02：待审且申请人无手机号显示提示；通过后请求 decision=APPROVE，响应 notice 以 warning 展示并重新加载', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const wrapper = await mountAppeals()
    const second = wrapper.findAll('.list-item')[1]
    expect(second.text()).toContain('申诉人无手机号：通过后清册只写姓名、不写联系电话')
    expect(wrapper.findAll('.list-item')[0].text()).not.toContain('申诉人无手机号')
    adminHttp.post.mockResolvedValue({ status: 'APPROVED', registry_update: { result: 'OWNER_ADDED', owner_phone_written: false, notice: '该产权人无联系电话' } })
    const before = adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/appeals').length
    await second.findAll('button').find((b) => b.text() === '通过').trigger('click')
    await flush()
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/appeals/124/decision', { decision: 'APPROVE', reject_reason: undefined })
    expect(warn).toHaveBeenCalledWith('该产权人无联系电话')
    expect(adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/appeals').length).toBe(before + 1)
  })

  it('TC-UNIT-680 / AC-203-04/05：通过失败（PHONE_OWNED_BY_OTHER / REGISTRY_UPDATE_FAILED）→ 展示服务端提示、不提示"已处理"，列表数据保持原位（不重新加载）', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const wrapper = await mountAppeals()
    for (const [code, message] of [['PHONE_OWNED_BY_OTHER', '该手机号已登记在本专有部分的另一位业主名下，无法更新清册'], ['REGISTRY_UPDATE_FAILED', '清册更新失败，申诉保持待审']]) {
      adminHttp.post.mockRejectedValueOnce({ code, message })
      const before = adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/appeals').length
      await wrapper.findAll('.list-item')[0].findAll('button').find((b) => b.text() === '通过').trigger('click')
      await flush()
      expect(error).toHaveBeenLastCalledWith(message)
      expect(adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/appeals').length).toBe(before)
    }
    expect(success).not.toHaveBeenCalled()
    expect(wrapper.findAll('.list-item')).toHaveLength(2)
  })

  it('TC-UNIT-681 / AC-198-01：点击第 2 张缩略图弹出大图（取该资料原图），上一份/下一份可切换；关闭后列表不重新加载、筛选保持', async () => {
    const wrapper = await mountAppeals()
    const listCalls = () => adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/appeals').length
    const before = listCalls()
    await wrapper.findAll('.proof-cell')[1].trigger('click')
    await flush()
    const dialog = document.body
    expect(dialog.textContent).toContain('b.png')
    expect(dialog.querySelector('img.proof-large')).not.toBeNull()
    expect(adminHttp.get).toHaveBeenCalledWith('/attachments/f2/download', { responseType: 'blob' })
    const next = [...dialog.querySelectorAll('button')].find((b) => b.textContent.includes('下一份'))
    next.click()
    await flush()
    expect(dialog.textContent).toContain('c.pdf')
    expect(dialog.querySelector('iframe.proof-frame')).not.toBeNull() // 第 3 份是 pdf
    const prev = [...dialog.querySelectorAll('button')].find((b) => b.textContent.includes('上一份'))
    prev.click()
    prev.click()
    await flush()
    expect(dialog.textContent).toContain('a.png')
    const close = [...dialog.querySelectorAll('button')].find((b) => b.textContent.trim() === '关闭')
    close.click()
    await flush()
    expect(listCalls()).toBe(before)
    expect(wrapper.find('.el-select').exists()).toBe(true)
    expect(wrapper.findAll('.list-item')).toHaveLength(2)
  })
})

// ------------------------------------------------------------------ ProofThumbs（US-198；CR-001）
describe('ProofThumbs.vue', () => {
  const proofs = (n, type = 'image/png') => Array.from({ length: n }, (_, i) => ({ id: `p${i + 1}`, name: `proof${i + 1}.${type.includes('pdf') ? 'pdf' : 'png'}`, size: 10, content_type: type }))
  const mountThumbs = async (list) => {
    const { wrapper } = await mountPage({ components: { ProofThumbs }, setup: () => ({ list }), template: '<ProofThumbs :proofs="list" />' })
    await flush()
    return wrapper
  }

  it('TC-UNIT-682 / AC-198-03、IFC-315：5 份图片资料恰显示 5 个缩略图格；经管理端下载接口取回（无公开地址）；并发不超过 3', async () => {
    let inflight = 0
    let peak = 0
    const gates = []
    adminHttp.get.mockImplementation((url) => new Promise((resolve) => {
      inflight += 1
      peak = Math.max(peak, inflight)
      gates.push(() => { inflight -= 1; resolve(new Blob(['x'])) })
    }))
    const wrapper = await mountThumbs(proofs(5))
    expect(wrapper.findAll('.proof-cell')).toHaveLength(5)
    expect(peak).toBeLessThanOrEqual(3)
    expect(adminHttp.get).toHaveBeenCalledTimes(3)
    while (gates.length) { gates.shift()(); await flush() }
    expect(adminHttp.get).toHaveBeenCalledTimes(5)
    expect(peak).toBeLessThanOrEqual(3)
    expect(adminHttp.get.mock.calls.map((c) => c[0]).sort()).toEqual([1, 2, 3, 4, 5].map((i) => `/attachments/p${i}/download`))
    expect(wrapper.findAll('img.proof-img')).toHaveLength(5)
  })

  it('TC-UNIT-683 / AC-198-02：pdf 资料显示文件图标与文件名、不取缩略图；点击后弹出 iframe 预览并提供下载入口（download=文件名）', async () => {
    adminHttp.get.mockResolvedValue(new Blob(['%PDF']))
    const wrapper = await mountThumbs(proofs(1, 'application/pdf'))
    expect(wrapper.find('.proof-icon').text()).toBe('PDF')
    expect(wrapper.find('.proof-name').text()).toBe('proof1.pdf')
    expect(wrapper.find('img.proof-img').exists()).toBe(false)
    expect(adminHttp.get).not.toHaveBeenCalled()
    await wrapper.find('.proof-cell').trigger('click')
    await flush()
    expect(document.body.querySelector('iframe.proof-frame')).not.toBeNull()
    const link = document.body.querySelector('a[download]')
    expect(link.getAttribute('download')).toBe('proof1.pdf')
  })

  it('TC-UNIT-684 / AC-198-04、REQ-NFUNC-034：取回被拒（403/401）——缩略图格显示错误文案、不渲染任何 img；大图弹层显示"预览失败"且无 img/iframe', async () => {
    adminHttp.get.mockRejectedValue({ code: 'FORBIDDEN', message: '无权查看该资料' })
    const wrapper = await mountThumbs(proofs(2))
    expect(wrapper.findAll('img')).toHaveLength(0)
    expect(wrapper.findAll('.proof-error').map((e) => e.text())).toEqual(['无权查看该资料', '无权查看该资料'])
    await wrapper.findAll('.proof-cell')[0].trigger('click')
    await flush()
    expect(document.body.textContent).toContain('预览失败：无权查看该资料')
    expect(document.body.querySelector('img.proof-large')).toBeNull()
    expect(document.body.querySelector('iframe')).toBeNull()
  })

  it('TC-UNIT-685 / IFC-315：弹层关闭与组件卸载释放对象地址（revokeObjectURL），防内存泄漏', async () => {
    adminHttp.get.mockResolvedValue(new Blob(['x']))
    const wrapper = await mountThumbs(proofs(1))
    await wrapper.find('.proof-cell').trigger('click')
    await flush()
    const created = URL.createObjectURL.mock.calls.length
    expect(created).toBeGreaterThanOrEqual(2) // 缩略图 + 大图
    const close = [...document.body.querySelectorAll('button')].find((b) => b.textContent.trim() === '关闭')
    close.click()
    await flush()
    wrapper.unmount()
    expect(URL.revokeObjectURL.mock.calls.length).toBeGreaterThanOrEqual(created)
  })

  it('TC-UNIT-686 / IFC-315：浏览器支持 IntersectionObserver 时只在进入可视区后才取回缩略图（懒加载）', async () => {
    const observed = []
    let callback
    global.IntersectionObserver = class {
      constructor(cb) { callback = cb }
      observe(el) { observed.push(el) }
      unobserve() {}
      disconnect() {}
    }
    try {
      adminHttp.get.mockResolvedValue(new Blob(['x']))
      const wrapper = await mountThumbs(proofs(4))
      expect(observed).toHaveLength(4)
      expect(adminHttp.get).not.toHaveBeenCalled()
      callback([{ isIntersecting: true, target: observed[1] }])
      await flush()
      expect(adminHttp.get).toHaveBeenCalledTimes(1)
      expect(adminHttp.get.mock.calls[0][0]).toBe('/attachments/p2/download')
      callback([{ isIntersecting: false, target: observed[2] }])
      await flush()
      expect(adminHttp.get).toHaveBeenCalledTimes(1)
      wrapper.unmount()
    } finally {
      delete global.IntersectionObserver
    }
  })
})

// ------------------------------------------------------------------ 席位页（US-206）
describe('AdminSeats.vue 待生效', () => {
  const seat = (over) => ({ id: 1, user: { id: 7, nickname: '甲' }, position: 'MEMBER', status: 'ACTIVE', effective: true, term_start: '2026-01-01', term_end: '2028-01-01', ...over })
  const mountSeats = async (rows) => {
    adminHttp.get.mockImplementation(routeTable({ '/admin/committee/seats': { count: rows.length, results: rows }, '/admin/committee/config': { term_months_member: 36 } }))
    const { wrapper } = await mountPage(AdminSeats)
    await flush()
    return wrapper
  }

  it('TC-UNIT-687 / AC-206-01：在任但未到开始日（effective=false）的席位显示"待生效"；已生效与已结束席位不显示', async () => {
    const wrapper = await mountSeats([
      seat({ id: 1, user: { id: 7, nickname: '未来甲' }, effective: false, term_start: '2026-12-01' }),
      seat({ id: 2, user: { id: 8, nickname: '现任乙' }, effective: true }),
      seat({ id: 3, user: { id: 9, nickname: '已结束丙' }, status: 'EXPIRED', effective: false })
    ])
    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].text()).toContain('待生效')
    expect(rows[1].text()).not.toContain('待生效')
    expect(rows[2].text()).not.toContain('待生效')
    expect(wrapper.text()).not.toMatch(/ACTIVE|EXPIRED/)
  })

  it('TC-UNIT-688 / AC-205-01：赋予对话框不再要求开始日不早于今天——日期选择器无 disabledDate，提示"结束日须晚于今天"', async () => {
    const wrapper = await mountSeats([])
    await buttonOf(wrapper, '赋予席位').trigger('click')
    await flush()
    expect(document.body.textContent).toContain('须晚于今天')
    expect(document.body.textContent).not.toContain('不得早于今天')
    const picker = wrapper.findAllComponents({ name: 'ElDatePicker' })[0] || document.body.querySelector('.el-date-editor')
    expect(picker).toBeTruthy()
    if (picker.props) expect(picker.props('disabledDate')).toBeUndefined()
  })
})
