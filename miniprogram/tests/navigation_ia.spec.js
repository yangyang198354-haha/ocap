// ocap_navigation_ia GROUP_D（MOD-179/180/181/182）：小程序“我的房屋”三 Tab、“我的”页分组、邮箱验证与账号注销。
// 层级：integration（真实页面/组件 + 真实 api.js/http.js/store，仅 mock uni.request）；E2E 级多步旅程以替代口径计数。
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountPage, respondWith, requests, byText } from './helpers.js'
import Units from '../pages/units/index.vue'
import Me from '../pages/me/index.vue'
import Email from '../pages/email/index.vue'
import Cancel from '../pages/cancel/index.vue'
import { MP_HOUSING_TABS, MP_USER_GROUPS } from '../utils/menu.js'

const OWNED = {
  unit_id: 7, specific_part: 'A房', role: 'HEAD', role_label: '产权业主',
  unit_type_label: '住宅', area_display: '89.50 ㎡', residents: []
}
const HOUSING = (units, pending = 0) => ({
  summary: units.some((u) => u.role !== 'RESIDENT')
    ? { code: 'OWNER', label: '产权业主' }
    : units.length ? { code: 'RESIDENT', label: '同住人' } : { code: 'GUEST', label: '游客' },
  units, pending_review_count: pending
})
const ME = (labels = ['游客'], phone = '138****0000', email = 'old@example.com') => ({
  profile: { id: 1, nickname: '张三', phone, email },
  identities: { is_guest: labels.includes('游客'), units: [], labels, summary: { code: 'GUEST', label: '游客' }, committee: null }
})
const unitsTable = (housing) => ({
  'GET /me/housing': housing,
  'GET /resident-applications/to-review': {
    results: [{ id: 8, unit: { unit_id: 7, specific_part: 'A房' }, status: 'PENDING', created_at: '2026-11-13T20:30:00+08:00', applicant: { nickname: '王五', account_no: '1000000005' } }]
  },
  'GET /resident-applications/mine': { results: [] },
  'GET /appeals/mine': { results: [] },
  'GET /units/options': { level: 'building', options: [] },
  'GET /me': ME()
})

const tabEls = (wrapper) => wrapper.findAll('.housing-tab')
const paneDisplay = (wrapper, comp) => wrapper.findComponent(comp).element.style.display

describe('小程序“我的房屋”三 Tab（US-304）', () => {
  it('TC-E2E-1101 / AC-304-01：顶部依次三个 Tab（我的身份与房屋/我的认证与申述/我的同住人申请），默认身份面板可见', async () => {
    respondWith(unitsTable(HOUSING([OWNED], 1)))
    const { wrapper } = await mountPage(Units)
    expect(tabEls(wrapper).map((t) => t.text())).toEqual(['我的身份与房屋', '我的认证与申述', '我的同住人申请'])
    expect(wrapper.find('.housing-tab.is-active').text()).toBe('我的身份与房屋')
    expect(wrapper.text()).toContain('我的身份与房屋')
  })

  it('TC-E2E-1102 / AC-304-02：切到“我的认证与申述”——含认证申诉/我的申诉子 Tab；切换子 Tab 后 mine 高亮', async () => {
    respondWith(unitsTable(HOUSING([OWNED], 1)))
    const { wrapper } = await mountPage(Units)
    await byText(wrapper, '.housing-tab', '我的认证与申述').trigger('click')
    await flushPromises()
    expect(wrapper.find('.housing-tab.is-active').text()).toBe('我的认证与申述')
    const subTabs = wrapper.findAll('.sub-tab').filter((t) => ['认证申诉', '我的申诉'].includes(t.text()))
    expect(subTabs.map((t) => t.text())).toEqual(['认证申诉', '我的申诉'])
    await subTabs[1].trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.sub-tab.is-active').map((t) => t.text())).toContain('我的申诉')
  })

  it('TC-E2E-1103 / AC-304-03：产权业主身份面板含“待我审批”子 Tab，点击后显示审批行；非业主无该子 Tab 与卡片', async () => {
    respondWith(unitsTable(HOUSING([OWNED], 1)))
    const owner = await mountPage(Units)
    const reviewTab = byText(owner.wrapper, '.sub-tab', '待我审批')
    expect(reviewTab).toBeTruthy()
    await reviewTab.trigger('click')
    await flushPromises()
    expect(owner.wrapper.find('#review').text()).toContain('王五')
    owner.wrapper.unmount()
    document.body.innerHTML = ''

    respondWith(unitsTable(HOUSING([])))
    const guest = await mountPage(Units)
    expect(guest.wrapper.findAll('.sub-tab').some((t) => t.text().includes('待我审批'))).toBe(false)
    expect(guest.wrapper.find('#review').exists()).toBe(false)
  })

  it('TC-E2E-1104 / AC-304-04：切到“我的同住人申请”——显示发起按钮与申请记录区', async () => {
    respondWith(unitsTable(HOUSING([OWNED], 1)))
    const { wrapper } = await mountPage(Units)
    await byText(wrapper, '.housing-tab', '我的同住人申请').trigger('click')
    await flushPromises()
    expect(wrapper.find('.housing-tab.is-active').text()).toBe('我的同住人申请')
    expect(byText(wrapper, 'button', '申请成为同住人')).toBeTruthy()
    expect(wrapper.text()).toContain('暂无同住人申请')
  })
})

describe('小程序“我的”页分组（US-305）', () => {
  const meTable = {
    'GET /me': ME(),
    'GET /me/housing': HOUSING([]),
    'GET /me/profile': { real_name: '', email: 'old@example.com' },
    'GET /reports': { results: [], total: 0 },
    'PATCH /me/theme': { theme: 'bento' },
    'PUT /me/theme': { theme: 'bento' }
  }

  it('TC-UNIT-1101 / AC-305-01、AC-305-02、AC-309-01：分组常量为“个人设置 4 项 + 系统设置 1 项”，无“设置密码”，三 Tab 文案与 Web 一致', () => {
    expect(MP_USER_GROUPS.map((g) => g.label)).toEqual(['个人设置', '系统设置'])
    expect(MP_USER_GROUPS[0].items.map((i) => i.label)).toEqual(['个人资料', '绑定手机', '邮箱验证', '账号注销'])
    expect(MP_USER_GROUPS[1].items.map((i) => i.label)).toEqual(['界面风格'])
    const labels = MP_USER_GROUPS.flatMap((g) => g.items.map((i) => i.label))
    expect(labels).not.toContain('手机号')
    expect(labels).not.toContain('设置密码')
    expect(MP_HOUSING_TABS.map((t) => t.label)).toEqual(['我的身份与房屋', '我的认证与申述', '我的同住人申请'])
  })

  it('TC-E2E-1105 / AC-305-01、AC-305-02、AC-305-03：分组标题顺序、入口文案固定“绑定手机”、跳转目标正确', async () => {
    respondWith(meTable)
    const { wrapper } = await mountPage(Me)
    const titles = wrapper.findAll('.title').map((t) => t.text())
    expect(titles.indexOf('个人设置')).toBeGreaterThan(-1)
    expect(titles.indexOf('系统设置')).toBeGreaterThan(titles.indexOf('个人设置'))
    const settingLabels = wrapper.findAll('.settings-item').map((i) => i.find('text').text())
    expect(settingLabels).toEqual(['个人资料', '绑定手机', '邮箱验证', '账号注销', '界面风格'])
    for (const [label, url] of [
      ['个人资料', '/pages/profile-setup/index'],
      ['绑定手机', '/pages/phone/index'],
      ['邮箱验证', '/pages/email/index'],
      ['账号注销', '/pages/cancel/index']
    ]) {
      uni.navigateTo.mockClear()
      await byText(wrapper, '.settings-item', label).trigger('click')
      await flushPromises()
      expect(uni.navigateTo.mock.calls[0][0]).toMatchObject({ url })
    }
  })

  it('TC-E2E-1106 / AC-305-04：界面风格选项在系统设置下渲染，点选调用主题保存', async () => {
    respondWith(meTable)
    const { wrapper } = await mountPage(Me)
    expect(wrapper.findAll('.theme-option')).toHaveLength(3)
    const other = wrapper.findAll('.theme-option').find((o) => !o.classes('is-selected'))
    await other.trigger('click')
    await flushPromises()
    expect(requests().some((r) => r.method === 'PUT' && r.path === '/me/theme')).toBe(true)
  })
})

describe('小程序邮箱验证与账号注销（US-305、US-310）', () => {
  it('TC-E2E-1107 / AC-305-01、AC-310-01：邮箱页保存邮箱、发送 EMAIL_VERIFY、提交 /me/email/verify', async () => {
    respondWith({
      'GET /me': ME(['游客'], '138****0000', 'old@example.com'),
      'PATCH /me/profile': {},
      'POST /me/codes': {},
      'POST /me/email/verify': {}
    })
    const { wrapper } = await mountPage(Email)
    expect(wrapper.text()).toContain('old@example.com')
    const emailInput = wrapper.find('input[placeholder="邮箱"]')
    await emailInput.setValue('new@example.com')
    await byText(wrapper, 'button', '保存邮箱').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'PATCH' && r.path === '/me/profile').data).toEqual({ email: 'new@example.com' })
    await byText(wrapper, 'button', '发送验证码').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'POST' && r.path === '/me/codes').data).toEqual({ purpose: 'EMAIL_VERIFY' })
    await wrapper.find('input[placeholder="验证码"]').setValue('123456')
    await wrapper.findAll('button').find((b) => b.text() === '验证').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'POST' && r.path === '/me/email/verify').data)
      .toEqual({ email: 'new@example.com', code: '123456' })
  })

  it('TC-E2E-1108 / AC-305-01、AC-310-01：注销页发送 CANCEL 验证码，确认后提交 /me/cancel 并清登录态回登录页', async () => {
    respondWith({
      'GET /me': ME(['游客'], '13800000000', 'old@example.com'),
      'POST /me/codes': {},
      'POST /me/cancel': {}
    })
    uni.showModal.mockImplementationOnce(({ success }) => success({ confirm: true }))
    const { wrapper, pinia } = await mountPage(Cancel)
    expect(wrapper.find('input[placeholder="已绑定的手机号"]').element.value).toBe('13800000000')
    await byText(wrapper, 'button', '发送注销验证码').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'POST' && r.path === '/me/codes').data).toEqual({ purpose: 'CANCEL' })
    await wrapper.find('input[placeholder="验证码"]').setValue('654321')
    await byText(wrapper, 'button', '确认注销').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'POST' && r.path === '/me/cancel').data)
      .toEqual({ phone: '13800000000', code: '654321' })
    expect(uni.reLaunch.mock.calls[0][0]).toMatchObject({ url: '/pages/login/index' })
    expect(uni.getStorageSync('ocap_token')).toBe('')
  })
})
