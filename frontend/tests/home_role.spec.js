// TC-WEB-601~606：角色化首页（ocap_role_home GR-D-001；US-354~359 / AC-354-01/02、AC-355-01/02/03、AC-356-02/03、AC-357-01/02/03、AC-358-01、AC-359-01/02/03）
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import Home from '@/portal/Home.vue'

const { http } = mocked

const ME = ({ units = [], position = null, guest = false, labels = ['游客'] } = {}) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: guest,
    units,
    committee: position ? { position } : null,
    labels
  }
})

const OWNER_UNIT = { unit_id: 1, role: 'OWNER', role_label: '产权业主', specific_part: 'A' }
const RESIDENT_UNIT = { unit_id: 2, role: 'RESIDENT', role_label: '同住人', specific_part: 'B' }
const empty = { results: [] }

const sectionText = (wrapper) => wrapper.findAll('section').map((s) => s.text())
const sectionIndex = (wrapper, text) => sectionText(wrapper).findIndex((t) => t.includes(text))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

describe('角色化首页（Web）', () => {
  it('TC-WEB-601 游客：不渲染房屋/任务/管理模块，不请求 /me/housing 与 /approval/tasks；财务只显示合计；决议带来源标签', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME({ guest: true }),
      '/resolutions': { results: [{ id: 11, title: '加装电梯决议', status: 'APPROVED', decided_at: '2026-11-01T10:00:00Z' }] },
      '/polls': { results: [{ id: 12, title: '满意度调查', kind: 'SURVEY', status: 'OPEN' }] },
      '/ledger/accounts/summary': { accounts: [{ id: 1, name: '公共账户', balance: '100.00' }], total_balance: '100.00' },
      '/info/posts': empty
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('当前身份：游客')
    expect(text).toContain('去认证')
    expect(text).not.toContain('我的房屋')
    expect(text).not.toContain('待我处理')
    expect(text).not.toContain('待办审批')
    expect(text).not.toContain('管理快捷')
    // D-RH-03：游客看合计 + 报表入口，不看逐账户明细
    expect(text).toContain('¥100.00')
    expect(text).not.toContain('公共账户')
    expect(text).toContain('业委会决议')
    expect(http.get.mock.calls.some((c) => c[0] === '/me/housing')).toBe(false)
    expect(http.get.mock.calls.some((c) => c[0] === '/approval/tasks')).toBe(false)
    // AC-354-01：公开决议在投票之前
    expect(sectionIndex(wrapper, '公开决议')).toBeLessThan(sectionIndex(wrapper, '投票与调查'))
  })

  it('TC-WEB-602 业主代表：待我表决只含业主达标投票，展示参与状态、无参与率，详情请求有上界', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME({ position: 'REPRESENTATIVE', units: [OWNER_UNIT], labels: ['业主代表'] }),
      '/me/housing': { pending_review_count: 0, units: [] },
      '/resolutions': empty,
      '/polls': {
        results: [
          { id: 21, title: '代表表决一', kind: 'REP_VOTE', status: 'OPEN', deadline: '2026-12-01T00:00:00Z' },
          { id: 22, title: '代表表决二', kind: 'REP_VOTE', status: 'OPEN', deadline: '2026-12-02T00:00:00Z' },
          { id: 23, title: '普通调查', kind: 'SURVEY', status: 'OPEN' },
          { id: 24, title: '已截止代表表决', kind: 'REP_VOTE', status: 'CLOSED' }
        ]
      },
      '/polls/21': { id: 21, title: '代表表决一', can_respond: true, my_response: 'YES' },
      '/polls/22': { id: 22, title: '代表表决二', can_respond: true, my_response: null },
      '/ledger/accounts/summary': { accounts: [], total_balance: '0.00' },
      '/info/posts': empty
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('待我表决 · 2')
    expect(text).toContain('代表表决一')
    expect(text).toContain('已投票')
    expect(text).toContain('未投票')
    expect(text).not.toContain('参与率')
    const detailCalls = http.get.mock.calls.map((c) => c[0]).filter((p) => /^\/polls\/\d+$/.test(p))
    expect(detailCalls.sort()).toEqual(['/polls/21', '/polls/22'])
    // AC-357-02：普通调查不进入待我表决
    const pendingVotes = wrapper.findAll('section').find((s) => s.text().includes('待我表决'))
    expect(pendingVotes.text()).not.toContain('普通调查')
    // AC-357-03 / AC-354-02：已截止代表投票进入公开决议并带来源标签
    expect(text).toContain('已截止代表表决')
    expect(text).toContain('业主代表决议')
  })

  it('TC-WEB-603 委员兼户主：任务排序为待办审批→待我处理，只有一张待我处理卡，数量只出现一次', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME({ position: 'MEMBER', units: [OWNER_UNIT], labels: ['户主', '业委会委员'] }),
      '/me/housing': { pending_review_count: 2, units: [] },
      '/approval/tasks': { results: [
        { instance_id: 1, scope: 'EXPENSE', subject_title: '报销#1' },
        { instance_id: 2, scope: 'EXPENSE', subject_title: '报销#2' },
        { instance_id: 3, scope: 'ADVANCE', subject_title: '备用金#3' },
        { instance_id: 4, scope: 'SETTLEMENT', subject_title: '核销#4' }
      ] },
      '/resolutions': empty,
      '/polls': empty,
      '/ledger/accounts/summary': { accounts: [], total_balance: '0.00' },
      '/info/posts': empty
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('待办审批 · 4')
    expect(text).toContain('待我处理 · 2')
    // AC-358-01：最多列出 3 条 + “全部”入口
    const taskSection = wrapper.findAll('section').find((s) => s.text().includes('待办审批'))
    expect(taskSection.findAll('.todo-item')).toHaveLength(3)
    expect(taskSection.text()).toContain('全部')
    expect(text).toContain('管理快捷')
    expect(sectionIndex(wrapper, '待办审批')).toBeLessThan(sectionIndex(wrapper, '待我处理'))
    expect(sectionIndex(wrapper, '待我处理')).toBeLessThan(sectionIndex(wrapper, '财务公开'))
    expect(sectionIndex(wrapper, '财务公开')).toBeLessThan(sectionIndex(wrapper, '管理快捷'))
    const reviewCards = wrapper.findAll('section').filter((s) => s.text().includes('待我处理'))
    expect(reviewCards).toHaveLength(1)
    expect(wrapper.text()).toContain('待我处理 · 2')
  })

  it('TC-WEB-604 同住人：与产权业主同版式，只读房屋，不请求 /me/housing，不显示待我处理', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME({ units: [RESIDENT_UNIT], labels: ['同住人'] }),
      '/resolutions': { results: [{ id: 31, title: '公共决议', status: 'APPROVED' }] },
      '/polls': { results: [{ id: 32, title: '街道代表表决', kind: 'REP_VOTE', status: 'CLOSED' }] },
      '/ledger/accounts/summary': { accounts: [{ id: 1, name: '账户A', balance: '1.00' }], total_balance: '1.00' },
      '/info/posts': empty
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('我的房屋 · 1')
    expect(text).not.toContain('待我处理')
    // AC-355-01：欢迎卡 → 我的房屋 → 投票 → 公开决议 → 信息公开 → 财务公开
    expect(sectionIndex(wrapper, '我的房屋')).toBeLessThan(sectionIndex(wrapper, '投票与调查'))
    expect(sectionIndex(wrapper, '投票与调查')).toBeLessThan(sectionIndex(wrapper, '公开决议'))
    expect(sectionIndex(wrapper, '公开决议')).toBeLessThan(sectionIndex(wrapper, '信息公开'))
    expect(sectionIndex(wrapper, '信息公开')).toBeLessThan(sectionIndex(wrapper, '财务公开'))
    expect(http.get.mock.calls.some((c) => c[0] === '/me/housing')).toBe(false)
    expect(http.get.mock.calls.some((c) => c[0] === '/approval/tasks')).toBe(false)
    // 同住人不是游客：保留逐账户明细；AC-355-03：公开决议含业主代表来源
    expect(text).toContain('账户A')
    expect(text).toContain('业主代表决议')
  })

  it('TC-WEB-605 内容类空态保留、任务类 0 隐藏', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME({ units: [OWNER_UNIT], labels: ['产权业主'] }),
      '/me/housing': { pending_review_count: 0, units: [] },
      '/resolutions': empty,
      '/polls': empty,
      '/ledger/accounts/summary': { accounts: [], total_balance: '0.00' },
      '/info/posts': empty
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('投票与调查 · 0')
    expect(text).toContain('暂无进行中的投票')
    expect(text).toContain('公开决议 · 0')
    expect(text).toContain('暂无公开决议')
    expect(text).toContain('暂无公告')
    expect(text).not.toContain('待我处理')
  })

  it('TC-WEB-606 业主代表兼户主：待我表决→待我处理→投票→公开决议→财务公开→信息公开，无待办审批与管理快捷', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME({ position: 'REPRESENTATIVE', units: [OWNER_UNIT], labels: ['业主代表', '户主'] }),
      '/me/housing': { pending_review_count: 1, units: [] },
      '/polls': { results: [{ id: 41, title: '代表表决', kind: 'REP_VOTE', status: 'OPEN', deadline: '2026-12-01T00:00:00Z' }] },
      '/polls/41': { id: 41, title: '代表表决', can_respond: true, my_response: null },
      '/resolutions': { results: [{ id: 42, title: '公共决议', status: 'APPROVED' }] },
      '/ledger/accounts/summary': { accounts: [], total_balance: '0.00' },
      '/info/posts': empty
    }))
    const { wrapper } = await mountPage(Home)
    const text = wrapper.text()
    expect(text).toContain('待我表决 · 1')
    expect(text).toContain('待我处理 · 1')
    expect(sectionIndex(wrapper, '待我表决')).toBeLessThan(sectionIndex(wrapper, '待我处理'))
    expect(sectionIndex(wrapper, '待我处理')).toBeLessThan(sectionIndex(wrapper, '投票与调查'))
    expect(sectionIndex(wrapper, '投票与调查')).toBeLessThan(sectionIndex(wrapper, '公开决议'))
    expect(sectionIndex(wrapper, '公开决议')).toBeLessThan(sectionIndex(wrapper, '财务公开'))
    expect(sectionIndex(wrapper, '财务公开')).toBeLessThan(sectionIndex(wrapper, '信息公开'))
    expect(wrapper.findAll('section').filter((s) => s.text().includes('待我处理'))).toHaveLength(1)
    expect(text).not.toContain('待办审批')
    expect(text).not.toContain('管理快捷')
    expect(http.get.mock.calls.some((c) => c[0] === '/approval/tasks')).toBe(false)
  })
})
