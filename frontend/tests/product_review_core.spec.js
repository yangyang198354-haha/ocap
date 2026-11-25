// ocap_product_review MOD-082/083 自验证：中文映射、确认封装（取消不发请求）、翻页组合函数、入口可见性、待审批提示
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

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
import { confirmDanger, CONFIRM_TEXTS } from '@/shared/confirm'
import { statusLabel, yesNo, ROLE_LABELS, IDENTITY_LABELS } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'
import Home from '@/portal/Home.vue'
import Claims from '@/portal/Claims.vue'
import InfoDetail from '@/portal/InfoDetail.vue'

const { http } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')

const me = (position, units = [], summary = { code: 'GUEST', label: '游客' }) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: {
    is_guest: !units.length, units, labels: [], summary,
    committee: position ? { position, term_end: '2027-01-01' } : null
  }
})

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

describe('labels / confirm / usePaging', () => {
  it('TC-UNIT-560 / AC-167-01~03：中文映射：状态、角色、布尔值', () => {
    expect(statusLabel('application', 'CLOSED')).toBe('已关闭（申请人已注销）')
    expect(statusLabel('appeal', 'REJECTED')).toBe('已驳回')
    expect(statusLabel('poll', 'OPEN')).toBe('进行中')
    expect(statusLabel('account', 'DISABLED')).toBe('停用')
    expect(ROLE_LABELS.HEAD).toBe('户主')
    expect(IDENTITY_LABELS.GUEST).toBe('游客')
    expect(yesNo(true)).toBe('是')
    expect(yesNo(false)).toBe('否')
    expect(yesNo(null)).toBe('')
  })

  it('TC-UNIT-561 / AC-167-01~03：键集合与小程序 labels.js 一致（ADR-092）', () => {
    const mini = fs.readFileSync(path.join(ROOT, 'miniprogram/utils/labels.js'), 'utf8')
    const web = fs.readFileSync(path.join(ROOT, 'frontend/src/shared/labels.js'), 'utf8')
    const keys = (src) => [...src.matchAll(/export const (\w+_LABELS)\s*=/g)].map((m) => m[1]).sort()
    expect(keys(mini)).toEqual(keys(web))
    for (const name of keys(web)) {
      const pick = (src) => src.split(`export const ${name} =`)[1].split('\nexport')[0].replace(/\s+/g, '')
      expect(pick(mini), name).toBe(pick(web))
    }
  })

  it('TC-UNIT-562 / AC-158-03、AC-158-04：confirmDanger：确认 → true，取消/关闭 → false；注销列出 4 项后果', async () => {
    messageBox.confirm.mockResolvedValueOnce('confirm')
    expect(await confirmDanger('removeResident', { name: '李四' })).toBe(true)
    messageBox.confirm.mockRejectedValueOnce('cancel')
    expect(await confirmDanger('cancelAccount')).toBe(false)
    expect(CONFIRM_TEXTS.cancelAccount.consequences).toHaveLength(4)
    await expect(confirmDanger('nope')).rejects.toThrow()
  })

  it('TC-UNIT-563 / AC-160-02、AC-161-02：usePaging：数组与分页对象两种返回；翻页保持筛选条件', async () => {
    const fetch = vi.fn(async (params) => ({ count: 45, results: [{ id: params.page }] }))
    const filters = ref({ q: 'abc' })
    const paging = usePaging({ fetch, filters })
    await paging.resetAndLoad()
    expect(paging.total.value).toBe(45)
    await paging.goto(3)
    expect(fetch).toHaveBeenLastCalledWith({ q: 'abc', page: 3, page_size: 20 })
    const arr = usePaging({ fetch: async () => [{ id: 1 }, { id: 2 }] })
    await arr.reload()
    expect(arr.total.value).toBe(2)
  })
})

describe('入口可见性与待审批提示', () => {
  it('TC-UNIT-564 / AC-154-04：非成员：Claims 页无“新建申请”', async () => {
    http.get.mockImplementation(routeTable({
      '/me': me(null), '/claims': { count: 0, results: [] }, '/approval/flows': { results: [] },
      '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Claims)
    expect(wrapper.findAll('button').some((b) => b.text().includes('新建申请'))).toBe(false)
  })

  it('TC-UNIT-565 / AC-154-04：成员：Claims 页有“新建申请”', async () => {
    http.get.mockImplementation(routeTable({
      '/me': me('MEMBER'), '/claims': { count: 0, results: [] }, '/approval/flows': { results: [] },
      '/system/limits': { claim_amount_max: '1000000.00' }
    }))
    const { wrapper } = await mountPage(Claims)
    expect(wrapper.findAll('button').some((b) => b.text().includes('新建申请'))).toBe(true)
  })

  it('TC-UNIT-566 / AC-151-01、AC-151-04、AC-166-03：产权业主首页显示“待我处理 · 2”；非成员不请求待办；无待审时不显示', async () => {
    const owner = me(null, [{ unit_id: 1, specific_part: 'A', role: 'OWNER' }], { code: 'OWNER', label: '产权业主' })
    http.get.mockImplementation(routeTable({
      '/me': owner, '/resolutions': { results: [] }, '/polls': { results: [] },
      '/me/housing': { pending_review_count: 2, units: [], summary: { code: 'OWNER', label: '产权业主' } }
    }))
    let { wrapper } = await mountPage(Home)
    expect(wrapper.text()).toContain('待我处理 · 2')
    expect(wrapper.text()).toContain('当前身份：产权业主')
    expect(http.get.mock.calls.some((c) => c[0] === '/approval/tasks')).toBe(false)
    document.body.innerHTML = ''
    http.get.mockImplementation(routeTable({
      '/me': owner, '/resolutions': { results: [] }, '/polls': { results: [] },
      '/me/housing': { pending_review_count: 0, units: [] }
    }))
    ;({ wrapper } = await mountPage(Home))
    expect(wrapper.text()).not.toContain('待我处理')
  })

  it('TC-UNIT-567 / AC-169-01、AC-169-02：InfoDetail：请求失败显示“内容不存在或已下线”与返回列表', async () => {
    http.get.mockRejectedValue(Object.assign(new Error('x'), { code: 'NOT_FOUND' }))
    const { wrapper } = await mountPage(InfoDetail)
    await flushPromises()
    expect(wrapper.text()).toContain('内容不存在或已下线')
    expect(wrapper.text()).toContain('返回列表')
  })
})
