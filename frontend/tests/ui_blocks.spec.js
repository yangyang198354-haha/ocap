// 首页语义区块 / 决议卡片三段比例 / 报销类型卡片与金额输入（GR-C-001-F01/F02；AC-074-02、AC-087-02、AC-081-03）
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import Home from '@/portal/Home.vue'
import Resolutions from '@/portal/Resolutions.vue'
import Claims from '@/portal/Claims.vue'
import { voteShare, remaining } from '@/shared/voteShare'
import { THEMES } from '@/theme/generated/registry.js'

const { http } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const SRC = path.resolve(ROOT, 'frontend/src')

const ME = {
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: false, units: [{ id: 1 }, { id: 2 }], committee: { position: 'MEMBER' }, labels: ['户主', '业委会委员'] }
}
const FUTURE = new Date(Date.now() + 3 * 86400000).toISOString()

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

function vueFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) return vueFiles(p)
    return p.endsWith('.vue') ? [p] : []
  })
}

describe('首页语义区块（AC-074-02）', () => {
  const routes = routeTable({
    '/me': ME,
    '/resolutions': { results: [{ id: 1, title: '加装电梯决议', status: 'APPROVED' }, { id: 2, title: '车库照明', status: 'REJECTED' }] },
    '/approval/tasks': { results: [{ instance_id: 3, scope: 'EXPENSE', subject_title: '报销#1' }] },
    '/polls': { results: [{ id: 9, title: '快递柜选址', kind: 'SURVEY', status: 'OPEN', deadline: FUTURE }, { id: 8, title: '旧调查', status: 'CLOSED' }] }
  })

  for (const theme of THEMES) {
    it(`三套风格（${theme.key}）下首页按角色渲染模块且不再有统计卡与快捷宫格`, async () => {
      document.documentElement.setAttribute('data-theme', theme.key)
      http.get.mockImplementation(routes)
      const { wrapper } = await mountPage(Home)
      for (const cls of ['.home-hero', '.home-todo', '.home-accounts', '.home-poll', '.home-latest', '.home-info']) {
        expect(wrapper.find(cls).exists(), cls).toBe(true)
      }
      expect(wrapper.findAll('.home-stat')).toHaveLength(0)
      expect(wrapper.findAll('.home-q')).toHaveLength(0)
      // 真实数据：待办、进行中投票（仅 OPEN）、倒计时
      expect(wrapper.find('.home-todo').text()).toContain('报销#1')
      expect(wrapper.find('.home-poll').text()).toContain('快递柜选址')
      expect(wrapper.find('.home-poll').text()).not.toContain('旧调查')
      expect(wrapper.findAll('.home-countdown b')).toHaveLength(3)
      expect(wrapper.find('.home-hero').text()).toContain('你好，张三')
      expect(wrapper.text()).toContain('管理快捷')
      expect(wrapper.text()).toContain('我的房屋 · 2')
      document.documentElement.removeAttribute('data-theme')
    })
  }

  it('取不到的数据不编造：待办失败、投票失败 → 任务卡隐藏，投票保留空态', async () => {
    http.get.mockImplementation(routeTable({ '/me': ME, '/resolutions': { results: [] } }))
    const { wrapper } = await mountPage(Home)
    expect(wrapper.find('.home-todo').exists()).toBe(false)
    expect(wrapper.find('.home-poll').text()).toContain('暂无进行中的投票')
    expect(wrapper.find('.home-countdown').exists()).toBe(false)
    expect(wrapper.find('.home-hero').text()).not.toContain('项审批待办')
  })

  it('首页布局差异在各风格文件中：三份 web.css 都按 html[data-theme] 定义 .home-* 布局', () => {
    for (const t of THEMES) {
      const css = fs.readFileSync(path.join(ROOT, 'themes', `${t.key}.web.css`), 'utf8')
      expect(css, t.key).toContain(`html[data-theme="${t.key}"] .home-grid`)
      expect(css, t.key).toContain(`html[data-theme="${t.key}"] .home-hero`)
    }
    const bento = fs.readFileSync(path.join(ROOT, 'themes/bento.web.css'), 'utf8')
    // Hero 回到 grid 内占 2×2，宽屏下与待办卡共同填满首行
    expect(bento).toMatch(/\.home-hero \{[^}]*grid-row: span 2/)
    expect(bento).toMatch(/\.home-todo \{[^}]*grid-column: span 2/)
    expect(bento).toContain('.home-stat.is-odd')
  })
})

describe('页面不含风格专属判断（AC-080-02 扩展）', () => {
  it('portal / admin 下 .vue 不出现 data-theme、风格 key 字面量或 current 与字面量的比较', () => {
    const bad = []
    for (const dir of ['portal', 'admin']) {
      for (const file of vueFiles(path.join(SRC, dir))) {
        const text = fs.readFileSync(file, 'utf8')
        const hit = text.match(/data-theme(?!-key)|\.current\s*[!=]==?\s*['"]|['"](neon|bento|terminal)['"]/g)
        if (hit) bad.push(`${path.relative(SRC, file)}: ${hit.join(',')}`)
      }
    }
    expect(bad).toEqual([])
  })
})

describe('决议卡片三段比例（AC-087-02）', () => {
  it('voteShare：同意 / 反对 / 弃权占已投票数；无票时全为 0', () => {
    const s = voteShare({ agree: 5, disagree: 1, abstain: 4 })
    expect(s.total).toBe(10)
    expect([s.agreePct, s.disagreePct, s.abstainPct]).toEqual([50, 10, 40])
    expect(voteShare({ agree: 0, disagree: 0, abstain: 0 }).agreePct).toBe(0)
    expect(voteShare(undefined).total).toBe(0)
  })

  it('remaining：剩余天时分，过期标记 expired', () => {
    const now = Date.parse('2026-11-09T00:00:00Z')
    expect(remaining('2026-11-11T14:36:00Z', now)).toEqual({ expired: false, days: 2, hours: 14, minutes: 36 })
    expect(remaining('2026-11-08T00:00:00Z', now).expired).toBe(true)
    expect(remaining(null, now)).toBeNull()
  })

  it('列表渲染卡片：编号、三段条宽度、票数、发起人、审批方式、截止；指定负责人不画比例条（F9 改写，AC-250-01/05、AC-249-01）', async () => {
    // 旧：条宽 = 票数/已投票数（50/10/40，无 participation）；新：分母=participation.expected（应参与人数），
    // 夹具 expected=20：同意 5→25%、反对 1→5%、弃权 4→20%，余 50% 留白；并断言"已参与 10 / 20 · 50%"与"进行中"
    http.get.mockImplementation(routeTable({
      '/me': ME,
      '/resolutions': {
        results: [
          { id: 31, title: '车库照明改造', status: 'PENDING', approval_mode: 'HALF_MAJORITY', vote_deadline: '2026-11-10T18:00:00Z',
            initiator: { labels: ['副主任'], display_name: '发起人甲' }, vote_counts: { agree: 5, disagree: 1, abstain: 4 },
            participation: { voted: 10, expected: 20 } },
          { id: 28, title: '地胶更换', status: 'APPROVED', approval_mode: 'DESIGNATED', initiator: { labels: ['委员'], display_name: '发起人乙' }, participation: null }
        ]
      },
      '/approval/flows': { results: [] }
    }))
    const { wrapper } = await mountPage(Resolutions)
    const cards = wrapper.findAll('.res-card')
    expect(cards).toHaveLength(2)
    expect(cards[0].find('.res-idx').text()).toBe('R-0031')
    const widths = cards[0].findAll('.vote-bar i').map((i) => i.attributes('style'))
    expect(widths[0]).toContain('width: 25%')
    expect(widths[1]).toContain('width: 5%')
    expect(widths[2]).toContain('width: 20%')
    const text = cards[0].text()
    for (const t of ['车库照明改造', '同意 5', '反对 1', '弃权 4', '副主任', '发起人甲', '半数以上参与者同意', '截止', '已参与 10 / 20 · 50%', '进行中']) expect(text).toContain(t)
    expect(cards[1].find('.vote-bar').exists()).toBe(false)
    expect(cards[1].text()).toContain('指定负责人')
    expect(http.get).toHaveBeenCalledWith('/resolutions', { params: { scope: 'public', page: 1, page_size: 20 } })
  })
})

describe('报销表单控件（AC-087-02 / AC-081-03）', () => {
  const claimsRoutes = routeTable({
    '/me': ME,
    '/claims': { results: [] },
    '/approval/flows': { results: [{ id: 7, name: '日常支出', mode: 'DESIGNATED' }] },
    '/ledger/accounts/summary': { accounts: [{ id: 1, name: '基本账户', is_default: true }] }
  })

  async function openForm() {
    http.get.mockImplementation(claimsRoutes)
    const mounted = await mountPage(Claims)
    mounted.wrapper.vm.openCreate()
    await flushPromises()
    return mounted
  }

  it('申请类型为两张可选卡片，点击切换 form.type；步骤条写明不可审批本人申请', async () => {
    const { wrapper } = await openForm()
    const cards = document.body.querySelectorAll('.type-card')
    expect(cards).toHaveLength(2)
    expect(cards[0].classList.contains('is-selected')).toBe(true)
    cards[1].click()
    await flushPromises()
    expect(wrapper.vm.form.type).toBe('ADVANCE')
    expect(document.body.querySelectorAll('.type-card')[1].classList.contains('is-selected')).toBe(true)
    expect(document.body.textContent).toContain('不可审批本人提交的申请')
    expect(document.body.querySelectorAll('.claim-step').length).toBe(3)
  })

  it('¥ 金额输入绑定 form.amount，提示两位小数；事由计数；提交字段与原来一致', async () => {
    http.post.mockResolvedValue({ id: 5 })
    const { wrapper } = await openForm()
    const input = document.body.querySelector('.money-input input')
    input.value = '300.50'
    input.dispatchEvent(new Event('input'))
    await flushPromises()
    expect(wrapper.vm.form.amount).toBe('300.50')
    expect(document.body.textContent).toContain('最多两位小数')
    wrapper.vm.form.reason = '购买灯泡'
    await flushPromises()
    expect(document.body.querySelector('.field-count').textContent).toContain('4 / 500')
    wrapper.vm.invoiceFiles.push({ id: 'att-1', name: 'inv.pdf', size: 2048 })
    wrapper.vm.invoiceIds.push('att-1')
    Object.assign(wrapper.vm.form, { occurred_on: '2026-11-01', approval_flow_id: 7 })
    await flushPromises()
    expect(document.body.querySelector('.file-row').textContent).toContain('inv.pdf')
    await wrapper.vm.create()
    expect(http.post).toHaveBeenLastCalledWith('/claims/reimbursements', {
      amount: '300.50', reason: '购买灯泡', occurred_on: '2026-11-01',
      invoice_ids: ['att-1'], approval_flow_id: 7, account_id: 1
    })
  })

  it('上传发票仍调用 /attachments(purpose=INVOICE)，列表显示文件名并可删除', async () => {
    http.post.mockResolvedValue({ id: 'att-9' })
    const { wrapper } = await openForm()
    await wrapper.vm.uploadInvoice({ file: new File(['x'], 'a.pdf') })
    await flushPromises()
    const upload = http.post.mock.calls.find((c) => c[0] === '/attachments')
    expect(upload[1].get('purpose')).toBe('INVOICE')
    expect(wrapper.vm.invoiceIds).toEqual(['att-9'])
    expect(document.body.querySelector('.file-row').textContent).toContain('a.pdf')
    wrapper.vm.removeInvoice('att-9')
    await flushPromises()
    expect(wrapper.vm.invoiceIds).toEqual([])
    expect(document.body.querySelector('.file-row')).toBeNull()
  })
})
