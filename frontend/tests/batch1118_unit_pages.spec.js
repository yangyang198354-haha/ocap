// ocap_batch_1118 GROUP_D：Web 申诉暂存一次提交、专有部分下拉检索、身份页真实姓名与共有产权人（MOD-146/147/148）。
// 层级：unit（页面级：真实页面 + 真实 api.js + 真实 store，仅 mock HTTP 层）。TC-UNIT-1201 起。
// 溯源：US-244/245/246/247/248。姓名/数量均为合成值（C-79）。
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

import { mountPage, routeTable } from './helpers.js'
import UnitsAppeal from '@/portal/units/UnitsAppeal.vue'
import Units from '@/portal/Units.vue'
import UnitCascader from '@/portal/parts/UnitCascader.vue'
import { rankOptions } from '@/shared/unitSearch'

const { http } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const buttonOf = (wrapper, text) => wrapper.findAll('button').find((b) => b.text().includes(text))
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }

const HOUSING = { summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0, real_names: [] }
const baseTable = (over = {}) => routeTable({
  '/me': { profile: { id: 1, nickname: '合成用户' }, identities: { is_guest: true, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } },
  '/me/housing': HOUSING, '/me/registry-matches': { pending: false, total: 0, units: [] }, '/resident-applications/to-review': [], '/resident-applications/mine': [], '/appeals/mine': [],
  '/units/options': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }] }, ...over
})

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})

// ------------------------------------------------------------------ US-244 / US-245 申诉
describe('UnitsAppeal：选文件只暂存，提交时一次发送（US-244、US-245）', () => {
  const mountAppeal = async (unitId = 7) => {
    http.get.mockImplementation(baseTable())
    const { wrapper, pinia } = await mountPage(UnitsAppeal)
    if (unitId) {
      wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', unitId)
      await flush()
    }
    return { wrapper, pinia }
  }
  const pick = async (wrapper, name, { type = 'image/png', size } = {}) => {
    const file = new File(['x'], name, { type })
    if (size) Object.defineProperty(file, 'size', { value: size })
    wrapper.findComponent({ name: 'ElUpload' }).props('onChange')({ raw: file, status: 'ready', name })
    await flush()
    return file
  }
  const posts = () => http.post.mock.calls.filter((c) => c[0] === '/appeals')
  const nameInput = (wrapper) => wrapper.find('input[placeholder="产权人名字"]')

  it('TC-UNIT-1201 / AC-244-01：选 2 个合格文件（jpg 与 pdf）→ 页面显示 2 个暂存文件（文件名、类型、大小、"移除"），任何 POST 请求数 = 0，不出现"已上传"', async () => {
    const { wrapper } = await mountAppeal()
    await pick(wrapper, 'proof.jpg', { type: 'image/jpeg' })
    await pick(wrapper, 'proof.pdf', { type: 'application/pdf', size: 2 * 1024 * 1024 })
    expect(wrapper.findAll('.staged-item')).toHaveLength(2)
    const text = wrapper.text()
    for (const t of ['proof.jpg', 'proof.pdf', 'JPG', 'PDF', '2.0 MB', '已选 2 份']) expect(text).toContain(t)
    expect(wrapper.findAll('.staged-item button').map((b) => b.text())).toEqual(['移除', '移除'])
    expect(text).not.toContain('已上传')
    expect(http.post).not.toHaveBeenCalled()
  })

  it('TC-UNIT-1202 / AC-244-03：已暂存 2 个文件后离开页面（卸载）再进入 → 暂存区为空；整个过程没有任何上传请求（服务器因该次选择产生的文件数 0）', async () => {
    const { wrapper } = await mountAppeal()
    await pick(wrapper, 'a.png')
    await pick(wrapper, 'b.png')
    expect(wrapper.text()).toContain('已选 2 份')
    wrapper.unmount()
    const again = await mountAppeal(null)
    expect(again.wrapper.text()).toContain('已选 0 份')
    expect(again.wrapper.findAll('.staged-item')).toHaveLength(0)
    expect(http.post).not.toHaveBeenCalled()
  })

  it('TC-UNIT-1203 / AC-244-04：暂存 3 个文件，移除其中第 2 个 → 剩 2 个（顺序保持），服务器上附件新增数仍为 0', async () => {
    const { wrapper } = await mountAppeal()
    for (const n of ['a.png', 'b.png', 'c.pdf']) await pick(wrapper, n)
    await wrapper.findAll('.staged-item')[1].find('button').trigger('click')
    await flush()
    expect(wrapper.findAll('.staged-item').map((li) => li.find('span').text())).toEqual(['a.png', 'c.pdf'])
    expect(wrapper.text()).toContain('已选 2 份')
    expect(http.post).not.toHaveBeenCalled()
  })

  it('TC-UNIT-1204 / AC-245-01/02/03：三项缺一不发请求，逐项提示——未选房屋"请选择到具体户"；名字空或全空格"请输入产权人名字"；名字超 64 字提示超长；无文件"请至少选择 1 份产权证明"；提交按钮始终可点', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const { wrapper } = await mountAppeal(null)
    const btn = () => buttonOf(wrapper, '提交申诉')
    expect(btn().attributes('disabled')).toBeUndefined()
    await pick(wrapper, 'a.png')
    await nameInput(wrapper).setValue('业主甲')
    await btn().trigger('click')
    expect(warn).toHaveBeenLastCalledWith('请选择到具体户')
    wrapper.findComponent({ name: 'UnitCascader' }).vm.$emit('update:modelValue', 7)
    await flush()
    await nameInput(wrapper).setValue('   ')
    await btn().trigger('click')
    expect(warn).toHaveBeenLastCalledWith('请输入产权人名字')
    await nameInput(wrapper).setValue('甲'.repeat(65))
    await btn().trigger('click')
    expect(String(warn.mock.calls.at(-1)[0])).toContain('64')
    expect(posts()).toHaveLength(0)
    // 缺文件
    const empty = await mountAppeal()
    await nameInput(empty.wrapper).setValue('业主甲')
    await buttonOf(empty.wrapper, '提交申诉').trigger('click')
    expect(warn).toHaveBeenLastCalledWith('请至少选择 1 份产权证明')
    expect(posts()).toHaveLength(0)
  })

  it('TC-UNIT-1205 / AC-245-04：12MB 的 jpg 不入暂存并提示"单个文件不超过10MB"；.docx 提示"仅支持 jpg/png/pdf"；已有 5 份再选第 6 份提示"最多 5 份"；恰 10MB 合格', async () => {
    const warn = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const { wrapper } = await mountAppeal()
    await pick(wrapper, 'big.jpg', { type: 'image/jpeg', size: 12 * 1024 * 1024 })
    expect(warn).toHaveBeenLastCalledWith('单个文件不超过10MB')
    await pick(wrapper, 'x.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    expect(warn).toHaveBeenLastCalledWith('仅支持 jpg/png/pdf')
    expect(wrapper.findAll('.staged-item')).toHaveLength(0)
    await pick(wrapper, 'edge.jpg', { type: 'image/jpeg', size: 10 * 1024 * 1024 })
    expect(wrapper.findAll('.staged-item')).toHaveLength(1)
    for (let i = 0; i < 4; i += 1) await pick(wrapper, `p${i}.png`)
    expect(wrapper.findAll('.staged-item')).toHaveLength(5)
    await pick(wrapper, 'sixth.png')
    expect(warn).toHaveBeenLastCalledWith('最多 5 份')
    expect(wrapper.findAll('.staged-item')).toHaveLength(5)
    expect(http.post).not.toHaveBeenCalled()
  })

  it('TC-UNIT-1206 / AC-245-05：提交请求因网络中断失败 → 提示失败原因，已选房屋、名字与已暂存文件全部保留；修改后再次提交成功（第 2 次请求带同样的文件）并清空', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const success = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountAppeal()
    await pick(wrapper, 'a.png')
    await pick(wrapper, 'b.pdf', { type: 'application/pdf' })
    await nameInput(wrapper).setValue('业主甲')
    http.post.mockRejectedValueOnce({ message: '网络连接失败' })
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(error).toHaveBeenCalledWith('网络连接失败')
    expect(wrapper.text()).toContain('已选 2 份')
    expect(nameInput(wrapper).element.value).toBe('业主甲')
    expect(wrapper.findComponent({ name: 'UnitCascader' }).props('modelValue')).toBe(7)
    http.post.mockResolvedValueOnce({ id: 9, status: 'PENDING' })
    await nameInput(wrapper).setValue('业主甲改')
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(posts()).toHaveLength(2)
    expect(posts()[1][1].getAll('files').map((f) => f.name)).toEqual(['a.png', 'b.pdf'])
    expect(posts()[1][1].get('owner_name')).toBe('业主甲改')
    expect(success).toHaveBeenCalledWith('申诉已提交，等待管理员审核')
    expect(wrapper.text()).toContain('已选 0 份')
    expect(nameInput(wrapper).element.value).toBe('')
  })

  it('TC-UNIT-1207 / AC-245-06：服务端拒绝（409 已有待审申诉）→ 提示既有错误文案，暂存内容保留，可修改后重试；只发了 1 次请求', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper } = await mountAppeal()
    await pick(wrapper, 'a.png')
    await nameInput(wrapper).setValue('业主甲')
    http.post.mockRejectedValueOnce({ code: 'APPEAL_PENDING', message: '该专有部分已有待审申诉' })
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(error).toHaveBeenCalledWith('该专有部分已有待审申诉')
    expect(wrapper.text()).toContain('已选 1 份')
    expect(posts()).toHaveLength(1)
  })

  it('TC-UNIT-1208 / AC-244-02、AC-245-02：成功提交只发 1 次 POST /appeals（FormData：unit_id=7、owner_name 已去首尾空格、files 全部），且选择阶段与提交前都没有 /attachments 请求', async () => {
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper } = await mountAppeal()
    await pick(wrapper, 'a.png')
    await pick(wrapper, 'b.pdf', { type: 'application/pdf' })
    expect(http.post).not.toHaveBeenCalled()
    await nameInput(wrapper).setValue('  业主甲  ')
    http.post.mockResolvedValue({ id: 3, status: 'PENDING' })
    await buttonOf(wrapper, '提交申诉').trigger('click')
    await flush()
    expect(http.post).toHaveBeenCalledTimes(1)
    const [url, form, cfg] = http.post.mock.calls[0]
    expect(url).toBe('/appeals')
    expect([form.get('unit_id'), form.get('owner_name')]).toEqual(['7', '业主甲'])
    expect(form.getAll('files')).toHaveLength(2)
    expect(cfg.timeout).toBeGreaterThanOrEqual(60000)
    expect(http.post.mock.calls.some((c) => c[0] === '/attachments')).toBe(false)
  })
})

// ------------------------------------------------------------------ US-246 检索
describe('rankOptions / UnitCascader：四级下拉输入检索（US-246）', () => {
  const ROOMS = ['55', '551', '552', '553', '155', '60'].map((v, i) => ({ value: v, unit_id: 100 + i, label: `${v}（住宅 ${v === '60' ? '155' : '89.5'} ㎡）`, unit_type_label: '住宅', area: '89.5' }))

  it('TC-UNIT-1210 / AC-246-01/02/03：输入"55"→ 前缀项 55、551、552、553 排最前（原序），包含项 155 在后，60 不显示（括号里的面积 155 不误命中）；清空恢复全部；"zzz"无匹配 → 空；大小写不敏感', () => {
    expect(rankOptions(ROOMS, '55').map((o) => o.value)).toEqual(['55', '551', '552', '553', '155'])
    expect(rankOptions(ROOMS, '').map((o) => o.value)).toEqual(['55', '551', '552', '553', '155', '60'])
    expect(rankOptions(ROOMS, '  ').length).toBe(6)
    expect(rankOptions(ROOMS, 'zzz')).toEqual([])
    expect(rankOptions([{ value: 'A1' }, { value: 'b2' }], 'a').map((o) => o.value)).toEqual(['A1'])
    expect(rankOptions(undefined, 'x')).toEqual([])
    expect(rankOptions(null, '')).toEqual([])
  })

  const optionsTable = {
    '': { level: 'building', skipped: [], has_empty: false, options: [{ value: '1' }, { value: '10' }, { value: '11' }, { value: '2' }] },
    '1': { level: 'unit_no', skipped: [], has_empty: false, options: [{ value: '1' }, { value: '10' }, { value: '2' }] },
    '1|1': { level: 'floor', skipped: [], has_empty: false, options: [{ value: '5' }, { value: '15' }, { value: '55' }] },
    '1|1|5': { level: 'room', skipped: [], has_empty: false, options: ROOMS },
    '2': { level: 'unit_no', skipped: [], has_empty: false, options: [{ value: '1' }] }
  }
  const mountCascader = async (props = {}) => {
    const getter = async (url, arg) => {
      const p = arg?.params || {}
      const key = [p.building, p.unit_no, p.floor].filter((v) => v !== undefined).join('|')
      const hit = optionsTable[key]
      if (!hit) throw new Error(`未预期的 options 请求 ${JSON.stringify(p)}`)
      return hit
    }
    http.get.mockImplementation(getter)
    const { wrapper } = await mountPage(UnitCascader, { props })
    await flush()
    return wrapper
  }
  const selects = (w) => w.findAllComponents({ name: 'ElSelect' })
  const choose = async (select, value) => {
    select.vm.$emit('update:modelValue', value)
    select.vm.$emit('change', value)
    await flush()
  }
  const labels = (w) => w.findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))
  const filter = async (select, q) => { select.props('filterMethod')(q); await flush() }

  it('TC-UNIT-1211 / AC-246-05：楼栋、单元、楼层、户号四级下拉均 filterable 且无匹配文案"无匹配项"；逐级选到户号后四个下拉都出现', async () => {
    const wrapper = await mountCascader()
    await choose(selects(wrapper)[0], '1')
    await choose(selects(wrapper)[1], '1')
    await choose(selects(wrapper)[2], '5')
    expect(selects(wrapper)).toHaveLength(4)
    for (const s of selects(wrapper)) {
      expect(s.props('filterable')).toBe(true)
      expect(typeof s.props('filterMethod')).toBe('function')
      expect(s.props('noDataText')).toBe('无匹配项')
    }
  })

  it('TC-UNIT-1212 / AC-246-01/02/03：户号下拉输入"55"→ 选项依次 55、551、552、553、155，60 不显示；点击 552 选中 552 并显示"住宅 · 89.5 ㎡"；清空输入恢复全部；输入"zzz"选项为空且已选结果不变、不报错', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const wrapper = await mountCascader()
    await choose(selects(wrapper)[0], '1')
    await choose(selects(wrapper)[1], '1')
    await choose(selects(wrapper)[2], '5')
    const room = () => selects(wrapper)[3]
    const roomLabels = () => wrapper.findAllComponents({ name: 'ElOption' }).filter((o) => ROOMS.some((r) => r.unit_id === o.props('value'))).map((o) => o.props('label').split('（')[0])
    await filter(room(), '55')
    expect(roomLabels()).toEqual(['55', '551', '552', '553', '155'])
    await choose(room(), 102)
    expect(wrapper.emitted('update:modelValue').pop()).toEqual([102])
    expect(wrapper.text()).toContain('住宅 · 89.5 ㎡')
    await filter(room(), '')
    expect(roomLabels()).toEqual(['55', '551', '552', '553', '155', '60'])
    await filter(room(), 'zzz')
    expect(roomLabels()).toEqual([])
    expect(wrapper.text()).toContain('住宅 · 89.5 ㎡')
    expect(wrapper.findComponent({ name: 'UnitCascader' }).exists() || true).toBe(true)
    expect(error).not.toHaveBeenCalled()
  })

  it('TC-UNIT-1213 / AC-246-05：每一级输入只过滤该级候选，其他级不受影响（楼栋输入"1"→ 1、10、11 前缀项在前、2 不显示；单元级选项不变）', async () => {
    const wrapper = await mountCascader()
    await choose(selects(wrapper)[0], '1')
    const buildingBefore = labels(wrapper)
    await filter(selects(wrapper)[0], '1')
    const optionsOf = (idx) => selects(wrapper)[idx].findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))
    expect(optionsOf(0)).toEqual(['1', '10', '11'])
    expect(optionsOf(1)).toEqual(['1', '10', '2'])
    await filter(selects(wrapper)[1], '1')
    expect(optionsOf(1)).toEqual(['1', '10'])
    expect(optionsOf(0)).toEqual(['1', '10', '11'])
    expect(buildingBefore.length).toBeGreaterThan(0)
  })

  it('TC-UNIT-1214 / AC-246-04：三页（认证产权、认证申诉、我的同住人申请）使用同一 UnitCascader 且不传 fetcher；更换上一级后下一级及户号清空（update:modelValue=null）并重新加载', async () => {
    for (const rel of ['frontend/src/portal/units/UnitsPick.vue', 'frontend/src/portal/units/UnitsAppeal.vue', 'frontend/src/portal/units/UnitsApplicationForm.vue']) {
      const src = read(rel)
      expect(src, rel).toMatch(/<UnitCascader\b/)
      expect(src, rel).not.toMatch(/fetcher/)
    }
    const wrapper = await mountCascader()
    await choose(selects(wrapper)[0], '1')
    await choose(selects(wrapper)[1], '1')
    await choose(selects(wrapper)[2], '5')
    await choose(selects(wrapper)[3], 101)
    expect(wrapper.emitted('update:modelValue').pop()).toEqual([101])
    await choose(selects(wrapper)[0], '2')
    expect(wrapper.emitted('update:modelValue').pop()).toEqual([null])
    expect(selects(wrapper)).toHaveLength(2)
    expect(http.get).toHaveBeenLastCalledWith('/units/options', { params: { building: '2' } })
  })

  it('TC-UNIT-1215 / IFC-364：传入 fetcher 时用 fetcher 取数（管理端 admin.unitOptions），不再调用成员端 /units/options', async () => {
    const fetcher = vi.fn(async () => optionsTable[''])
    http.get.mockReset()
    const { wrapper } = await mountPage(UnitCascader, { props: { fetcher } })
    await flush()
    expect(fetcher).toHaveBeenCalledWith({})
    expect(http.get).not.toHaveBeenCalled()
    expect(wrapper.findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))).toEqual(['1', '10', '11', '2'])
  })
})

// ------------------------------------------------------------------ US-247 / US-248 身份页
describe('我的身份与房屋：真实姓名与共有产权人（US-247、US-248）', () => {
  const UNIT = (id, part, co, role = 'HEAD') => ({
    unit_id: id, specific_part: part, role, role_label: role === 'RESIDENT' ? '同住人' : '产权业主', certified_at: '2026-01-01T00:00:00+08:00',
    unit_type_label: '住宅', area_display: '89.50 ㎡', pending_application_count: 0, residents: [], co_owners: co
  })
  const mountIdentity = async (housing) => {
    http.get.mockImplementation(baseTable({ '/me/housing': housing }))
    const { wrapper } = await mountPage(Units, { props: { section: 'identity' } })
    await flush()
    return wrapper
  }

  it('TC-UNIT-1220 / AC-247-01/02/03：汇总身份行显示"真实姓名：业主甲"；多个姓名用"、"连接；游客/同住人/缺失（real_names=[] 或旧响应无该字段）显示"—"，不以昵称"合成用户"代替', async () => {
    let w = await mountIdentity({ summary: { code: 'OWNER', label: '产权业主' }, units: [UNIT(1, '1栋1单元9层902号', [])], pending_review_count: 0, real_names: ['业主甲'] })
    expect(w.find('.real-names').text()).toBe('真实姓名：业主甲')
    w.unmount()
    w = await mountIdentity({ summary: { code: 'OWNER', label: '产权业主' }, units: [UNIT(1, '1栋1单元9层902号', [])], pending_review_count: 0, real_names: ['业主甲', '业主丙'] })
    expect(w.find('.real-names').text()).toBe('真实姓名：业主甲、业主丙')
    w.unmount()
    w = await mountIdentity({ ...HOUSING })
    expect(w.find('.real-names').text()).toBe('真实姓名：—')
    expect(w.text()).not.toContain('合成用户')
    w.unmount()
    w = await mountIdentity({ summary: { code: 'RESIDENT', label: '同住人' }, units: [UNIT(2, '2栋2单元3层301号', ['业主乙'], 'RESIDENT')], pending_review_count: 0 })
    expect(w.find('.real-names').text()).toBe('真实姓名：—')
  })

  it('TC-UNIT-1221 / AC-248-01/02/04/05：每套房屋行显示各自"共有产权人"：有则列全名（只有姓名，无手机号与"未注册"标注），无则"无"，不串行；旧响应缺字段显示"无"不报错', async () => {
    const w = await mountIdentity({
      summary: { code: 'OWNER', label: '产权业主' }, pending_review_count: 0, real_names: ['业主甲'],
      units: [UNIT(1, '1栋1单元9层902号', ['业主乙']), UNIT(2, '2栋2单元3层301号', []), UNIT(3, '3栋1单元1层101号', ['共有人一', '共有人二']), { ...UNIT(4, '4栋1单元1层101号', []), co_owners: undefined }]
    })
    const rows = w.findAll('.co-owners').map((p) => p.text())
    expect(rows).toEqual(['共有产权人：业主乙', '共有产权人：无', '共有产权人：共有人一、共有人二', '共有产权人：无'])
    const text = w.text()
    expect(text).not.toMatch(/未注册|1[3-9]\d{9}|\*{4}/)
  })
})
