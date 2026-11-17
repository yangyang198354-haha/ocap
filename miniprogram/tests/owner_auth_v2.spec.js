// ocap_owner_auth_v2 GROUP_D：小程序页面行为（MOD-118）。TC-MP-504 起。
// 页面脚本与模板经 @vue/test-utils 编译挂载；uni 为桩（setup.js），不代表微信真机行为；小程序构建与真机未验证（M-SD-006）。
// OQ-06：小程序申诉资料仅图片（uni.chooseImage），pdf 仅 Web——AC-201-01 小程序部分 PARTIAL，见 e2e_test_report 人工验证清单。
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { byText, mountPage, requests } from './helpers.js'
import Units from '../pages/units/index.vue'
import UnitPicker from '../components/UnitPicker.vue'

const toasts = () => uni.showToast.mock.calls.map((c) => c[0].title)
const HOUSING = { summary: { code: 'GUEST', label: '游客' }, pending_review_count: 0, units: [] }
const ME = { profile: { id: 1, nickname: '张三' }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }

/** 可返回非 200 状态的 uni.request 桩：table 值为 [statusCode, body] 或 body；未登记 404。 */
function respond(table) {
  uni.request.mockImplementation(({ url, method, data, success }) => {
    const path = url.replace(/^\/api\/v1/, '')
    const key = `${method} ${path}`
    const hit = table[key]
    if (hit === undefined) return success({ statusCode: 404, data: { code: 'NOT_FOUND', message: `未预期的请求 ${key}` } })
    const [statusCode, body] = Array.isArray(hit) ? hit : [200, typeof hit === 'function' ? hit(data) : hit]
    return success({ statusCode, data: body })
  })
}

const base = (over = {}) => ({
  'GET /me': ME, 'GET /me/housing': HOUSING, 'GET /resident-applications/to-review': [],
  'GET /resident-applications/mine': [], 'GET /appeals/mine': [], 'GET /units/options': { options: [] }, ...over
})
// 改写（ocap_identity_property GR-C-001-a，AC-238-01、AC-242-03）：姓名框占位由"请输入姓名"改为"请输入您本人的姓名（…）"；
// 页面新增"认证产权"按钮，旧用例的 byText('button','认证') 会先命中它，故认证按钮改按"文本恰为认证"精确查找
const NAME_PLACEHOLDER = '请输入您本人的姓名（须与业主清册登记的姓名一致）'
const certifyButton = (wrapper) => wrapper.findAll('button').find((b) => b.text() === '认证')
const inputs = (wrapper) => ({
  name: wrapper.findAll('input').find((i) => i.attributes('placeholder') === NAME_PLACEHOLDER),
  owner: wrapper.findAll('input').find((i) => i.attributes('placeholder') === '产权人名字')
})
const certifyPosts = () => requests().filter((r) => r.method === 'POST' && r.path === '/certifications')
const pickUnit = async (wrapper, id = 7) => {
  wrapper.findComponent(UnitPicker).vm.$emit('update:modelValue', id)
  await flushPromises()
}

describe('小程序 我的房屋：姓名核对与申诉', () => {
  it('TC-MP-504 / AC-200-02：未选房号提示"请先选择房号"；姓名为空/纯空格提示"请输入姓名"；都不发认证请求', async () => {
    respond(base())
    const { wrapper } = await mountPage(Units)
    await certifyButton(wrapper).trigger('click')
    await flushPromises()
    expect(toasts()).toContain('请先选择房号')
    await pickUnit(wrapper)
    await inputs(wrapper).name.setValue('   ')
    await certifyButton(wrapper).trigger('click')
    await flushPromises()
    expect(toasts()).toContain('请输入姓名')
    expect(certifyPosts()).toHaveLength(0)
  })

  it('TC-MP-505 / AC-200-01：姓名去首尾空格，POST /certifications {unit_id, name}；成功提示中文身份', async () => {
    respond(base({ 'POST /certifications': { unit_id: 7, role: 'HEAD' } }))
    const { wrapper } = await mountPage(Units)
    await pickUnit(wrapper, 7)
    await inputs(wrapper).name.setValue('  张三 ')
    await certifyButton(wrapper).trigger('click')
    await flushPromises()
    expect(certifyPosts()[0].data).toEqual({ unit_id: 7, name: '张三' })
    expect(toasts()).toContain('认证成功，身份：户主')
  })

  it('TC-MP-506 / AC-201-01/02、AC-199-04：OWNER_NOT_MATCHED → 提示转申诉，姓名带入"产权人名字"，不显示服务端文案里的清册信息', async () => {
    respond(base({ 'POST /certifications': [422, { code: 'OWNER_NOT_MATCHED', message: '清册该户业主为李某某 138****0001', details: { appeal_available: true } }] }))
    const { wrapper } = await mountPage(Units)
    await pickUnit(wrapper, 7)
    await inputs(wrapper).name.setValue('张三')
    await certifyButton(wrapper).trigger('click')
    await flushPromises()
    expect(toasts()).toContain('姓名与手机号未能通过核对，请上传产权证明提交申诉')
    expect(toasts().join('|')).not.toMatch(/李某某|138/)
    expect(inputs(wrapper).owner.element.value).toBe('张三')
    expect(wrapper.text()).not.toContain('李某某')
  })

  it('TC-MP-507 / AC-199-02、AC-201-04：申诉——产权人名字为空提示"请输入产权人名字"；有名字无资料提示"请先上传产权证明"；都不发 POST /appeals', async () => {
    respond(base())
    const { wrapper } = await mountPage(Units)
    await pickUnit(wrapper)
    await byText(wrapper, 'button', '提交申诉').trigger('click')
    await flushPromises()
    expect(toasts()).toContain('请输入产权人名字')
    await inputs(wrapper).owner.setValue('王五')
    await byText(wrapper, 'button', '提交申诉').trigger('click')
    await flushPromises()
    expect(toasts()).toContain('请先上传产权证明')
    expect(requests().filter((r) => r.path === '/appeals')).toHaveLength(0)
  })

  it('TC-MP-508 / AC-199-01、OQ-06：多图上传——chooseImage 剩余张数递减（5→3），逐张 uploadFile(APPEAL_PROOF)，提交 {unit_id, owner_name, proof_ids}；满 5 张后不再弹选择', async () => {
    respond(base({ 'POST /appeals': { id: 3, status: 'PENDING' } }))
    let n = 0
    uni.uploadFile.mockImplementation(({ success }) => success({ statusCode: 201, data: JSON.stringify({ id: `att-${++n}` }) }))
    const { wrapper } = await mountPage(Units)
    await pickUnit(wrapper, 7)
    uni.chooseImage.mockImplementation(({ success, count }) => success({ tempFilePaths: Array.from({ length: Math.min(count, 2) }, (_, i) => `/tmp/${i}.png`) }))
    await byText(wrapper, 'button', '上传产权证明').trigger('click')
    await flushPromises()
    expect(uni.chooseImage.mock.calls[0][0].count).toBe(5)
    expect(uni.uploadFile.mock.calls.map((c) => c[0].formData.purpose)).toEqual(['APPEAL_PROOF', 'APPEAL_PROOF'])
    await byText(wrapper, 'button', '继续添加').trigger('click')
    await flushPromises()
    expect(uni.chooseImage.mock.calls[1][0].count).toBe(3)
    await byText(wrapper, 'button', '继续添加').trigger('click')
    await flushPromises()
    expect(uni.chooseImage.mock.calls[2][0].count).toBe(1)
    expect(n).toBe(5)
    uni.chooseImage.mockClear()
    await byText(wrapper, 'button', '继续添加').trigger('click')
    await flushPromises()
    expect(uni.chooseImage).not.toHaveBeenCalled()
    expect(toasts()).toContain('最多上传 5 张产权证明')
    await inputs(wrapper).owner.setValue(' 王五 ')
    await byText(wrapper, 'button', '提交申诉').trigger('click')
    await flushPromises()
    const post = requests().find((r) => r.method === 'POST' && r.path === '/appeals')
    expect(post.data).toEqual({ unit_id: 7, owner_name: '王五', proof_ids: ['att-1', 'att-2', 'att-3', 'att-4', 'att-5'] })
    expect(toasts()).toContain('申诉已提交')
  })

  it('TC-MP-509 / IFC-314：提示文案不再要求先绑定手机号；无手机号也可输入产权人名字申诉', async () => {
    respond(base())
    const { wrapper } = await mountPage(Units)
    expect(wrapper.text()).toContain('没有手机号时，请在下方输入产权人名字并上传产权证明提交申诉')
    expect(wrapper.text()).not.toMatch(/请先绑定手机号/)
  })
})

describe('小程序 UnitPicker：商铺第二级显示名', () => {
  const optionsFor = (params) => {
    const key = [params.building, params.unit_no].filter((v) => v !== undefined).join('|')
    return {
      '': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }, { value: '地下车位' }, { value: '商铺' }] },
      '商铺': { level: 'unit_no', skipped: [], has_empty: false, level_label: '楼栋/门牌', options: [{ value: '1栋' }, { value: '建设南路142号' }] },
      '1': { level: 'unit_no', skipped: [], has_empty: false, options: [{ value: '1' }] }
    }[key]
  }
  const mountPicker = async () => {
    uni.request.mockImplementation(({ data, success }) => {
      success({ statusCode: 200, data: optionsFor(data || {}) })
    })
    const { wrapper } = await mountPage(UnitPicker)
    await flushPromises()
    return wrapper
  }

  it('TC-MP-510 / IFC-300、AC-194-01/04：选"商铺"后第二级标签为"楼栋/门牌"；改选 1 栋后复位为"单元"', async () => {
    const wrapper = await mountPicker()
    const pickers = () => wrapper.findAll('picker')
    expect(pickers()).toHaveLength(2) // 楼栋 + 房号
    await pickers()[0].trigger('change', { detail: { value: 2 } })
    await flushPromises()
    expect(wrapper.text()).toContain('楼栋/门牌：请选择')
    expect(wrapper.text()).not.toContain('单元：')
    await pickers()[0].trigger('change', { detail: { value: 0 } })
    await flushPromises()
    expect(wrapper.text()).toContain('单元：请选择')
    expect(wrapper.text()).not.toContain('楼栋/门牌：')
  })
})
