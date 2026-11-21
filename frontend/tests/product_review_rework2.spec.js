// ocap_product_review GROUP_D 缺陷回流 2 后重测（TC-UNIT-590 起，新增；不改动已冻结的 579 ~ 589 及更早用例）。
// 范围：回流 2 同类扫描另修的 8 处（InfoDetail、AdminAudit、AdminFinance、AdminMemberships、AdminContentPosts、
//   AdminContentEditor 保存历史、Tasks 标题回退）的页面级验证；GR-C-003 条件：shared/adminText.js 四张映射的守护。
// 溯源：REQ-FUNC-158 / US-167（AC-167-02、AC-167-03）。真实页面 + 真实 api.js，仅 mock HTTP 层。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeAll, beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, useRoute: () => ({ params: { id: globalThis.__routeId || '7' } }) }
})

import { mountPage, routeTable } from './helpers.js'
import InfoDetail from '@/portal/InfoDetail.vue'
import Tasks from '@/portal/Tasks.vue'
import AdminAudit from '@/admin/AdminAudit.vue'
import AdminFinance from '@/admin/AdminFinance.vue'
import AdminMemberships from '@/admin/AdminMemberships.vue'
import AdminContentPosts from '@/admin/AdminContentPosts.vue'
import AdminContentEditor from '@/admin/AdminContentEditor.vue'
import * as adminText from '@/shared/adminText'
import { CLAIM_TYPE_TEXT, CLAIM_STATUS_TEXT, AUDIT_ACTOR_TEXT, AUDIT_RESULT_TEXT } from '@/shared/adminText'

const { http, adminHttp } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const ISO = '2026-11-13T20:30:45+08:00'
const ISO2 = '2026-11-12T08:05:00+08:00'
const NO_ISO = /\d{4}-\d{2}-\d{2}T\d{2}|\+08:00/

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
  if (!Range.prototype.getBoundingClientRect) {
    Range.prototype.getBoundingClientRect = () => ({ x: 0, y: 0, width: 0, height: 0, top: 0, left: 0, right: 0, bottom: 0 })
  }
  if (!Range.prototype.getClientRects) Range.prototype.getClientRects = () => ({ length: 0, item: () => null, [Symbol.iterator]: function* () {} })
  if (!document.elementFromPoint) document.elementFromPoint = () => null
})
beforeEach(() => {
  vi.clearAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  localStorage.setItem('ocap_admin_token', 'atok')
  document.body.innerHTML = ''
})
afterEach(() => { document.body.innerHTML = '' })

const cellsOf = (wrapper) => wrapper.findAll('tbody tr').map((r) => r.findAll('td').map((td) => td.text()))

describe('回流 2 另修的页面：中文与时间格式（REQ-FUNC-158）', () => {
  it('TC-UNIT-590 / AC-167-02、REQ-FUNC-158：InfoDetail 的发布时间为"年-月-日 时:分"，不含 T 与时区', async () => {
    globalThis.__routeId = '3'
    http.get.mockImplementation(routeTable({
      '/info/posts/3': { id: 3, title: '公告', published_at: ISO, pages: [{ html: '<p>正文</p>' }] }
    }))
    const { wrapper } = await mountPage(InfoDetail)
    await flush()
    expect(wrapper.text()).toContain('公告')
    expect(wrapper.text()).toContain('2026-11-13 20:30')
    expect(wrapper.text()).not.toMatch(NO_ISO)
    expect(wrapper.text()).not.toContain(':45')
  })

  it('TC-UNIT-591 / AC-167-03、REQ-FUNC-158：AdminAudit 的主体、结果列为中文，时间无 T 与时区；动作与对象保持原值（便于对照筛选）', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/audit-logs': { count: 3, results: [
        { id: 1, occurred_at: ISO, actor_type: 'MEMBER', action: 'INCOME_VOIDED', object_type: 'income_sheet', object_id: '9', result: 'SUCCESS' },
        { id: 2, occurred_at: ISO2, actor_type: 'ADMIN', action: 'USER_REVOKED', object_type: 'membership', object_id: '2', result: 'DENIED' },
        { id: 3, occurred_at: ISO2, actor_type: 'SYSTEM', action: 'JOB_RUN', object_type: 'job', object_id: '1', result: 'FAILURE' }] },
      '/admin/system-config/audit.retention_months': { value: 24 }
    }))
    // 分区同步：审计日志表在 /admin/audit/logs 二级页，传 section: 'logs'（原：与系统配置同页）
    const { wrapper } = await mountPage(AdminAudit, { props: { section: 'logs' } })
    await flush()
    const rows = cellsOf(wrapper)
    expect(rows).toHaveLength(3)
    const [t1, who1, action1, , , res1] = rows[0]
    expect(t1).toContain('2026-11-13 20:30')
    expect(t1).not.toMatch(NO_ISO)
    expect([who1, res1]).toEqual(['成员', '成功'])
    expect(action1).toBe('INCOME_VOIDED')
    expect([rows[1][1], rows[1][5]]).toEqual(['管理员', '拒绝'])
    expect([rows[2][1], rows[2][5]]).toEqual(['系统', '失败'])
    for (const r of rows) expect(r[0]).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/)
  })

  it('TC-UNIT-592 / AC-167-03、REQ-FUNC-158：AdminFinance 类型 3 种、状态 4 种全部显示中文，无英文代码', async () => {
    const types = ['REIMBURSEMENT', 'ADVANCE', 'SETTLEMENT']
    const statuses = ['PENDING', 'APPROVED', 'REJECTED', 'WITHDRAWN']
    const results = statuses.map((status, i) => ({ id: i + 1, type: types[i % 3], amount: '10.00', reason: `事由${i}`, status }))
    results.push({ id: 5, type: 'SETTLEMENT', amount: '1.00', reason: '核销', status: 'PENDING' })
    adminHttp.get.mockImplementation(routeTable({
      '/admin/claims': { count: results.length, results },
      '/admin/system-config': { 'audit.retention_months': 24, 'claim.amount_max': '1000000.00' }
    }))
    const { wrapper } = await mountPage(AdminFinance)
    await flush()
    const rows = cellsOf(wrapper)
    expect(rows).toHaveLength(5)
    const typeOf = (r) => r[1]
    const statusOf = (r) => r[4]
    expect(rows.map(typeOf)).toEqual(['报销', '备用金', '核销', '报销', '核销'])
    expect(rows.map(statusOf)).toEqual(['审批中', '已通过', '未通过', '已撤回', '审批中'])
    const table = wrapper.find('table').text()
    expect(table).not.toMatch(/REIMBURSEMENT|ADVANCE|SETTLEMENT|PENDING|APPROVED|REJECTED|WITHDRAWN/)
  })

  it('TC-UNIT-593 / AC-167-02、REQ-FUNC-158：AdminMemberships 认证时间为"年-月-日 时:分"；身份为中文', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/memberships': { count: 1, results: [
        { id: 1, user: { id: 7, nickname: '甲', account_no: '1' }, unit_id: 3, specific_part: 'A房', role: 'HEAD', certified_at: ISO }] }
    }))
    const { wrapper } = await mountPage(AdminMemberships)
    await flush()
    const [row] = cellsOf(wrapper)
    expect(row[10]).toBe('户主')
    expect(row[11]).toBe('2026-11-13 20:30')
    expect(wrapper.text()).not.toMatch(NO_ISO)
  })

  it('TC-UNIT-594 / AC-167-02、REQ-FUNC-158：AdminContentPosts 发布时间与更新时间为"年-月-日 时:分"，状态中文', async () => {
    adminHttp.get.mockImplementation(routeTable({
      '/admin/content/posts': { count: 1, results: [{ id: 5, title: '公告', status: 'PUBLISHED', published_at: ISO, updated_at: ISO2 }] }
    }))
    const wrapper = mount(AdminContentPosts, { global: { plugins: [ElementPlus], mocks: { $router: { push: vi.fn() } } }, attachTo: document.body })
    await flush()
    const [row] = cellsOf(wrapper)
    expect(row[1]).toBe('已发布')
    expect(row[2]).toBe('2026-11-13 20:30')
    expect(row[3]).toBe('2026-11-12 08:05')
    expect(wrapper.text()).not.toMatch(NO_ISO)
    wrapper.unmount()
  })

  it('TC-UNIT-595 / AC-167-02、REQ-FUNC-158：AdminContentEditor 的"保存历史"时间为"年-月-日 时:分"，结果中文', async () => {
    globalThis.__routeId = '7'
    adminHttp.get.mockImplementation(async (url) => {
      if (url === '/admin/content/posts/7') return { id: 7, title: '公告', doc: { type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: '正文' }] }] }, style_key: 'builtin:classic', media_urls: {}, text_confirmed: false }
      if (url === '/admin/content/style-templates') return [{ key: 'builtin:classic', name: '经典' }]
      if (url === '/admin/content/llm/options') return []
      if (url === '/admin/content/prompt-templates') return []
      if (url === '/admin/content/posts/7/drafts/history') {
        return { results: [{ id: 1, platform: 'wechat_mp', status: 'FAILED', operator: '管理员甲', created_at: ISO }] }
      }
      throw new Error(`未预期的 GET ${url}`)
    })
    const wrapper = mount(AdminContentEditor, { global: { plugins: [ElementPlus], mocks: { $router: { push: vi.fn() } } }, attachTo: document.body })
    await flush()
    const open = wrapper.findAll('button').find((b) => b.text().replace(/\s/g, '') === '保存历史')
    await open.trigger('click')
    await flush()
    const dialogText = document.body.querySelector('.el-dialog__body')?.textContent
    const histories = [...document.body.querySelectorAll('.el-dialog')].map((d) => d.textContent).filter((t) => t.includes('管理员甲'))
    expect(histories.length).toBeGreaterThan(0)
    const text = histories[0]
    expect(text).toContain('2026-11-13 20:30')
    expect(text).not.toMatch(NO_ISO)
    expect(text).not.toMatch(/FAILED/)
    expect(dialogText).toBeTypeOf('string')
    wrapper.unmount()
  })

  it('TC-UNIT-596 / REQ-FUNC-158：Tasks 标题回退——后端未给 subject_title 时标题显示中文类别而不是 EXPENSE', async () => {
    http.get.mockImplementation(routeTable({
      '/approval/tasks': { count: 2, results: [
        { instance_id: 1, scope: 'EXPENSE', submitted_at: ISO },
        { instance_id: 2, scope: 'INCOME', submitted_at: ISO2 }] }
    }))
    const { wrapper } = await mountPage(Tasks)
    await flush()
    const strongs = wrapper.findAll('strong').map((s) => s.text())
    expect(strongs).toEqual(['财务（报销/备用金）', '收入表'])
    expect(wrapper.text()).not.toMatch(/EXPENSE|INCOME\b|T20:30|\+08:00/)
  })
})

describe('GR-C-003 条件：shared/adminText.js 四张映射的守护', () => {
  // 解析后端模型 choices：形如 ("KEY", "文案") 的元组（来源：模型常量，非被测前端自己的输出）
  const choicesOf = (rel, name) => {
    const src = read(rel)
    const m = src.match(new RegExp(`${name}\\s*=\\s*\\[([\\s\\S]*?)\\]\\s*\\n`))
    expect(m, `${rel} 中找不到 ${name}`).toBeTruthy()
    return [...m[1].matchAll(/\(\s*"([A-Z_]+)"\s*,/g)].map((x) => x[1])
  }
  const sorted = (xs) => [...xs].sort()

  it('TC-UNIT-597 / REQ-FUNC-158、GR-C-003：adminText.js 恰好导出 4 张登记表；小程序 labels.js 不含；不混入 labels.js', () => {
    expect(Object.keys(adminText).sort()).toEqual(['AUDIT_ACTOR_TEXT', 'AUDIT_RESULT_TEXT', 'CLAIM_STATUS_TEXT', 'CLAIM_TYPE_TEXT'])
    const mini = read('miniprogram/utils/labels.js')
    const web = read('frontend/src/shared/labels.js')
    for (const name of Object.keys(adminText)) {
      expect(mini, name).not.toContain(name)
      expect(web, name).not.toContain(`export const ${name}`)
    }
  })

  it('TC-UNIT-598 / REQ-FUNC-158、GR-C-003：四张映射的键集合与后端模型枚举完全一致（不多不少）', () => {
    expect(sorted(Object.keys(CLAIM_TYPE_TEXT))).toEqual(sorted(choicesOf('backend/apps/claims/models.py', 'TYPES')))
    expect(sorted(Object.keys(CLAIM_STATUS_TEXT))).toEqual(sorted(choicesOf('backend/apps/claims/models.py', 'STATUSES')))
    expect(sorted(Object.keys(AUDIT_ACTOR_TEXT))).toEqual(sorted(choicesOf('backend/apps/core/models.py', 'ACTOR_TYPES')))
    expect(sorted(Object.keys(AUDIT_RESULT_TEXT))).toEqual(sorted(choicesOf('backend/apps/core/models.py', 'RESULTS')))
  })

  it('TC-UNIT-599 / REQ-FUNC-158、GR-C-003：四张映射的取值全部含中文，且不含 3 个以上连续大写字母', () => {
    for (const [name, table] of Object.entries(adminText)) {
      expect(Object.keys(table).length, name).toBeGreaterThan(0)
      for (const [k, v] of Object.entries(table)) {
        expect(v, `${name}.${k}`).toMatch(/[一-龥]/)
        expect(v, `${name}.${k}`).not.toMatch(/[A-Z]{3,}/)
      }
    }
  })

  it('TC-UNIT-600 / REQ-FUNC-158、GR-C-003：四张映射均被页面实际使用（AdminFinance 用 CLAIM_*，AdminAudit 用 AUDIT_*），不是死代码', () => {
    const fin = read('frontend/src/admin/AdminFinance.vue')
    const audit = read('frontend/src/admin/AdminAudit.vue')
    for (const n of ['CLAIM_TYPE_TEXT', 'CLAIM_STATUS_TEXT']) expect(fin, n).toMatch(new RegExp(`textOf\\(${n},`))
    for (const n of ['AUDIT_ACTOR_TEXT', 'AUDIT_RESULT_TEXT']) expect(audit, n).toMatch(new RegExp(`textOf\\(${n},`))
  })

  it('TC-UNIT-601 / ADR-092、GR-C-003-F01：登记范围守护——shared/ 下除 labels.js、adminText.js 外没有含中文取值的导出映射表；adminText.js 的表名不与 labels.js 重名', () => {
    // 评估结论（见 test_plan）：冻结用例 TC-UNIT-588 只读 labels.js，新映射放 adminText.js 不会触发它；
    // 本用例补上"新映射不在任何守护范围内"的漏检口：任何新的 Chinese-valued 导出表只允许出现在这两个登记文件中。
    const dir = path.join(ROOT, 'frontend/src/shared')
    const offenders = []
    for (const f of fs.readdirSync(dir).filter((n) => n.endsWith('.js'))) {
      if (f === 'labels.js' || f === 'adminText.js') continue
      const src = fs.readFileSync(path.join(dir, f), 'utf8')
      for (const m of src.matchAll(/export const (\w+)\s*=\s*\{([^}]*)\}/g)) {
        // 枚举映射表的特征：至少 2 项形如 `KEY: '中文'`（全大写键 → 中文值）；API 函数对象、弹窗文案表不是枚举映射
        const enumEntries = [...m[2].matchAll(/\b[A-Z][A-Z_]{2,}\s*:\s*['"][^'"]*[一-龥]/g)]
        if (enumEntries.length >= 2) offenders.push(`${f}:${m[1]}`)
      }
    }
    expect(offenders).toEqual([])
    const web = read('frontend/src/shared/labels.js')
    const inLabels = new Set([...web.matchAll(/export const (\w+)\s*=/g)].map((m) => m[1]))
    for (const name of Object.keys(adminText)) expect(inLabels.has(name), name).toBe(false)
  })
})
