// ocap_product_review GROUP_D：界面行为（[UI] 标记的 AC）与前端侧 E2E 可测部分。
// 真实页面 + 真实 api.js + 真实 store，仅 mock HTTP 层与 ElMessageBox.confirm。TC-UNIT-522 起；跨页面/路由的为 TC-INT。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
const messageBox = vi.hoisted(() => ({ confirm: vi.fn() }))
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, ElMessageBox: { ...actual.ElMessageBox, confirm: messageBox.confirm } }
})

import { mountPage, routeTable } from './helpers.js'
import { useAuthStore } from '@/stores/auth'
import Units from '@/portal/Units.vue'
import UnitsPick from '@/portal/units/UnitsPick.vue'
import UnitsReview from '@/portal/units/UnitsReview.vue'
import UnitsApplications from '@/portal/units/UnitsApplications.vue'
import UnitsMyAppeals from '@/portal/units/UnitsMyAppeals.vue'
import UnitsIdentity from '@/portal/units/UnitsIdentity.vue' // 改写：MeIdentity.vue 已删除，身份卡由 UnitsIdentity 承载（ADR-132）
import MeProfile from '@/portal/me/MeProfile.vue'
import MeCancel from '@/portal/me/MeCancel.vue'
import Login from '@/portal/Login.vue'
import Polls from '@/portal/Polls.vue'
import Resolutions from '@/portal/Resolutions.vue'
import PortalLayout from '@/portal/PortalLayout.vue'
import InfoDetail from '@/portal/InfoDetail.vue'
import AdminMemberships from '@/admin/AdminMemberships.vue'
import AdminSeats from '@/admin/AdminSeats.vue'
import AdminFlows from '@/admin/AdminFlows.vue'
import AdminUsers from '@/admin/AdminUsers.vue'
import AdminFinance from '@/admin/AdminFinance.vue'
import AdminStyleTemplates from '@/admin/AdminStyleTemplates.vue'
import UserPicker from '@/admin/parts/UserPicker.vue'

const { http, adminHttp } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')

const ME = (position = null, units = [], summary = { code: 'GUEST', label: '游客' }) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: !units.length, units, labels: [], summary, committee: position ? { position, term_end: '2027-01-01' } : null }
})
const HEAD_UNIT = { unit_id: 1, specific_part: '1栋1单元3层301号', role: 'HEAD', role_label: '户主', certified_at: '2026-01-01T00:00:00+08:00' }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
const vnodeText = (v) => (typeof v === 'string' ? v : Array.isArray(v) ? v.map(vnodeText).join('\n') : vnodeText(v?.children ?? ''))
beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  messageBox.confirm.mockReset()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

// ------------------------------------------------------------------ 我的房屋（同住人链路）
// 分区同步（ocap_brand_layout MOD-123）：Units.vue 为分区宿主，默认 identity；其余分区经 section 或直接挂载 units/* 组件。
describe('我的房屋 Units.vue（分区宿主 + units/*）', () => {
  const housing = (extra = {}) => ({
    summary: { code: 'HEAD', label: '户主' },
    units: [{ ...HEAD_UNIT, residents: [{ user_id: 9, nickname: '李四', account_no: '1000000009', joined_at: '2026-02-03T09:05:00+08:00' }], pending_application_count: 0 }],
    pending_review_count: 0, ...extra
  })
  const table = (over = {}) => routeTable({
    '/me': ME('MEMBER', [HEAD_UNIT], { code: 'HEAD', label: '户主' }),
    '/me/housing': housing(), '/resident-applications/to-review': [], '/resident-applications/mine': [],
    '/appeals/mine': [], '/units/options': { level: 'building', options: ['1栋'] }, ...over
  })

  it('TC-UNIT-522 / AC-150-01：页面没有任何"专有部分 ID"或内部编号输入框；逐级选择组件存在', async () => {
    http.get.mockImplementation(table())
    const { wrapper } = await mountPage(Units, { props: { section: 'pick' } }) // 原：整页；现：认证产权分区（旧名"选择房屋"）
    const placeholders = wrapper.findAll('input').map((i) => i.attributes('placeholder') || '')
    expect(placeholders.join('|')).not.toMatch(/ID|编号|专有部分/)
    expect(wrapper.text()).not.toContain('专有部分 ID')
    expect(wrapper.findComponent({ name: 'UnitCascader' }).exists()).toBe(true)
  })

  it('TC-UNIT-523 / AC-243-01、AC-236-02（旧 AC-150-01）：选定房屋后点"申请成为同住人"只提交 {unit_id}，并提示"申请已提交，等待产权业主审批"；该按钮已从"认证产权"页迁至"我的同住人申请"页', async () => {
    // 改写：旧在 UnitsPick 上点"申请成为同住人" → 新在 UnitsApplications 上点；UnitsPick 不再有该按钮
    http.get.mockImplementation(table())
    http.post.mockResolvedValue({ id: 5, status: 'PENDING' })
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const pick = await mountPage(UnitsPick)
    expect(buttonOf(pick.wrapper, '申请成为同住人')).toBeUndefined()
    pick.wrapper.unmount()
    document.body.innerHTML = ''
    const { wrapper } = await mountPage(UnitsApplications)
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 42)
    await flush()
    await buttonOf(wrapper, '申请成为同住人').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/resident-applications', { unit_id: 42 })
    expect(success).toHaveBeenCalledWith('申请已提交，等待产权业主审批')
  })

  it('TC-UNIT-524 / AC-167-01、§8 推断 1：认证成功提示为中文身份（户主 / 产权业主），不出现 HEAD / OWNER', async () => {
    http.get.mockImplementation(table())
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountPage(UnitsPick)
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 7)
    // 改写（AC-238-01）：旧占位"请输入姓名" → 新占位"请输入您本人的姓名（须与业主清册登记的姓名一致）"
    await wrapper.find('input[placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）"]').setValue('张三') // ocap_owner_auth_v2：认证须输入姓名
    await flush()
    for (const [role, label] of [['HEAD', '户主'], ['OWNER', '产权业主'], ['RESIDENT', '同住人']]) {
      http.post.mockResolvedValueOnce({ unit_id: 7, role })
      await buttonOf(wrapper, '认证产权').trigger('click')
      await flush()
      expect(success).toHaveBeenCalledWith(`认证成功，身份：${label}`)
    }
    expect(success.mock.calls.flat().join('|')).not.toMatch(/HEAD|OWNER|RESIDENT/)
  })

  it('TC-UNIT-525 / AC-153-04、AC-158-03：移除同住人——取消不发请求；确认后 DELETE /units/1/residents/9', async () => {
    http.get.mockImplementation(table())
    http.delete.mockResolvedValue(null)
    const { wrapper } = await mountPage(Units)
    messageBox.confirm.mockRejectedValueOnce('cancel')
    await buttonOf(wrapper, '移除').trigger('click')
    await flush()
    expect(http.delete).not.toHaveBeenCalled()
    messageBox.confirm.mockResolvedValueOnce('confirm')
    await buttonOf(wrapper, '移除').trigger('click')
    await flush()
    expect(http.delete).toHaveBeenCalledWith('/units/1/residents/9')
    expect(vnodeText(messageBox.confirm.mock.calls[0][0])).toContain('李四')
  })

  it('TC-UNIT-526 / AC-153-04：同住人"退出"——取消不发请求；确认后 POST /units/{id}/leave', async () => {
    const resident = { ...HEAD_UNIT, role: 'RESIDENT', role_label: '同住人', residents: [], pending_application_count: 0 }
    http.get.mockImplementation(table({ '/me/housing': housing({ units: [resident], summary: { code: 'RESIDENT', label: '同住人' } }) }))
    http.post.mockResolvedValue(null)
    const { wrapper } = await mountPage(Units)
    messageBox.confirm.mockRejectedValueOnce('cancel')
    await buttonOf(wrapper, '退出').trigger('click')
    await flush()
    expect(http.post).not.toHaveBeenCalled()
    messageBox.confirm.mockResolvedValueOnce('confirm')
    await buttonOf(wrapper, '退出').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/units/1/leave', {})
  })

  it('TC-UNIT-527 / AC-152-01~03、AC-156-01~04：我的申请/申诉：状态中文、时间"年-月-日 时:分"、驳回原因原文、空态文案', async () => {
    http.get.mockImplementation(table({
      '/resident-applications/mine': [
        { id: 1, unit: { unit_id: 1, specific_part: 'A' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', decided_at: null },
        { id: 2, unit: { unit_id: 1, specific_part: 'A' }, status: 'REJECTED', created_at: '2026-11-12T10:00:00+08:00', decided_at: '2026-11-12T11:15:00+08:00' }
      ],
      '/appeals/mine': [{ id: 3, unit: { unit_id: 2, specific_part: 'B' }, status: 'REJECTED', submitted_at: '2026-11-10T08:00:00+08:00', decided_at: '2026-11-11T09:05:00+08:00', reject_reason: '材料不清，请重传' }]
    }))
    // 原：整页同屏；现：我的同住人申请、我的申诉各为独立分区，两页文本合并后断言（断言不变）
    const apps = await mountPage(UnitsApplications)
    const appeals = await mountPage(UnitsMyAppeals)
    const text = `${apps.wrapper.text()}\n${appeals.wrapper.text()}`
    expect(text).toContain('待审批')
    expect(text).toContain('已拒绝')
    expect(text).toContain('2026-11-13 20:30')
    expect(text).toContain('处理 2026-11-12 11:15')
    expect(text).toContain('已驳回')
    expect(text).toContain('驳回原因：材料不清，请重传')
    expect(text).not.toMatch(/PENDING|REJECTED|T20:30/)
    expect(text).not.toContain('暂无同住人申请')
    document.body.innerHTML = ''
    http.get.mockImplementation(table())
    const empty = `${(await mountPage(UnitsApplications)).wrapper.text()}\n${(await mountPage(UnitsMyAppeals)).wrapper.text()}`
    expect(empty).toContain('暂无同住人申请')
    expect(empty).toContain('暂无申诉')
  })

  it('TC-UNIT-528 / AC-157-03：游客显示"游客"与"暂无已认证房屋"，不显示同住人名单', async () => {
    http.get.mockImplementation(table({ '/me/housing': { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 } }))
    const text = (await mountPage(Units)).wrapper.text()
    expect(text).toContain('汇总身份：游客')
    expect(text).toContain('暂无已认证房屋')
  })

  it('TC-UNIT-529 / AC-151-01：待审批列表显示申请人昵称、房屋名与提交时间，不含手机号明文', async () => {
    http.get.mockImplementation(table({
      '/resident-applications/to-review': [{ id: 8, unit: { unit_id: 1, specific_part: 'A房' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', decided_at: null,
        applicant: { id: 3, account_no: '1000000003', nickname: '小王', phone: '139****0001' } }]
    }))
    const text = (await mountPage(UnitsReview)).wrapper.text() // 原：整页；现：待我审批分区
    expect(text).toContain('小王 → A房')
    expect(text).toContain('2026-11-13 20:30')
    expect(text).not.toMatch(/1\d{10}/)
  })
})

// ------------------------------------------------------------------ 个人中心
// 拆分同步（MOD-122）：个人中心各区块为独立页 me/*，用例原意不变，仅改挂载对象。
describe('个人中心 me/* 各页（原 Me.vue）', () => {
  const profile = { account_no: '1000000001', phone: '138****0000', nickname: '张三', gender: 0, birthday: null, email: null, avatar_url: '' }
  const mountMe = async (over = {}, component = UnitsIdentity) => {
    http.get.mockImplementation(routeTable({
      '/me': ME(null, [HEAD_UNIT], { code: 'HEAD', label: '户主' }), '/me/profile': profile,
      '/resident-applications/to-review': [], '/resident-applications/mine': [], '/appeals/mine': [],
      '/me/housing': { summary: { code: 'HEAD', label: '户主' }, units: [{ ...HEAD_UNIT, residents: [], pending_application_count: 0, unit_type_label: '住宅', area_display: '89.50 ㎡' }], pending_review_count: 0 }, ...over
    }))
    const mounted = await mountPage(component)
    useAuthStore(mounted.pinia).me = ME(null, [HEAD_UNIT], { code: 'HEAD', label: '户主' })
    await flush()
    return mounted
  }

  it('TC-UNIT-530 / AC-232-01、AC-157-01、AC-157-05：身份卡（现为"我的身份与房屋"页）列出汇总身份与每套房屋（名称、类型、面积、关系），全部中文且没有编辑身份的输入控件', async () => {
    // 改写：旧 MeIdentity 身份卡"零按钮" → 新 UnitsIdentity：仍无 input/select 等编辑身份控件；按钮仅"认证产权"（AC-237-01），不含身份编辑
    const { wrapper } = await mountMe()
    const card = wrapper.findAll('.card').find((c) => c.text().includes('身份'))
    expect(card.text()).toContain('汇总身份：户主')
    expect(card.text()).toContain('1栋1单元3层301号')
    expect(card.text()).toContain('住宅')
    expect(card.text()).toContain('89.50 ㎡')
    expect(card.text()).toContain('户主')
    expect(card.text()).not.toMatch(/HEAD|OWNER|RESIDENT/)
    expect(card.findAll('input,select')).toHaveLength(0)
    expect(card.findAll('button').map((b) => b.text())).toEqual(['认证产权'])
  })

  it('TC-UNIT-531 / AC-165-03：更换头像处提示"jpg/png，不超过 5 MB"，选择器仅允许 jpg/png；超大或错误格式在上传前被拒', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper } = await mountMe({}, MeProfile)
    expect(wrapper.text()).toContain('jpg/png，不超过 5 MB')
    expect(wrapper.find('input[type="file"]').attributes('accept')).toBe('.jpg,.jpeg,.png')
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    const before = upload.props('beforeUpload')
    expect(before({ name: 'a.gif', type: 'image/gif', size: 10 })).toBe(false)
    expect(before({ name: 'a.png', type: 'image/png', size: 5 * 1024 * 1024 + 1 })).toBe(false)
    expect(before({ name: 'a.png', type: 'image/png', size: 5 * 1024 * 1024 })).toBe(true)
    expect(error).toHaveBeenCalledWith('头像仅支持 jpg/png 格式')
    expect(error).toHaveBeenCalledWith('头像不能超过 5 MB')
  })

  it('TC-UNIT-532 / AC-165-01：保存生日提交 YYYY-MM-DD；留空提交 null（选填）', async () => {
    const { wrapper } = await mountMe({ '/me/profile': { ...profile, birthday: '1990-05-06' } }, MeProfile)
    http.patch.mockResolvedValue({ ...profile, birthday: '1990-05-06' })
    await buttonOf(wrapper, '保存').trigger('click')
    await flush()
    expect(http.patch).toHaveBeenLastCalledWith('/me/profile', { nickname: '张三', gender: 0, birthday: '1990-05-06' })
  })

  it('TC-UNIT-533 / AC-165-02：头像通过鉴权下载（/attachments/<id>/download，blob）并显示为图片', async () => {
    const created = vi.fn(() => 'blob:avatar-1')
    global.URL.createObjectURL = created
    global.URL.revokeObjectURL = vi.fn()
    http.get.mockImplementation(routeTable({
      '/me': ME(null), '/me/profile': { ...profile, avatar_url: '/api/v1/attachments/abc-123/download' },
      '/me/housing': { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 },
      '/attachments/abc-123/download': new Blob(['x'], { type: 'image/png' })
    }))
    const { wrapper } = await mountPage(MeProfile)
    await flush()
    expect(http.get.mock.calls.some((c) => c[0] === '/attachments/abc-123/download' && c[1]?.responseType === 'blob')).toBe(true)
    expect(wrapper.find('img[src="blob:avatar-1"]').exists()).toBe(true)
  })

  it('TC-UNIT-534 / AC-158-04：注销账号——取消确认不发验证码校验请求；确认后才调用 /me/cancel', async () => {
    const { wrapper } = await mountMe({}, MeCancel)
    http.post.mockResolvedValue(null)
    const inputs = wrapper.findAll('input')
    const phoneInput = inputs.find((i) => i.attributes('placeholder') === '已绑定的手机号')
    await phoneInput.setValue('13800000000')
    messageBox.confirm.mockRejectedValueOnce('cancel')
    await buttonOf(wrapper, '确认注销').trigger('click')
    await flush()
    expect(http.post).not.toHaveBeenCalledWith('/me/cancel', expect.anything())
    messageBox.confirm.mockResolvedValueOnce('confirm')
    await buttonOf(wrapper, '确认注销').trigger('click')
    await flush()
    expect(http.post.mock.calls.some((c) => c[0] === '/me/cancel')).toBe(true)
    expect(vnodeText(messageBox.confirm.mock.calls.at(-1)[0])).toMatch(/接任[\s\S]*席位失效[\s\S]*关闭[\s\S]*不可恢复/)
  })
})

// ------------------------------------------------------------------ 登录页 / 导航 / 详情
describe('登录页、导航与内容详情', () => {
  it('TC-UNIT-535 / AC-163-01：密码登录输入框提示为"账号或手机号"，不含"邮箱"', async () => {
    const { wrapper } = await mountPage(Login)
    const inputs = wrapper.findAll('input')
    const idInput = inputs.find((i) => i.attributes('placeholder') === '账号或手机号')
    expect(idInput).toBeTruthy()
    const pane = wrapper.findAll('.el-tab-pane').find((p) => p.text() === '' && p.find('input[placeholder="账号或手机号"]').exists())
    const passwordPaneText = (pane || wrapper.find('input[placeholder="账号或手机号"]').element.closest('.el-tab-pane')).outerHTML
    expect(passwordPaneText).not.toContain('邮箱')
  })

  it('TC-UNIT-577 / AC-154-04、AC-166-01：左侧导航（原：顶部导航）——非成员无"报销/备用金""收入表""待办"；委员三者可见；"个人中心"移入右上角菜单，不在导航内', async () => {
    const nav = async (position) => {
      document.body.innerHTML = ''
      http.get.mockImplementation(routeTable({ '/me': ME(position) }))
      const { wrapper } = await mountPage(PortalLayout)
      await flush()
      return wrapper.find('nav.side-nav').text()
    }
    const plain = await nav(null)
    for (const t of ['我的房屋', '决议', '投票/调查', '财务报表']) expect(plain).toContain(t)
    expect(plain).not.toContain('个人中心')
    for (const t of ['报销/备用金', '收入表', '待办']) expect(plain).not.toContain(t)
    const member = await nav('MEMBER')
    for (const t of ['报销/备用金', '收入表', '待办']) expect(member).toContain(t)
  })

  it('TC-UNIT-536 / AC-169-02：详情失败时提示"内容不存在或已下线"，"返回列表"链接指向信息公开列表', async () => {
    http.get.mockRejectedValue(Object.assign(new Error('x'), { code: 'NOT_FOUND', status: 404 }))
    const { wrapper } = await mountPage(InfoDetail)
    await flush()
    expect(wrapper.text()).toContain('内容不存在或已下线')
    const link = wrapper.findAll('a').find((a) => a.text().includes('返回列表'))
    expect(link.attributes('href')).toMatch(/\/info$/)
  })
})

// ------------------------------------------------------------------ 投票 / 决议
describe('投票与决议列表', () => {
  it('TC-UNIT-537 / AC-167-02：投票状态为"进行中/已结束"，截止时间为"2026-11-13 20:30"，无 T 与时区后缀', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME('CHAIR'), '/system/limits': { poll_max_questions: 50, poll_options_min: 2, poll_options_max: 10, vote_min_window_minutes: 60 },
      '/polls': { count: 2, results: [
        { id: 1, title: '甲', kind: 'SURVEY', status: 'OPEN', deadline: '2026-11-13T20:30:00+08:00' },
        { id: 2, title: '乙', kind: 'REP_VOTE', status: 'CLOSED', deadline: '2026-10-01T08:05:00+08:00' }] }
    }))
    const { wrapper } = await mountPage(Polls)
    const text = wrapper.text()
    expect(text).toContain('调查 · 进行中 · 截止 2026-11-13 20:30')
    expect(text).toContain('业主代表投票 · 已结束 · 截止 2026-10-01 08:05')
    expect(text).not.toMatch(/OPEN|CLOSED|\+08:00|13T20/)
    expect(text).toContain('共 2 条')
  })

  it('TC-UNIT-538 / AC-172-01：主任/副主任打开发起页，预先显示"最多 50 道题；单选/多选题选项 2 ~ 10 个；表决窗口不少于 60 分钟"', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME('CHAIR'), '/system/limits': { poll_max_questions: 50, poll_options_min: 2, poll_options_max: 10, vote_min_window_minutes: 60 },
      '/polls': { count: 0, results: [] }
    }))
    const { wrapper } = await mountPage(Polls)
    await buttonOf(wrapper, '发起').trigger('click')
    await flush()
    expect(document.body.textContent).toContain('最多 50 道题；单选/多选题选项 2 ~ 10 个；表决窗口不少于 60 分钟')
  })

  it('TC-UNIT-539 / AC-161-01、AC-161-04：决议列表显示总条数；总数不超过 20 时无翻页控件，超过时有', async () => {
    const list = (count) => ({ count, results: Array.from({ length: Math.min(count, 20) }, (_, i) => ({ id: i + 1, title: `决议${i}`, status: 'APPROVED' })) })
    http.get.mockImplementation(routeTable({ '/me': ME(null), '/resolutions': list(25), '/system/limits': { vote_min_window_minutes: 60 } }))
    let { wrapper } = await mountPage(Resolutions)
    expect(wrapper.text()).toContain('共 25 条')
    expect(wrapper.find('.el-pagination').exists()).toBe(true)
    document.body.innerHTML = ''
    http.get.mockImplementation(routeTable({ '/me': ME(null), '/resolutions': list(7), '/system/limits': { vote_min_window_minutes: 60 } }))
    ;({ wrapper } = await mountPage(Resolutions))
    expect(wrapper.text()).toContain('共 7 条')
    expect(wrapper.find('.el-pagination').exists()).toBe(false)
  })
})

// ------------------------------------------------------------------ 管理端
describe('管理端页面', () => {
  const mountAdmin = async (component, table, props = {}) => {
    adminHttp.get.mockImplementation(routeTable(table))
    const { wrapper } = await mountPage(component, { props })
    await flush()
    return wrapper
  }

  it('TC-UNIT-540 / AC-158-01：撤销认证——取消不发请求且没有新增调用；确认后才 POST /admin/memberships/revoke，确认框写明后果', async () => {
    const wrapper = await mountAdmin(AdminMemberships, {
      '/admin/memberships': { count: 1, results: [{ id: 1, user: { id: 7, nickname: '甲', account_no: '1' }, unit_id: 3, specific_part: 'A房', role: 'OWNER', certified_at: '2026-01-01' }] }
    })
    adminHttp.post.mockResolvedValue({})
    messageBox.confirm.mockRejectedValueOnce('cancel')
    await buttonOf(wrapper, '撤销认证').trigger('click')
    await flush()
    expect(adminHttp.post).not.toHaveBeenCalled()
    messageBox.confirm.mockResolvedValueOnce('confirm')
    await buttonOf(wrapper, '撤销认证').trigger('click')
    await flush()
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/memberships/revoke', { user_id: 7, unit_id: 3 })
    expect(vnodeText(messageBox.confirm.mock.calls[0][0])).toMatch(/失去该房屋的身份[\s\S]*户主接任/)
  })

  it('TC-UNIT-541 / AC-159-02、AC-256-01/02、REQ-FUNC-292：赋予席位对话框没有"用户 ID"输入框；新：逐级选专有部分(UnitCascader，管理端选项接口)→选清册业主(姓名+完整手机号)→提交 registry_owner_id 且不含 user_id', async () => {
    const wrapper = await mountAdmin(AdminSeats, {
      '/admin/committee/seats': { count: 0, results: [] }, '/admin/committee/config': { cap_member: 5 },
      '/admin/registry/unit-options': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }] },
      '/admin/committee/owner-candidates': { unit_id: 5, specific_part: '1栋1单元9层902号', owners: [
        { owner_id: 11, name: '业主甲', phone: '13800000001', seated: false, registered: false },
        { owner_id: 12, name: '业主乙', phone: '13900000002', seated: true, registered: true }] }
    })
    await buttonOf(wrapper, '赋予席位').trigger('click')
    await flush()
    const dialog = document.body
    const placeholders = [...dialog.querySelectorAll('input')].map((i) => i.getAttribute('placeholder') || '')
    expect(placeholders.join('|')).not.toMatch(/用户 ?ID|用户编号|搜索用户/)
    const cascader = wrapper.findComponent({ name: 'UnitCascader' })
    expect(cascader.exists()).toBe(true)
    cascader.vm.$emit('update:modelValue', 5)
    await flush()
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/committee/owner-candidates', { params: { unit_id: 5 } })
    expect(dialog.textContent).toContain('业主甲')
    expect(dialog.textContent).toContain('13800000001')
    expect(dialog.textContent).toContain('已有有效席位')
    const radios = [...dialog.querySelectorAll('.seat-holder-owners input[type=radio]')]
    expect(radios).toHaveLength(2)
    expect(radios[1].disabled).toBe(true)
    radios[0].click()
    await flush()
    adminHttp.post.mockResolvedValue({})
    const save = [...dialog.querySelectorAll('button')].find((b) => b.textContent.trim() === '保存')
    save.click()
    await flush()
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/committee/seats', { registry_owner_id: 11, position: 'MEMBER' })
    expect(JSON.stringify(adminHttp.post.mock.calls)).not.toContain('user_id')
  })

  it('TC-UNIT-542 / AC-158-03：撤销席位、删除审批流程——取消不发请求', async () => {
    let wrapper = await mountAdmin(AdminSeats, {
      '/admin/committee/seats': { count: 1, results: [{ id: 4, user: { id: 7, nickname: '甲' }, position: 'MEMBER', status: 'ACTIVE', term_start: '2026-01-01', term_end: '2027-01-01' }] },
      '/admin/committee/config': {}
    })
    messageBox.confirm.mockRejectedValue('cancel')
    await buttonOf(wrapper, '撤销').trigger('click')
    await flush()
    expect(adminHttp.delete).not.toHaveBeenCalled()
    document.body.innerHTML = ''
    wrapper = await mountAdmin(AdminFlows, {
      '/admin/approval/flows': { count: 1, results: [{ id: 9, name: '流程甲', scope: 'EXPENSE', mode: 'DESIGNATED', is_active: true }] }
    })
    await buttonOf(wrapper, '删除').trigger('click')
    await flush()
    expect(adminHttp.delete).not.toHaveBeenCalled()
    messageBox.confirm.mockReset()
    messageBox.confirm.mockResolvedValue('confirm')
    adminHttp.delete.mockResolvedValue(null)
    await buttonOf(wrapper, '删除').trigger('click')
    await flush()
    expect(adminHttp.delete).toHaveBeenCalledWith('/admin/approval/flows/9')
  })

  it('修复问题二：新建审批流程选"半数人员同意"时隐藏审批人设置，保存不提交 approver_ids', async () => {
    const wrapper = await mountAdmin(AdminFlows, { '/admin/approval/flows': { count: 0, results: [] } })
    await buttonOf(wrapper, '新建流程').trigger('click')
    await flush()
    // 默认指定负责人：可见 UserPicker，可添加审批人
    expect(wrapper.findComponent(UserPicker).exists()).toBe(true)
    wrapper.findComponent(UserPicker).vm.$emit('change', { id: 7, nickname: '委员甲', identity_label: '委员' })
    await flush()
    expect(document.body.textContent).toContain('委员甲')
    // 切到半数同意：清空并隐藏审批人设置，显示说明
    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    const modeSelect = selects[selects.length - 1]
    modeSelect.vm.$emit('update:modelValue', 'HALF_MAJORITY')
    modeSelect.vm.$emit('change', 'HALF_MAJORITY')
    await flush()
    expect(wrapper.findComponent(UserPicker).exists()).toBe(false)
    expect(document.body.textContent).toContain('无需设置审批人')
    // 保存：approver_ids 为空
    adminHttp.post.mockResolvedValue({})
    const save = [...document.body.querySelectorAll('button')].find((b) => b.textContent.trim() === '保存')
    save.click()
    await flush()
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/approval/flows',
      expect.objectContaining({ mode: 'HALF_MAJORITY', approver_ids: [] }))
  })

  it('TC-UNIT-543 / AC-167-03：席位页与账号页的状态、启用列显示中文，布尔显示"是/否"，页面文字无 ACTIVE / true / false', async () => {
    let wrapper = await mountAdmin(AdminSeats, {
      '/admin/committee/seats': { count: 2, results: [
        { id: 1, user: { id: 7, nickname: '甲' }, position: 'MEMBER', status: 'ACTIVE', term_start: '2026-01-01', term_end: '2027-01-01' },
        { id: 2, user: { id: 8, nickname: '乙' }, position: 'CHAIR', status: 'EXPIRED', term_start: '2025-01-01', term_end: '2026-01-01' }] },
      '/admin/committee/config': {}
    })
    expect(wrapper.text()).toContain('在任')
    expect(wrapper.text()).not.toMatch(/ACTIVE|EXPIRED|\btrue\b|\bfalse\b/)
    document.body.innerHTML = ''
    // 分区同步：管理员账号（启用 = 是/否）与注册用户（状态 = 启用/停用、共 N 条）分属 /admin/users 与 /admin/users/registered，分别挂载后合并断言
    const adminRows = [{ id: 1, username: 'root', is_active: true }, { id: 2, username: 'x', is_active: false }]
    const userRows = { count: 2, results: [
      { id: 1, account_no: '1', phone: '138****0001', nickname: '甲', status: 'ACTIVE', identity_label: '户主', certified_units: 1, real_names: [], last_login_at: null },
      { id: 2, account_no: '2', phone: null, nickname: '乙', status: 'DISABLED', identity_label: '游客', certified_units: 0, real_names: [], last_login_at: null }] }
    wrapper = await mountAdmin(AdminUsers, { '/admin/admins': adminRows, '/admin/users': userRows })
    const adminText = wrapper.text()
    document.body.innerHTML = ''
    wrapper = await mountAdmin(AdminUsers, { '/admin/admins': adminRows, '/admin/users': userRows }, { section: 'registered' })
    const regText = wrapper.text()
    const text = `${adminText}\n${regText}`
    expect(text).toContain('启用')
    expect(text).toContain('停用')
    expect(adminText).toContain('是')
    expect(adminText).toContain('否')
    expect(text).not.toMatch(/ACTIVE|DISABLED|\btrue\b|\bfalse\b/)
    expect(regText).toContain('共 2 条')
  })

  it('TC-UNIT-544 / AC-160-02：账号页带关键词翻到第 2 页，请求仍携带同一关键词与 page=2', async () => {
    const wrapper = await mountAdmin(AdminUsers, {
      '/admin/admins': [], '/admin/users': { count: 45, results: [{ id: 1, account_no: '1', phone: null, nickname: 'e2e_x', status: 'ACTIVE', identity_label: '游客', certified_units: 0, real_names: [], last_login_at: null }] }
    }, { section: 'registered' }) // 分区同步：注册用户列表在 registered 分区
    const input = wrapper.find('input[placeholder^="昵称"]')
    await input.setValue('e2e_')
    await input.trigger('change')
    await flush()
    adminHttp.get.mockClear()
    wrapper.findComponent({ name: 'ElPagination' }).vm.$emit('current-change', 2)
    await flush()
    const call = adminHttp.get.mock.calls.find((c) => c[0] === '/admin/users')
    expect(call[1].params).toMatchObject({ q: 'e2e_', page: 2 })
  })

  it('TC-UNIT-545 / AC-162-03、AC-162-05：版式模板页——名称为空保存被拦（提示"模板名称不能为空"、不发请求）；内置模板无编辑/删除入口；被引用数显示', async () => {
    const warning = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const wrapper = await mountAdmin(AdminStyleTemplates, {
      '/admin/content/style-templates': [
        { key: 'builtin:classic', name: '经典', builtin: true, tokens: {} },
        { key: 'custom:3', id: 3, name: 'e2e_模板A', builtin: false, tokens: { font_size: 16 }, usage_count: 2 }]
    })
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('内置')
    expect(rows[0].findAll('button')).toHaveLength(0)
    expect(rows[1].text()).toContain('自定义')
    expect(rows[1].text()).toContain('2')
    expect(rows[1].findAll('button').map((b) => b.text())).toEqual(['编辑', '删除'])
    await buttonOf(wrapper, '新建模板').trigger('click')
    await flush()
    const save = [...document.body.querySelectorAll('.el-dialog button')].find((b) => b.textContent.trim() === '保存')
    save.click()
    await flush()
    expect(warning).toHaveBeenCalledWith('模板名称不能为空')
    expect(adminHttp.post).not.toHaveBeenCalled()
  })

  it('TC-UNIT-546 / AC-162-04：删除被引用的模板——确认后后端 STYLE_IN_USE，提示"被 K 条内容引用"；取消不发请求', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const wrapper = await mountAdmin(AdminStyleTemplates, {
      '/admin/content/style-templates': [{ key: 'custom:3', id: 3, name: 'e2e_模板A', builtin: false, tokens: {}, usage_count: 2 }]
    })
    messageBox.confirm.mockRejectedValueOnce('cancel')
    await wrapper.find('tbody button.el-button--danger').trigger('click')
    await flush()
    expect(adminHttp.delete).not.toHaveBeenCalled()
    messageBox.confirm.mockResolvedValueOnce('confirm')
    adminHttp.delete.mockRejectedValueOnce(Object.assign(new Error('x'), { code: 'STYLE_IN_USE', details: { count: 2 } }))
    await wrapper.find('tbody button.el-button--danger').trigger('click')
    await flush()
    expect(adminHttp.delete).toHaveBeenCalledWith('/admin/content/style-templates/3')
    expect(error).toHaveBeenCalledWith('被 2 条内容引用，不能删除')
  })

  it('TC-UNIT-547 / AC-170-01、AC-170-04：金额上限配置卡显示当前值；非法输入显示后端文案并回读原值；合法值保存后按两位小数显示', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const wrapper = await mountAdmin(AdminFinance, {
      '/admin/claims': { count: 0, results: [] }, '/admin/system-config': { 'audit.retention_months': 24, 'claim.amount_max': '1000000.00' }
    }, { section: 'limit' }) // 分区同步：金额上限卡在 /admin/finance/limit 分区
    const input = wrapper.find('input[placeholder*="上限"]').exists() ? wrapper.find('input[placeholder*="上限"]') : wrapper.findAll('input').find((i) => i.element.value.includes('1000000'))
    expect(input.element.value).toContain('1000000')
    adminHttp.put.mockRejectedValueOnce(Object.assign(new Error('上限须为正数且最多两位小数'), { code: 'INVALID_VALUE' }))
    await input.setValue('abc')
    await buttonOf(wrapper, '保存').trigger('click')
    await flush()
    expect(adminHttp.put).toHaveBeenCalledWith('/admin/system-config/claim.amount_max', { value: 'abc' })
    expect(error).toHaveBeenCalled()
    expect(input.element.value).toContain('1000000') // 重新读取后恢复原值
    adminHttp.put.mockResolvedValueOnce({ key: 'claim.amount_max', value: '500000.00' })
    await input.setValue('500000')
    await buttonOf(wrapper, '保存').trigger('click')
    await flush()
    expect(input.element.value).toContain('500000.00')
  })
})

describe('用户选择器 UserPicker', () => {
  const type = async (wrapper, text) => {
    const input = wrapper.find('input')
    await input.setValue(text)
    await new Promise((r) => setTimeout(r, 400))
    await flushPromises()
  }

  it('TC-UNIT-578 / AC-159-04：无匹配时显示"无匹配用户"；匹配超过一页时出现翻页控件并按页请求（page_size=10）', async () => {
    adminHttp.get.mockImplementation(async (url, arg) => {
      if (arg.params.q === 'none') return { count: 0, results: [] }
      return { count: 25, results: Array.from({ length: 10 }, (_, i) => ({ id: i + 1, nickname: `用户${i}`, account_no: `100000000${i}`, phone: '138****0001', identity_label: '游客', real_names: [] })) }
    })
    const { wrapper } = await mountPage(UserPicker)
    await type(wrapper, 'none')
    expect(wrapper.text()).toContain('无匹配用户')
    expect(wrapper.find('.el-pagination').exists()).toBe(false)
    await type(wrapper, '用户')
    expect(wrapper.findAll('.user-picker-item')).toHaveLength(10)
    const pager = wrapper.findComponent({ name: 'ElPagination' })
    expect(pager.exists()).toBe(true)
    adminHttp.get.mockClear()
    pager.vm.$emit('current-change', 2)
    await flush()
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/users', { params: { q: '用户', page: 2, page_size: 10 } })
  })
})

// ------------------------------------------------------------------ 源码级守护
describe('确认弹窗覆盖与界面文案守护（静态）', () => {
  const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)])
  const vueFiles = walk(path.join(ROOT, 'frontend/src')).filter((f) => f.endsWith('.vue'))

  it('TC-UNIT-548 / AC-158-01、AC-158-03、AC-158-04：11 个确认键都在页面中被使用，且每处调用都是"确认失败即 return"的写法', () => {
    const keys = ['revokeMembership', 'revokeSeat', 'deleteUnit', 'deleteFlow', 'voidIncome', 'withdrawResolution',
      'withdrawClaim', 'withdrawIncome', 'removeResident', 'leaveUnit', 'cancelAccount']
    // 同步：新拆分页的文件头 HTML 注释会提到 confirmDanger('…')（MeCancel.vue:1），统计"调用"前先剥离注释，守护对象仍是真实调用
    const stripComments = (text) => text.replace(/<!--[\s\S]*?-->/g, '').replace(/^\s*\/\/.*$/gm, '')
    const all = vueFiles.map((f) => stripComments(fs.readFileSync(f, 'utf8'))).join('\n')
    for (const key of keys) {
      const uses = [...all.matchAll(new RegExp(`confirmDanger\\('${key}'`, 'g'))]
      expect(uses.length, key).toBeGreaterThan(0)
    }
    const calls = [...all.matchAll(/confirmDanger\('/g)].length
    const guarded = [...all.matchAll(/if \(!\(await confirmDanger\('/g)].length
    expect(calls).toBeGreaterThanOrEqual(11)
    expect(guarded).toBe(calls)
  })

  it('TC-UNIT-549 / AC-150-01、AC-159-02：页面源码中不再有"专有部分 ID"或"用户 ID"的手输控件', () => {
    // 扫描范围加入拆分后的新文件（Units.vue 的内容已迁至 portal/units/*）
    const rels = ['portal/Units.vue', 'admin/AdminSeats.vue', 'admin/AdminFlows.vue',
      ...fs.readdirSync(path.join(ROOT, 'frontend/src/portal/units')).map((f) => `portal/units/${f}`)]
    for (const rel of rels) {
      const src = fs.readFileSync(path.join(ROOT, 'frontend/src', rel), 'utf8')
      expect(src, rel).not.toMatch(/placeholder="[^"]*(专有部分 ?ID|用户 ?ID|审批人用户)/)
      expect(src, rel).not.toMatch(/split\(/)
    }
  })

  it('TC-UNIT-550 / AC-157-05、AC-167-01：用户端页面不再直接显示 role 原始代码（模板中的 {{ x.role }} 均经 label）', () => {
    for (const f of vueFiles.filter((f) => /portal/.test(f))) {
      const src = fs.readFileSync(f, 'utf8')
      const template = src.split('<script')[0]
      expect(template, f).not.toMatch(/\{\{\s*[\w.?]*\.role\s*\}\}/)
    }
  })
})
