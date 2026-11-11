// 小程序首页语义区块 / 决议卡片三段比例 / 报销类型卡片（GR-C-001-F01/F02）
import { describe, expect, it } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountPage, respondWith, requests } from './helpers.js'
import Index from '../pages/index/index.vue'
import Resolutions from '../pages/resolutions/index.vue'
import Claims from '../pages/claims/index.vue'
import { voteShare } from '../utils/voteShare.js'

const ME = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: false, units: [{ id: 1 }], committee: null, labels: ['户主'] }
}

describe('首页语义区块', () => {
  it('Hero / 待办 / 4 数据卡 / 7 入口 / 投票 / 最新 均渲染，数据来自现有接口', async () => {
    respondWith({
      'GET /me': ME,
      'GET /approval/tasks': { results: [{ instance_id: 3, scope: 'EXPENSE', subject_title: '报销#1' }] },
      'GET /resolutions': { results: [{ id: 1, title: '加装电梯决议', status: 'APPROVED' }] },
      'GET /polls': { results: [{ id: 9, title: '快递柜选址', status: 'OPEN', deadline: '2030-01-01T00:00:00Z' }, { id: 8, title: '旧调查', status: 'CLOSED' }] }
    })
    const { wrapper } = await mountPage(Index)
    for (const cls of ['.home-hero', '.home-todo', '.home-quick', '.home-poll', '.home-latest']) {
      expect(wrapper.find(cls).exists(), cls).toBe(true)
    }
    expect(wrapper.findAll('.home-stat')).toHaveLength(4)
    expect(wrapper.findAll('.home-q')).toHaveLength(7)
    expect(wrapper.find('.home-poll').text()).toContain('快递柜选址')
    expect(wrapper.find('.home-poll').text()).not.toContain('旧调查')
    expect(wrapper.findAll('.home-stat .stat-value').map((n) => n.text())).toEqual(['1', '1', '1', '1'])
  })

  it('投票 / 待办取不到时显示空态，不编造', async () => {
    respondWith({ 'GET /me': ME, 'GET /resolutions': { results: [] } })
    const { wrapper } = await mountPage(Index)
    expect(wrapper.find('.home-poll').text()).toContain('暂无进行中的投票')
    expect(wrapper.find('.home-todo').text()).toContain('暂无审批待办')
    expect(wrapper.findAll('.home-stat .stat-value').map((n) => n.text())).toEqual(['1', '—', '—', '0'])
  })
})

describe('决议卡片三段比例', () => {
  it('voteShare 口径与 Web 一致', () => {
    const s = voteShare({ agree: 5, disagree: 1, abstain: 4 })
    expect([s.agreePct, s.disagreePct, s.abstainPct]).toEqual([50, 10, 40])
  })

  it('列表渲染卡片：编号、比例条宽度、票数；指定负责人不画比例条；请求参数不变', async () => {
    respondWith({
      'GET /resolutions': {
        results: [
          { id: 31, title: '车库照明改造', status: 'PENDING', approval_mode: 'HALF_MAJORITY', vote_deadline: '2026-11-10T18:00:00Z',
            initiator: { labels: ['副主任'] }, vote_counts: { agree: 5, disagree: 1, abstain: 4 } },
          { id: 28, title: '地胶更换', status: 'APPROVED', approval_mode: 'DESIGNATED', initiator: { labels: ['委员'] } }
        ]
      }
    })
    const { wrapper } = await mountPage(Resolutions)
    const cards = wrapper.findAll('.res-card')
    expect(cards).toHaveLength(2)
    expect(cards[0].find('.res-idx').text()).toBe('R-0031')
    expect(cards[0].find('.vote-agree').attributes('style')).toContain('width: 50%')
    expect(cards[0].find('.vote-disagree').attributes('style')).toContain('width: 10%')
    expect(cards[0].find('.vote-abstain').attributes('style')).toContain('width: 40%')
    expect(cards[0].text()).toContain('同意 5')
    expect(cards[0].text()).toContain('半数同意')
    expect(cards[1].find('.vote-bar').exists()).toBe(false)
    expect(requests().find((r) => r.path === '/resolutions').data).toEqual({ scope: 'public' })
  })
})

describe('报销类型卡片', () => {
  it('点击“备用金预借”卡片切换类型，提交仍走 /claims/advances 且字段不变', async () => {
    respondWith({
      'GET /me': ME,
      'GET /approval/flows': { results: [{ id: 7, name: '报销流程' }] },
      'GET /claims': { results: [] },
      'POST /claims/advances': { id: 2 }
    })
    const { wrapper } = await mountPage(Claims)
    const cards = wrapper.findAll('.type-card')
    expect(cards).toHaveLength(2)
    await cards[1].trigger('click')
    expect(wrapper.vm.typeIndex).toBe(1)
    expect(wrapper.findAll('.type-card')[1].classes()).toContain('is-selected')
    wrapper.vm.pickFlow({ detail: { value: 0 } })
    Object.assign(wrapper.vm, { amount: '1000.00', reason: '活动', expectedUsage: '小区活动', expectedSettleOn: '2026-12-01' })
    await wrapper.vm.create()
    await flushPromises()
    expect(requests().find((r) => r.path === '/claims/advances').data).toEqual({
      amount: '1000.00', reason: '活动', expected_usage: '小区活动',
      expected_settle_on: '2026-12-01', approval_flow_id: 7
    })
  })
})
