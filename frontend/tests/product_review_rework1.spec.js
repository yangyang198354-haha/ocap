// ocap_product_review GROUP_D 缺陷回流 1 后重测（TC-UNIT-579 起，新增；不改动已冻结用例）。
// DEF-020（REQ-FUNC-158：Web 不向用户展示内部值）、DEF-019 的 Web 作废按钮 can_void 条件、GR-C-002-F01（Web 专有映射的守护）。
// 真实页面 + 真实 api.js + 真实 store，仅 mock HTTP 层与 ElMessageBox.confirm。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

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

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, useRoute: () => ({ params: { id: globalThis.__routeId || '1' } }) }
})

import { mountPage, routeTable } from './helpers.js'
import AdminFlows from '@/admin/AdminFlows.vue'
import Tasks from '@/portal/Tasks.vue'
import ResolutionDetail from '@/portal/ResolutionDetail.vue'
import Income from '@/portal/Income.vue'
import InfoList from '@/portal/InfoList.vue'
import Home from '@/portal/Home.vue'
import { FLOW_SCOPE_TEXT, APPROVAL_MODE_TEXT, INCOME_STATUS_TEXT } from '@/shared/labels'

const { http, adminHttp } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const RAW = /RESOLUTION|EXPENSE|INCOME\b|DESIGNATED|HALF_MAJORITY|EFFECTIVE|WITHDRAWN|PENDING|\bVOID\b|\bDRAFT\b|\btrue\b|\bfalse\b/
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const ISO = '2026-11-13T20:30:45+08:00'

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  messageBox.confirm.mockReset()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})

const me = (position) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: false, units: [], labels: [], summary: { code: 'MEMBER', label: '委员' },
    committee: position ? { position, term_end: '2027-01-01' } : null }
})

describe('DEF-020 / REQ-FUNC-158：管理端与用户端不展示内部值', () => {
  it('TC-UNIT-579 / AC-167-03、REQ-FUNC-158：AdminFlows 适用/方式/启用列为中文，页面文字不含内部代码', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/approval/flows': { count: 3, results: [
        { id: 1, name: '决议流程', scope: 'RESOLUTION', mode: 'HALF_MAJORITY', is_active: true },
        { id: 2, name: '财务流程', scope: 'EXPENSE', mode: 'DESIGNATED', is_active: false },
        { id: 3, name: '收入流程', scope: 'INCOME', mode: 'DESIGNATED', is_active: true }] }
    }))
    const { wrapper } = await mountPage(AdminFlows)
    await flush()
    const rows = wrapper.findAll('tbody tr').map((r) => r.text())
    expect(rows).toHaveLength(3)
    expect(rows[0]).toContain('决议')
    expect(rows[0]).toContain('半数以上参与者同意')
    expect(rows[1]).toContain('财务（报销/备用金）')
    expect(rows[1]).toContain('指定负责人审批')
    expect(rows[2]).toContain('收入表')
    expect(rows[0]).toContain('是')
    expect(rows[1]).toContain('否')
    expect(wrapper.text()).not.toMatch(RAW)
  })

  it('TC-UNIT-580 / REQ-FUNC-158：Tasks 待办列表显示中文类别与"年-月-日 时:分"，不含内部代码与 ISO 时间', async () => {
    http.get.mockImplementation(routeTable({
      '/approval/tasks': { count: 2, results: [
        { instance_id: 1, subject_title: '购买水泵', scope: 'EXPENSE', submitted_at: ISO },
        { instance_id: 2, subject_title: '年度决议', scope: 'RESOLUTION', submitted_at: '2026-11-12T08:05:00+08:00' }] }
    }))
    const { wrapper } = await mountPage(Tasks)
    await flush()
    const text = wrapper.text()
    expect(text).toContain('财务（报销/备用金） · 2026-11-13 20:30')
    expect(text).toContain('决议 · 2026-11-12 08:05')
    expect(text).not.toMatch(/EXPENSE|RESOLUTION|T20:30|\+08:00|:45/)
  })

  it('TC-UNIT-581 / REQ-FUNC-158：ResolutionDetail 审批方式为中文（半数以上参与者同意与指定负责人两种）', async () => {
    for (const [mode, label] of [['HALF_MAJORITY', '半数以上参与者同意'], ['DESIGNATED', '指定负责人审批']]) {
      document.body.innerHTML = ''
      globalThis.__routeId = '7'
      http.get.mockImplementation(routeTable({
        '/resolutions/7': { id: 7, title: '议题', content: '正文', status: 'APPROVED', approval_mode: mode,
          initiator: { id: 2 }, attachments: [], vote_counts: null },
        '/me': me('MEMBER')
      }))
      const { wrapper } = await mountPage(ResolutionDetail)
      await flush()
      expect(wrapper.text(), mode).toContain(`审批方式：${label}`)
      expect(wrapper.text(), mode).not.toMatch(/HALF_MAJORITY|DESIGNATED/)
    }
  })

  it('TC-UNIT-582 / REQ-FUNC-158：Income 收入表状态为中文（草稿/审批中/已生效/未通过/已撤回/已作废）', async () => {
    const statuses = ['DRAFT', 'PENDING', 'EFFECTIVE', 'REJECTED', 'WITHDRAWN', 'VOID']
    http.get.mockImplementation(routeTable({
      '/admin/income/sheets': { count: 6, results: statuses.map((s, i) => ({
        id: i + 1, title: `表${i + 1}`, status: s, total_amount: '10.00', period_start: '2026-01-01', period_end: '2026-01-31', can_void: false })) },
      '/approval/flows': { results: [] }, '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Income)
    await flush()
    const text = wrapper.text()
    for (const label of ['草稿', '审批中', '已生效', '未通过', '已撤回', '已作废']) expect(text, label).toContain(label)
    expect(text).not.toMatch(/\bDRAFT\b|\bPENDING\b|\bEFFECTIVE\b|\bREJECTED\b|\bWITHDRAWN\b|\bVOID\b/)
  })

  it('TC-UNIT-583 / REQ-FUNC-158：InfoList 发布时间为"年-月-日 时:分"', async () => {
    http.get.mockImplementation(async (url) => {
      if (url === '/info/posts') return { count: 1, results: [{ id: 1, title: '公告', summary: '摘要', published_at: ISO }] }
      throw new Error(`未预期的请求 ${url}`)
    })
    const { wrapper } = await mountPage(InfoList)
    await flush()
    expect(wrapper.text()).toContain('2026-11-13 20:30')
    expect(wrapper.text()).not.toMatch(/T20:30|\+08:00|:45/)
  })
})

describe('DEF-019 / AC-060-10：Web 作废按钮的 can_void 条件', () => {
  const sheet = (id, status, can_void) => ({ id, title: `表${id}`, status, total_amount: '10.00',
    period_start: '2026-01-01', period_end: '2026-01-31', can_void })

  it('TC-UNIT-584 / AC-060-04、AC-060-10：仅"已生效且 can_void=true"的行有"作废"按钮；非原审批人（can_void=false）、其他状态无；缺 can_void 字段视为无', async () => {
    http.get.mockImplementation(routeTable({
      '/admin/income/sheets': { count: 5, results: [
        sheet(1, 'EFFECTIVE', true), sheet(2, 'EFFECTIVE', false), sheet(3, 'PENDING', true), sheet(4, 'VOID', true),
        { ...sheet(5, 'EFFECTIVE', undefined), can_void: undefined }] },
      '/approval/flows': { results: [] }, '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Income)
    await flush()
    const voidButtons = wrapper.findAll('button').filter((b) => b.text().trim() === '作废')
    expect(voidButtons).toHaveLength(1)
    messageBox.confirm.mockResolvedValue('confirm')
    http.post.mockResolvedValue({})
    await voidButtons[0].trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledWith('/admin/income/sheets/1/void', {})
  })

  it('TC-UNIT-585 / AC-060-04：作废确认取消时不发请求', async () => {
    http.get.mockImplementation(routeTable({
      '/admin/income/sheets': { count: 1, results: [sheet(1, 'EFFECTIVE', true)] },
      '/approval/flows': { results: [] }, '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Income)
    await flush()
    messageBox.confirm.mockRejectedValue('cancel')
    await buttonOf(wrapper, '作废').trigger('click')
    await flush()
    expect(http.post).not.toHaveBeenCalled()
  })
})

describe('REQ-FUNC-158 同类扫描（DEF-020 范围之外的页面）', () => {
  it('TC-UNIT-586 / REQ-FUNC-158：首页待办卡片显示中文类别与"年-月-日 时:分"（业委会成员）', async () => {
    http.get.mockImplementation(routeTable({
      '/me': me('MEMBER'), '/resolutions': { results: [] }, '/polls': { results: [] },
      '/approval/tasks': { count: 1, results: [{ instance_id: 1, subject_title: '购买水泵', scope: 'EXPENSE', submitted_at: ISO }] }
    }))
    const { wrapper } = await mountPage(Home)
    await flush()
    const text = wrapper.text()
    expect(text).toContain('购买水泵')
    expect(text).not.toMatch(/EXPENSE|T20:30|\+08:00/)
    expect(text).toContain('财务（报销/备用金）')
    expect(text).toContain('2026-11-13 20:30')
  })

  it('TC-UNIT-587 / REQ-FUNC-158：决议详情的"表决截止"时间为"年-月-日 时:分"', async () => {
    globalThis.__routeId = '8'
    http.get.mockImplementation(routeTable({
      '/resolutions/8': { id: 8, title: '议题', content: '正文', status: 'PENDING', approval_mode: 'HALF_MAJORITY',
        vote_deadline: ISO, initiator: { id: 2 }, attachments: [], vote_counts: { agree: 0, disagree: 0, abstain: 0 } },
      '/me': me('MEMBER')
    }))
    const { wrapper } = await mountPage(ResolutionDetail)
    await flush()
    expect(wrapper.text()).toContain('表决截止：2026-11-13 20:30')
    expect(wrapper.text()).not.toMatch(/T20:30|\+08:00/)
  })
})

describe('GR-C-002-F01：Web 专有映射的守护（TC-UNIT-561 只比较 *_LABELS）', () => {
  const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')

  it('TC-UNIT-588 / ADR-092、REQ-FUNC-158：Web 专有映射（非 *_LABELS 导出）只有已登记的三个，小程序 labels.js 不含；取值与后端枚举一致', () => {
    const web = read('frontend/src/shared/labels.js')
    const mini = read('miniprogram/utils/labels.js')
    const tables = [...web.matchAll(/export const (\w+)\s*=\s*\{/g)].map((m) => m[1]).filter((n) => !n.endsWith('_LABELS')).sort()
    expect(tables).toEqual(['APPROVAL_MODE_TEXT', 'FLOW_SCOPE_TEXT', 'INCOME_STATUS_TEXT'])
    for (const name of tables) expect(mini, name).not.toContain(`export const ${name}`)
    // 键与后端枚举一致（来源：模型 choices 常量）
    const flowModel = read('backend/apps/approval/models.py')
    const incomeModel = read('backend/apps/income/models.py')
    for (const key of Object.keys(FLOW_SCOPE_TEXT)) expect(flowModel, key).toContain(`"${key}"`)
    for (const key of Object.keys(APPROVAL_MODE_TEXT)) expect(flowModel, key).toContain(`"${key}"`)
    for (const key of Object.keys(INCOME_STATUS_TEXT)) expect(incomeModel, key).toContain(`"${key}"`)
  })

  it('TC-UNIT-589 / REQ-FUNC-158：映射表取值全部为中文，不含英文代码', () => {
    for (const table of [FLOW_SCOPE_TEXT, APPROVAL_MODE_TEXT, INCOME_STATUS_TEXT]) {
      for (const [k, v] of Object.entries(table)) {
        expect(v, k).toMatch(/[一-龥]/)
        expect(v, k).not.toMatch(/[A-Z]{3,}/)
      }
    }
  })
})
