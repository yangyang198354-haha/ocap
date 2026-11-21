// ocap_profile_ux GROUP_D：资料字段 / 他人 profile / 席位表格 / 房屋关系搜索 / 右上角头像。
// 层级：unit（页面 + 真实 api.js，仅 mock HTTP）。TC-UNIT-1501 起。
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import UserProfile from '@/portal/UserProfile.vue'
import ParticipantList from '@/portal/parts/ParticipantList.vue'
import MeProfile from '@/portal/me/MeProfile.vue'
import AdminSeats from '@/admin/AdminSeats.vue'
import AdminMemberships from '@/admin/AdminMemberships.vue'
import PortalUserMenu from '@/portal/PortalUserMenu.vue'
import { meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'

const { http, adminHttp } = mocked
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (root, text) => root.findAll('button').find((b) => b.text().includes(text))

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})

beforeEach(() => {
  vi.clearAllMocks()
  for (const m of [...Object.values(http), ...Object.values(adminHttp)]) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

describe('US-270 / US-272：他人 profile 页', () => {
  it('TC-UNIT-1501：展示昵称/身份/签名，is_self 时显示编辑入口；无敏感字段', async () => {
    http.get.mockResolvedValue({
      id: 7, nickname: '昵称甲', avatar_url: null,
      identity: { code: 'HEAD', label: '产权业主' }, labels: ['产权业主'],
      real_name: null, signature: '第一行\n第二行', is_self: true
    })
    const { wrapper } = await mountPage(UserProfile, { path: '/users/7/profile' })
    await flush()
    expect(wrapper.text()).toContain('昵称甲')
    expect(wrapper.text()).toContain('产权业主')
    expect(wrapper.text()).toContain('第一行')
    expect(buttonOf(wrapper, '编辑资料')).toBeTruthy()
    expect(wrapper.text()).not.toMatch(/1[3-9]\d{9}|@/)
  })

  it('TC-UNIT-1502：签名档为空显示空状态文案；他人页面无编辑入口', async () => {
    http.get.mockResolvedValue({
      id: 8, nickname: '昵称乙', avatar_url: null,
      identity: { code: 'GUEST', label: '游客' }, labels: ['游客'],
      real_name: null, signature: '', is_self: false
    })
    const { wrapper } = await mountPage(UserProfile, { path: '/users/8/profile' })
    await flush()
    expect(wrapper.text()).toContain('这个人很懒，什么都没写')
    expect(buttonOf(wrapper, '编辑资料')).toBeFalsy()
  })

  it('TC-UNIT-1509：实名可见时顺序为昵称 → 实名+徽章 → 身份，身份样式独立（AC-273-01/274-01/275-01）', async () => {
    http.get.mockResolvedValue({
      id: 9, nickname: '昵称丙', avatar_url: null,
      identity: { code: 'HEAD', label: '产权业主' }, labels: ['产权业主'],
      real_name: '杨扬', signature: '', is_self: false
    })
    const { wrapper } = await mountPage(UserProfile, { path: '/users/9/profile' })
    await flush()
    const text = wrapper.text()
    expect(text.indexOf('昵称丙')).toBeLessThan(text.indexOf('杨扬'))
    expect(text.indexOf('杨扬')).toBeLessThan(text.indexOf('产权业主'))
    expect(wrapper.find('.real-name').exists()).toBe(true)
    expect(wrapper.find('.real-name .verified-badge').text()).toContain('已实名认证')
    expect(wrapper.find('.identity-tag').text()).toContain('产权业主')
  })

  it('TC-UNIT-1510：无实名时不渲染实名文本与认证徽章（AC-273-02/274-02）', async () => {
    http.get.mockResolvedValue({
      id: 10, nickname: '昵称丁', avatar_url: null,
      identity: { code: 'GUEST', label: '游客' }, labels: ['游客'],
      real_name: null, signature: '', is_self: false
    })
    const { wrapper } = await mountPage(UserProfile, { path: '/users/10/profile' })
    await flush()
    expect(wrapper.find('.real-name').exists()).toBe(false)
    expect(wrapper.find('.verified-badge').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('实名：')
    expect(wrapper.find('.identity-tag').exists()).toBe(true)
  })

  it('TC-UNIT-1511：昵称为空时显示占位且仍在身份之前（AC-273-03）', async () => {
    http.get.mockResolvedValue({
      id: 11, nickname: '', avatar_url: null,
      identity: { code: 'GUEST', label: '游客' }, labels: ['游客'],
      real_name: null, signature: '', is_self: false
    })
    const { wrapper } = await mountPage(UserProfile, { path: '/users/11/profile' })
    await flush()
    const text = wrapper.text()
    expect(text).toContain('未设置昵称')
    expect(text.indexOf('未设置昵称')).toBeLessThan(text.indexOf('游客'))
  })

  it('TC-UNIT-1512：实名与身份的样式规则不同（AC-275-01/275-02）', () => {
    const src = readFileSync('src/portal/UserProfile.vue', 'utf8')
    const realRule = src.match(/\.real-name\s*\{([^}]*)\}/)[1]
    const identityRule = src.match(/\.identity-tag\s*\{([^}]*)\}/)[1]
    expect(realRule).toContain('var(--text)')
    expect(realRule).toContain('font-weight: 650')
    expect(identityRule).not.toContain('var(--text)')
    expect(identityRule).not.toContain('font-weight: 650')
  })
})

describe('US-270 / AC-270-01：展示昵称/头像的位置可进入 profile', () => {
  it('TC-UNIT-1508：参与人昵称与头像可点击；缺 user_id 时退化为纯文本', async () => {
    const { wrapper } = await mountPage(ParticipantList, {
      path: '/resolutions/1',
      props: { items: [
        { user_id: 12, display_name: '委员甲', avatar_url: null, voted_at: '2026-11-18T10:00:00+08:00' },
        { display_name: '委员乙', avatar_url: null, voted_at: '2026-11-18T10:01:00+08:00' }
      ] }
    })
    await flush()
    const rows = wrapper.findAll('.participant-item')
    expect(rows[0].find('a').attributes('href')).toBe('/users/12/profile')
    expect(rows[0].find('a').text()).toContain('委员甲')
    expect(rows[1].find('a').exists()).toBe(false)
    expect(rows[1].text()).toContain('委员乙')
  })
})

describe('US-271 / US-272：个人资料页新增表单', () => {
  const profile = { id: 2, account_no: '8000000003', nickname: '昵称甲', gender: 0, birthday: null,
    phone: '138****0000', email: null, avatar_url: null, signature: '', real_name: '', real_name_visible: false }

  it('TC-UNIT-1503：保存签名档提交 signature；非产权业主不显示实名开关', async () => {
    http.get.mockResolvedValue({ ...profile })
    http.patch.mockResolvedValue({ ...profile, signature: '你好' })
    const { wrapper } = await mountPage(MeProfile, { path: '/me/profile' })
    await flush()
    await wrapper.find('textarea').setValue('你好')
    await buttonOf(wrapper, '保存签名档').trigger('click')
    await flush()
    expect(http.patch).toHaveBeenCalledWith('/me/profile', { signature: '你好' })
    const switches = wrapper.findAll('.el-switch')
    expect(switches.length).toBe(1)
    expect(switches[0].classes()).toContain('is-disabled')
  })

  it('TC-UNIT-1507：后端判定可展示实名时开关可用（AC-271-03，含业委会成员）', async () => {
    http.get.mockResolvedValue({ ...profile, real_name: '张三', can_show_real_name: true })
    const { wrapper } = await mountPage(MeProfile, { path: '/me/profile' })
    await flush()
    const switchEl = wrapper.find('.el-switch')
    expect(switchEl.classes()).not.toContain('is-disabled')
    expect(wrapper.text()).toContain('主页仅展示昵称')
  })
})

describe('US-264 / US-265：席位表格', () => {
  const SEAT = {
    id: 1, position: 'MEMBER', status: 'ACTIVE', effective: true, bind_state: 'BOUND',
    user: { id: 7, account_no: '8000000007', nickname: '昵称甲' },
    holder: { kind: 'USER', unit_text: null, owner_name: null },
    holder_detail: { nickname: '昵称甲', name: '张三', phone: '13800000001', unit_text: '1栋1单元9层902号',
                     unit_type: '住宅', building: '1栋', unit_no: '1单元', floor: '9' },
    term_start: '2026-01-01', term_end: '2027-01-01'
  }

  function mockSeats() {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/committee/seats': (arg) => ({ count: 1, page: 1, page_size: 20,
        ended_count: 2, results: arg?.params?.bucket === 'ended' ? [] : [SEAT] }),
      '/admin/committee/config': { cap_chair: 1, cap_vice: 1, cap_member: 3, cap_rep: 3 },
      '/admin/registry/unit-options': { level: 'building', options: [{ value: '1栋' }] }
    }))
  }

  it('TC-UNIT-1504：主表 15 列（含楼栋/单元/楼层/房号/面积）、默认 bucket=active、展开后请求 bucket=ended', async () => {
    mockSeats()
    const { wrapper } = await mountPage(AdminSeats)
    await flush()
    const headers = wrapper.findAll('th').map((th) => th.text().trim())
    for (const label of ['昵称', '姓名', '联系电话', '专有部分坐落', '楼栋', '单元', '楼层', '房号',
      '专有部分类型', '面积', '职位', '状态', '任期开始', '任期结束', '操作']) {
      expect(headers).toContain(label)
    }
    const first = adminHttp.get.mock.calls.find((c) => c[0] === '/admin/committee/seats')[1].params
    expect(first.bucket).toBe('active')
    expect(wrapper.text()).toContain('13800000001')  // REQ-FUNC-292：管理后台显示完整手机号
    expect(wrapper.text()).toContain('住宅')
    expect(wrapper.text()).toContain('资格失效 / 已结束（2）')  // AC-265-01：展开前显示条数
    await wrapper.find('.el-collapse-item__header').trigger('click')
    await flush()
    const calls = adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/committee/seats')
    expect(calls.at(-1)[1].params.bucket).toBe('ended')
  })
})

describe('US-268 / US-269：房屋关系过滤与搜索', () => {
  const ROW = {
    id: 1, unit_id: 3, specific_part: '2栋3单元10层1001号', role: 'HEAD', source: 'CERTIFIED',
    certified_at: '2026-11-18T10:00:00+08:00', real_name: '王五',
    user: { id: 9, account_no: '8000000009', nickname: '四哥', phone: '13900001111' }
  }

  function mockMemberships() {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/memberships': { count: 1, page: 1, page_size: 20, results: [ROW] },
      '/admin/registry/unit-options': { level: 'building', options: [{ value: '2栋' }] }
    }))
  }

  it('TC-UNIT-1505：昵称/账号、实名、手机号分别走 q/name/phone 参数，并展示实名与完整手机号', async () => {
    mockMemberships()
    const { wrapper } = await mountPage(AdminMemberships)
    await flush()
    const input = (placeholder) => wrapper.find(`input[placeholder="${placeholder}"]`)
    const search = async () => {
      await buttonOf(wrapper, '搜索').trigger('click')
      await flush()
      return adminHttp.get.mock.calls.filter((c) => c[0] === '/admin/memberships').at(-1)[1].params
    }
    await input('昵称 / 账号').setValue('四哥')
    expect((await search()).q).toBe('四哥')
    await input('实名').setValue('王五')
    expect((await search()).name).toBe('王五')
    await input('手机号').setValue('1111')
    expect((await search()).phone).toBe('1111')
    expect(wrapper.text()).toContain('王五')
    expect(wrapper.text()).toContain('13900001111')
    expect(wrapper.find('a[href*="/users/9/profile"]').exists()).toBe(true)
  })
})

describe('US-262：右上角头像', () => {
  it('TC-UNIT-1506：头像与昵称同触发器；无头像时回退默认头像图片', async () => {
    http.get.mockResolvedValue(new Blob())
    const pinia = createPinia()
    useAuthStore(pinia).me = { profile: { nickname: '昵称甲', avatar_url: null } }
    const { wrapper } = await mountPage(PortalUserMenu, { pinia })
    await flush()
    const trigger = wrapper.find('.user-menu-trigger')
    expect(trigger.text()).toContain('昵称甲')
    const img = trigger.find('img.auth-image')
    expect(img.exists()).toBe(true)
    expect(img.attributes('alt')).toBe('默认头像')
  })
})

describe('契约：新增客户端调用与后端路由对应', () => {
  it('TC-INT-1501：meApi.userProfile → GET /users/{id}/profile', async () => {
    http.get.mockResolvedValue({})
    await meApi.userProfile(7)
    expect(http.get).toHaveBeenCalledWith('/users/7/profile', { params: undefined })
  })
})
