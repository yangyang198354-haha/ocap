// TC-INT-601~603：小程序角色化首页（ocap_role_home GR-D-001；US-354、US-357、US-359）
import { describe, expect, it } from 'vitest'
import { mountPage, respondWith, requests } from './helpers.js'
import Index from '../pages/index/index.vue'

const ME = ({ units = [], position = null, guest = false, labels = ['游客'] } = {}) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: guest, units, committee: position ? { position } : null, labels }
})

const OWNER_UNIT = { unit_id: 1, role: 'OWNER', role_label: '产权业主', specific_part: 'A' }
const cards = (wrapper) => wrapper.findAll('.card').map((c) => c.text())
const cardIndex = (wrapper, text) => cards(wrapper).findIndex((t) => t.includes(text))

describe('小程序角色化首页', () => {
  it('TC-INT-601 游客：无房屋/任务/管理模块，不请求 housing 与 tasks；财务仅合计；决议带来源标签', async () => {
    respondWith({
      'GET /me': ME({ guest: true }),
      'GET /resolutions': { results: [{ id: 1, title: '加装电梯决议', status: 'APPROVED', decided_at: '2026-11-01T10:00:00Z' }] },
      'GET /polls': { results: [{ id: 2, title: '满意度调查', kind: 'SURVEY', status: 'OPEN' }] },
      'GET /ledger/accounts/summary': { accounts: [{ id: 1, name: '公共账户', balance: '100.00' }], total_balance: '100.00' },
      'GET /info/posts': { results: [] }
    })
    const { wrapper } = await mountPage(Index)
    const text = wrapper.text()
    expect(text).toContain('身份：游客')
    expect(text).toContain('去认证')
    expect(text).not.toContain('我的房屋')
    expect(text).not.toContain('待我处理')
    expect(text).not.toContain('待办审批')
    expect(text).not.toContain('管理快捷')
    expect(text).toContain('¥100.00')
    expect(text).not.toContain('公共账户')
    expect(text).toContain('业委会决议')
    // AC-354-03：模块顺序与 Web 一致（公开决议在投票之前）
    expect(cardIndex(wrapper, '公开决议')).toBeLessThan(cardIndex(wrapper, '投票与调查'))
    expect(requests().some((r) => r.path === '/me/housing')).toBe(false)
    expect(requests().some((r) => r.path === '/approval/tasks')).toBe(false)
  })

  it('TC-INT-602 业主代表：待我表决只含 OPEN REP_VOTE，展示参与状态且无参与率', async () => {
    respondWith({
      'GET /me': ME({ position: 'REPRESENTATIVE', units: [OWNER_UNIT], labels: ['业主代表'] }),
      'GET /me/housing': { pending_review_count: 0, units: [] },
      'GET /resolutions': { results: [] },
      'GET /polls': {
        results: [
          { id: 21, title: '代表表决一', kind: 'REP_VOTE', status: 'OPEN', deadline: '2026-12-01' },
          { id: 22, title: '代表表决二', kind: 'REP_VOTE', status: 'OPEN', deadline: '2026-12-02' },
          { id: 23, title: '普通调查', kind: 'SURVEY', status: 'OPEN' }
        ]
      },
      'GET /polls/21': { id: 21, title: '代表表决一', can_respond: true, my_response: 'YES' },
      'GET /polls/22': { id: 22, title: '代表表决二', can_respond: true, my_response: null },
      'GET /ledger/accounts/summary': { accounts: [], total_balance: '0.00' },
      'GET /info/posts': { results: [] }
    })
    const { wrapper } = await mountPage(Index)
    const text = wrapper.text()
    expect(text).toContain('待我表决 · 2')
    expect(text).toContain('已投票')
    expect(text).toContain('未投票')
    expect(text).not.toContain('参与率')
    const detailPaths = requests().map((r) => r.path).filter((p) => /^\/polls\/\d+$/.test(p))
    expect(detailPaths.sort()).toEqual(['/polls/21', '/polls/22'])
    expect(text).not.toContain('普通调查 · 待我表决')
  })

  it('TC-INT-603 委员兼户主：待办审批在待我处理之前，只有一张待我处理卡', async () => {
    respondWith({
      'GET /me': ME({ position: 'MEMBER', units: [OWNER_UNIT], labels: ['户主', '业委会委员'] }),
      'GET /me/housing': { pending_review_count: 2, units: [] },
      'GET /approval/tasks': { count: 1, results: [{ instance_id: 1, scope: 'EXPENSE', subject_title: '报销#1' }] },
      'GET /resolutions': { results: [] },
      'GET /polls': { results: [] },
      'GET /ledger/accounts/summary': { accounts: [], total_balance: '0.00' },
      'GET /info/posts': { results: [] }
    })
    const { wrapper } = await mountPage(Index)
    const text = wrapper.text()
    expect(text).toContain('待办审批 · 1')
    expect(text).toContain('待我处理 · 2')
    expect(text).toContain('管理快捷')
    expect(cardIndex(wrapper, '待办审批')).toBeLessThan(cardIndex(wrapper, '待我处理'))
    expect(cardIndex(wrapper, '待我处理')).toBeLessThan(cardIndex(wrapper, '财务公开'))
    expect(cardIndex(wrapper, '财务公开')).toBeLessThan(cardIndex(wrapper, '管理快捷'))
    const reviewCards = wrapper.findAll('.card').filter((c) => c.text().includes('待我处理'))
    expect(reviewCards).toHaveLength(1)
  })
})
