// ocap_batch_1118 GROUP_D：决议卡片（发起人/规则/截止/进行中·已结束、参与进度条）、参与人列表、整卡可点与动效样式、导航动效（MOD-149/150）。
// 层级：unit（页面/组件级 + 样式表静态解析，jsdom）。TC-UNIT-1301 起。溯源：US-249~253。
// 动效观感、三主题实际可见性与系统"减少动效"实际表现为人工验证项（jsdom 无渲染引擎），此处只验证 CSS 规则位置、时长上限与 JS 钩子行为。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus from 'element-plus'
import { createPinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, useRoute: actual.useRoute }
})

import { mountPage, routeTable } from './helpers.js'
import Resolutions from '@/portal/Resolutions.vue'
import ParticipantList from '@/portal/parts/ParticipantList.vue'
import Polls from '@/portal/Polls.vue'
import SideNav from '@/layout/SideNav.vue'
import { participationShare, voteShare } from '@/shared/voteShare'
import { PORTAL_MENU, visibleMenu } from '@/layout/menus'

const { http } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const ME = { profile: { id: 1, nickname: '合成用户' }, identities: { is_guest: false, units: [], labels: [], summary: { code: 'GUEST', label: '游客' }, committee: null } }

beforeAll(() => {
  if (!global.ResizeObserver) global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
})
beforeEach(() => {
  vi.clearAllMocks()
  for (const m of Object.values(http)) m.mockReset()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
})
afterEach(() => {
  vi.useRealTimers()
  delete globalThis.matchMedia
})

// ------------------------------------------------------------------ US-250 participationShare
describe('participationShare：参与进度数字（AC-250-01~04、AC-250-07、AC-259-05）', () => {
  const item = (counts, voted, expected) => ({ vote_counts: counts, participation: voted == null ? null : { voted, expected } })
  const approx = (a, b) => expect(a).toBeCloseTo(b, 1)

  it('TC-UNIT-1301 / AC-250-01：7 人应参与、已参与 4（同意 3、反对 1）→ 4 / 7 · 57%；着色 57%（同意≈43%、反对≈14%），留白≈43%', () => {
    const s = participationShare(item({ agree: 3, disagree: 1, abstain: 0 }, 4, 7))
    expect([s.voted, s.expected, s.pct, s.empty]).toEqual([4, 7, 57, false])
    approx(s.agreePct, 42.86)
    approx(s.disagreePct, 14.29)
    approx(s.abstainPct, 0)
    approx(100 - (s.agreePct + s.disagreePct + s.abstainPct), 42.86)
  })

  it('TC-UNIT-1302 / AC-250-02/03：全部 7 人参与 → 100%、条无留白；无人参与 → 0 / 7 · 0%、条全留白，无 NaN', () => {
    const full = participationShare(item({ agree: 5, disagree: 1, abstain: 1 }, 7, 7))
    expect([full.pct, full.voted, full.expected]).toEqual([100, 7, 7])
    approx(full.agreePct + full.disagreePct + full.abstainPct, 100)
    const none = participationShare(item({ agree: 0, disagree: 0, abstain: 0 }, 0, 7))
    expect([none.pct, none.voted, none.expected, none.empty]).toEqual([0, 0, 7, false])
    expect(JSON.stringify(none)).not.toMatch(/NaN|null/)
  })

  it('TC-UNIT-1303 / AC-250-04：应参与人数为 0 → empty=true（不画条，显示"暂无表决人"），无 NaN；无 participation（旧响应）同样 empty', () => {
    const zero = participationShare(item({ agree: 0, disagree: 0, abstain: 0 }, 0, 0))
    expect(zero.empty).toBe(true)
    expect(zero.pct).toBe(0)
    expect(JSON.stringify(zero)).not.toMatch(/NaN/)
    expect(participationShare(item({ agree: 1, disagree: 0, abstain: 0 }, null)).empty).toBe(true)
  })

  it('TC-UNIT-1304 / AC-250-07、AC-259-05：在任席位 7（含 1 待绑定），6 位可投票者均已表决（同意 4、反对 1、弃权 1）→ 6 / 7 · 86%（不是 100%），着色：同意≈57%、反对≈14%、弃权≈14%，留白≈14%', () => {
    const s = participationShare(item({ agree: 4, disagree: 1, abstain: 1 }, 6, 7))
    expect([s.voted, s.expected, s.pct]).toEqual([6, 7, 86])
    approx(s.agreePct, 57.14)
    approx(s.disagreePct, 14.29)
    approx(s.abstainPct, 14.29)
    approx(100 - (s.agreePct + s.disagreePct + s.abstainPct), 14.29)
  })

  it('TC-UNIT-1305 / REQ-NFUNC-050：既有 voteShare 导出与返回结构不变（Home.vue 在用）', () => {
    const s = voteShare({ agree: 5, disagree: 1, abstain: 4 })
    expect([s.total, s.agreePct, s.disagreePct, s.abstainPct]).toEqual([10, 50, 10, 40])
    expect(Object.keys(s).sort()).toEqual(['abstain', 'abstainPct', 'agree', 'agreePct', 'disagree', 'disagreePct', 'total'])
  })
})

// ------------------------------------------------------------------ US-249 / US-250 / US-252 卡片
describe('Resolutions 卡片：发起人、规则、截止、状态、进度条、整卡可点（US-249、US-250、US-252）', () => {
  const ROW = (over) => ({ id: 1, title: '合成决议', status: 'PENDING', approval_mode: 'HALF_MAJORITY', vote_deadline: '2026-12-01T18:00:00+08:00',
    initiator: { id: 2, labels: ['主任'], display_name: '发起人甲' }, vote_counts: { agree: 3, disagree: 1, abstain: 0 }, participation: { voted: 4, expected: 7 }, ...over })
  const mountList = async (rows, section = 'public') => {
    http.get.mockImplementation(routeTable({ '/me': ME, '/resolutions': { results: rows, count: rows.length }, '/approval/flows': { results: [] } }))
    const { wrapper } = await mountPage(Resolutions, { props: { section } })
    await flush()
    return wrapper
  }

  it('TC-UNIT-1310 / AC-249-01/02：已结束半数以上参与者同意卡片显示"发起人：发起人甲 · 主任"、规则"半数以上参与者同意"、"截止 2026-12-01 18:00"、"已结束"并保留"通过"结果标签（UI 既有文案为"通过/未通过"）；指定负责人无截止时间显示"指定负责人""无截止时间"，没有"截止"空白', async () => {
    const w = await mountList([
      ROW({ id: 1, status: 'APPROVED' }),
      ROW({ id: 2, status: 'APPROVED', approval_mode: 'DESIGNATED', vote_deadline: null, vote_counts: undefined, participation: null })
    ])
    const [a, b] = w.findAll('.res-card')
    for (const t of ['发起人：发起人甲 · 主任', '半数以上参与者同意', '截止 2026-12-01 18:00', '已结束', '通过']) expect(a.text(), t).toContain(t)
    expect(a.text()).not.toContain('未通过')
    expect(a.text()).not.toContain('进行中')
    expect(b.text()).toContain('指定负责人')
    expect(b.text()).toContain('无截止时间')
    expect(b.text()).not.toMatch(/截止\s*$|截止 undefined|截止 null/)
    expect(b.text()).toContain('由指定负责人审批')
    expect(b.find('.vote-bar').exists()).toBe(false)
  })

  it('TC-UNIT-1311 / AC-249-03：昵称为空时接口给账号编号作 display_name，卡片显示账号编号与身份，不是空白也不是单独的"发起人"', async () => {
    const w = await mountList([ROW({ initiator: { id: 2, labels: ['委员'], display_name: '8000000123' } })])
    expect(w.find('.res-initiator').text()).toContain('发起人：8000000123 · 委员')
  })

  it('TC-UNIT-1312 / AC-249-04：进行中的半数同意决议标"进行中"，不显示"已通过/未通过"标签', async () => {
    const w = await mountList([ROW({ status: 'PENDING' })])
    const t = w.find('.res-card').text()
    expect(t).toContain('进行中')
    expect(t).not.toMatch(/已通过|未通过|已结束/)
  })

  it('TC-UNIT-1313 / AC-250-01/03/04/05/06：卡片进度条文案——"已参与 4 / 7 · 57%"；无人参与"已参与 0 / 7 · 0%"；应参与 0 "暂无表决人"且不画条；指定负责人"由指定负责人审批"；无障碍标签含"已参与 4 / 7，同意 3，反对 1，弃权 0"', async () => {
    const w = await mountList([
      ROW({ id: 1 }),
      ROW({ id: 2, vote_counts: { agree: 0, disagree: 0, abstain: 0 }, participation: { voted: 0, expected: 7 } }),
      ROW({ id: 3, vote_counts: { agree: 0, disagree: 0, abstain: 0 }, participation: { voted: 0, expected: 0 } }),
      ROW({ id: 4, approval_mode: 'DESIGNATED', vote_counts: undefined, participation: null })
    ])
    const [c1, c2, c3, c4] = w.findAll('.res-card')
    expect(c1.find('.res-participation').text()).toBe('已参与 4 / 7 · 57%')
    const widths = c1.findAll('.vote-bar i').map((i) => i.attributes('style'))
    expect(widths[0]).toContain('42.857')
    expect(widths[1]).toContain('14.285')
    expect(c1.find('.vote-bar').attributes('role')).toBe('img')
    expect(c1.find('.vote-bar').attributes('aria-label')).toBe('已参与 4 / 7，同意 3，反对 1，弃权 0')
    expect(c2.find('.res-participation').text()).toBe('已参与 0 / 7 · 0%')
    expect(c2.text()).not.toContain('NaN')
    expect(c3.text()).toContain('暂无表决人')
    expect(c3.find('.vote-bar').exists()).toBe(false)
    expect(c4.text()).toContain('由指定负责人审批')
  })

  it('TC-UNIT-1314 / AC-249-05、AC-252-01：公开决议、我发起的、待我表决三个路由使用同一页面组件；卡片标题是指向 /resolutions/{id} 的链接，CSS 把它拉伸为整卡点击区', async () => {
    const router = read('frontend/src/router/index.js')
    expect(router).toMatch(/path: 'resolutions', component: ResolutionsPage, props: \{ section: 'public' \}/)
    expect(router).toMatch(/path: 'resolutions\/mine', component: ResolutionsPage, props: \{ section: 'mine' \}/)
    expect(router).toMatch(/path: 'resolutions\/todo', component: ResolutionsPage, props: \{ section: 'todo' \}/)
    for (const section of ['public', 'mine', 'todo']) {
      document.body.innerHTML = ''
      const w = await mountList([ROW({ id: 31 })], section)
      expect(w.find('.res-card a.res-title').attributes('href')).toBe('/resolutions/31')
      for (const t of ['发起人：发起人甲', '半数以上参与者同意', '截止', '进行中']) expect(w.find('.res-card').text(), `${section} ${t}`).toContain(t)
    }
    const css = read('frontend/src/shared/style.css')
    expect(css).toMatch(/\.res-title::after,\s*\.poll-link::after\s*\{[^}]*position:\s*absolute;[^}]*inset:\s*0/)
    expect(css).toMatch(/\.res-card,\s*\.poll-item\s*\{\s*position:\s*relative;\s*\}/)
  })

  it('TC-UNIT-1315 / AC-252-03、AC-252-04：卡片内其他链接/按钮提升到拉伸层之上（z-index:1）不触发整卡跳转；卡片 :focus-within 有可见焦点样式；链接是原生 <a>（Tab 聚焦 + Enter 进入）', () => {
    const css = read('frontend/src/shared/style.css')
    expect(css).toMatch(/\.res-card a:not\(\.res-title\),\s*\.res-card button,[^{]*\{\s*position:\s*relative;\s*z-index:\s*1;\s*\}/)
    expect(css).toMatch(/\.res-card:focus-within,\s*\.poll-item:focus-within\s*\{\s*outline:\s*2px solid var\(--accent\)/)
    expect(read('frontend/src/portal/Resolutions.vue')).toMatch(/<router-link class="res-title"/)
  })

  it('TC-UNIT-1316 / AC-252-06：投票/调查页每项含指向 /polls/{id} 的 .poll-link，CSS 同样整卡拉伸', async () => {
    http.get.mockImplementation(routeTable({
      '/me': ME, '/polls': { count: 1, results: [{ id: 5, title: '合成调查', kind: 'SURVEY', status: 'OPEN', deadline: '2026-12-01T18:00:00+08:00' }] },
      '/system/limits': { poll_max_questions: 20 }
    }))
    const { wrapper } = await mountPage(Polls)
    await flush()
    expect(wrapper.find('.poll-item a.poll-link').attributes('href')).toBe('/polls/5')
  })
})

// ------------------------------------------------------------------ US-251 参与人列表
describe('ParticipantList：参与人（US-251）', () => {
  const mountList = (props) => mount(ParticipantList, { props, global: { plugins: [createPinia(), ElementPlus] } })

  it('TC-UNIT-1320 / AC-251-01/02：3 人参与 → "已参与 3 人"与 3 行（昵称+参与时间；无头像显示默认头像占位）；页面文本不含投票选项、手机号', () => {
    const w = mountList({ mode: 'HALF_MAJORITY', items: [
      { display_name: '委员甲', avatar_url: '/api/v1/attachments/00000000-0000-0000-0000-000000000001/download', voted_at: '2026-11-18T09:00:00+08:00' },
      { display_name: '委员乙', avatar_url: null, voted_at: '2026-11-18T10:00:00+08:00' },
      { display_name: '委员丙', avatar_url: null, voted_at: '2026-11-18T11:00:00+08:00' }
    ] })
    expect(w.find('.participant-count').text()).toBe('已参与 3 人')
    const rows = w.findAll('.participant-item')
    expect(rows).toHaveLength(3)
    expect(rows.map((r) => r.find('.participant-name').text())).toEqual(['委员甲', '委员乙', '委员丙'])
    expect(rows[0].findComponent({ name: 'AuthImage' }).exists()).toBe(true)
    expect(rows[1].find('.participant-avatar-default').exists()).toBe(true)
    expect(rows[2].find('.participant-avatar-default').text()).toBe('委')
    expect(w.text()).not.toMatch(/同意|反对|弃权|AGREE|1[3-9]\d{9}/)
  })

  it('TC-UNIT-1321 / AC-251-03/04：无人参与显示"暂无人参与"；指定负责人显示"无表决参与人"且不显示列表与"已参与"', () => {
    const empty = mountList({ mode: 'HALF_MAJORITY', items: [] })
    expect(empty.text()).toContain('已参与 0 人')
    expect(empty.text()).toContain('暂无人参与')
    expect(empty.find('.participant-items').exists()).toBe(false)
    const des = mountList({ mode: 'DESIGNATED', items: [] })
    expect(des.text()).toContain('无表决参与人')
    expect(des.text()).not.toContain('已参与')
    expect(des.find('.participant-items').exists()).toBe(false)
  })
})

describe('ResolutionDetail：参与人加载（US-251）', () => {
  it('TC-UNIT-1322 / AC-251-01/03/04、AC-249-04：半数同意详情调用 participants 并显示列表；参与人接口失败降级为"暂无人参与"（详情仍显示）；指定负责人不请求参与人接口，显示"无表决参与人"', async () => {
    vi.resetModules()
    const { default: ResolutionDetail } = await import('@/portal/ResolutionDetail.vue')
    const detail = (over) => ({ id: 7, title: '合成决议', content: '正文', status: 'PENDING', approval_mode: 'HALF_MAJORITY', vote_deadline: '2026-12-01T18:00:00+08:00',
      initiator: { id: 2, labels: ['主任'], display_name: '发起人甲' }, attachments: [], vote_counts: { agree: 1, disagree: 1, abstain: 0 }, participation: { voted: 2, expected: 5 }, ...over })
    const mountDetail = async () => {
      const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/resolutions/:id', component: ResolutionDetail }] })
      router.push('/resolutions/7')
      await router.isReady()
      const w = mount(ResolutionDetail, { global: { plugins: [createPinia(), router, ElementPlus] }, attachTo: document.body })
      await flush()
      return w
    }
    http.get.mockImplementation(routeTable({
      '/me': ME, '/resolutions/7': detail(),
      '/resolutions/7/participants': { mode: 'HALF_MAJORITY', count: 2, results: [
        { display_name: '委员甲', avatar_url: null, voted_at: '2026-11-18T09:00:00+08:00' }, { display_name: '委员乙', avatar_url: null, voted_at: '2026-11-18T10:00:00+08:00' }] }
    }))
    let w = await mountDetail()
    expect(w.text()).toContain('已参与 2 人')
    expect(w.text()).toContain('委员甲')
    expect(w.text()).toContain('已参与 2 / 5')
    expect(w.text()).not.toContain('决议不存在或无权查看')
    expect(http.get.mock.calls.some((c) => c[0] === '/resolutions/7/participants')).toBe(true)
    w.unmount()
    http.get.mockImplementation(async (url) => {
      if (url === '/me') return ME
      if (url === '/resolutions/7') return detail()
      throw { message: '服务异常' }
    })
    w = await mountDetail()
    expect(w.text()).toContain('暂无人参与')
    expect(w.text()).toContain('合成决议')
    w.unmount()
    http.get.mockReset()
    http.get.mockImplementation(routeTable({ '/me': ME, '/resolutions/7': detail({ approval_mode: 'DESIGNATED', vote_counts: undefined, participation: null, status: 'APPROVED' }) }))
    w = await mountDetail()
    expect(w.text()).toContain('无表决参与人')
    expect(http.get.mock.calls.some((c) => c[0] === '/resolutions/7/participants')).toBe(false)
  })
})

// ------------------------------------------------------------------ 动效样式（静态解析，AC-252-02/05、AC-253-01~04/06、NFUNC-047）
describe('style.css 动效规则：位置、时长、主题无关（US-252、US-253）', () => {
  const css = read('frontend/src/shared/style.css')
  const motionBlock = css.slice(css.indexOf('@media (prefers-reduced-motion: no-preference)'))
  const outside = css.replace(motionBlock, '')

  it('TC-UNIT-1330 / AC-252-05、AC-253-04：所有 transition/animation/@keyframes 与卡片悬停位移都在 prefers-reduced-motion: no-preference 块内（"减少动效"下新增动画数 0）', () => {
    expect(css.match(/@media \(prefers-reduced-motion: no-preference\)/g)).toHaveLength(1)
    // 块外不得出现本批新增的动效声明（卡片/导航相关选择器）
    expect(outside).not.toMatch(/\.res-card[^{]*\{[^}]*transition/)
    expect(outside).not.toMatch(/side-sub-item[^{]*\{[^}]*(transition|animation)/)
    expect(outside).not.toMatch(/@keyframes side-sub-in/)
    expect(outside).not.toMatch(/\.res-card:hover[^{]*\{[^}]*transform/)
    expect(motionBlock).toMatch(/\.res-card:hover, \.poll-item:hover \{ transform: translateY\(-3px\); box-shadow: var\(--shadow\); \}/)
    expect(motionBlock).toMatch(/\.res-card:active, \.poll-item:active \{ transform: scale\(\.985\); \}/)
  })

  it('TC-UNIT-1331 / AC-252-02、NFUNC-047：新增 transition/animation 单次时长均 ≤ 400ms，总错峰延迟 ≤ 360ms；JS 高度动画 ≤ 400ms', () => {
    const times = [...motionBlock.matchAll(/(?:transition|animation):[^;}]*?(?<![\d.])(\d*\.?\d+)(ms|s)\b/g)].map((m) => (m[2] === 's' ? Number(m[1]) * 1000 : Number(m[1])))
    expect(times.length).toBeGreaterThanOrEqual(4)
    for (const t of times) expect(t).toBeLessThanOrEqual(400)
    const delay = motionBlock.match(/animation-delay:\s*calc\(var\(--i, 0\) \* (\d+)ms\)/)
    expect(Number(delay[1]) * 5 + 160).toBeLessThanOrEqual(400)
    const nav = read('frontend/src/layout/SideNav.vue')
    expect(Number(nav.match(/height (\d+)ms ease/)[1])).toBeLessThanOrEqual(400)
  })

  it('TC-UNIT-1332 / AC-253-02/03/06：选中强调与展开动效只使用主题变量（var(--accent) 等），无颜色字面量；二级项（宽屏侧栏 .side-sub-item 与窄屏切换条 .sub-nav-item）使用同类 .is-active 指示条', () => {
    expect(motionBlock).not.toMatch(/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/)
    expect(motionBlock).toMatch(/\.side-sub-item\.is-active::after,\s*\.sub-nav-item\.is-active::after\s*\{\s*transform:\s*scaleY\(1\);\s*\}/)
    expect(motionBlock).toMatch(/background:\s*var\(--accent\)/)
    expect(read('frontend/src/layout/SubNavBar.vue')).toMatch(/class="sub-nav-item"/)
    expect(read('frontend/src/layout/SubNavBar.vue')).toMatch(/is-active/)
    expect(motionBlock).not.toMatch(/::before/)
  })
})

// ------------------------------------------------------------------ SideNav 展开动效（US-253）
describe('SideNav：二级菜单展开/收起过渡与降级（US-253）', () => {
  const MENU = visibleMenu(PORTAL_MENU, { isCommittee: true })
  const mountNav = async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: { template: '<div />' } }] })
    router.push('/')
    await router.isReady()
    const w = mount(SideNav, { props: { menu: MENU }, global: { plugins: [router], stubs: { transition: false } }, attachTo: document.body })
    await flushPromises()
    return { w, router }
  }
  const toggleOf = (w, label) => w.findAll('.side-group-toggle').find((b) => b.text().includes(label))
  const defineHeight = (h) => Object.defineProperty(HTMLElement.prototype, 'scrollHeight', { configurable: true, get: () => h })
  const resetHeight = () => { delete HTMLElement.prototype.scrollHeight }

  it('TC-UNIT-1340 / AC-253-01：点击一级项"我的房屋"→ 立即展开二级项（aria-expanded=true）；二级 ul 带高度过渡（0 → 实际高度，内联 height 过渡 280ms，≤400ms），结束后清理内联样式；再次点击收起同样有过渡', async () => {
    vi.useFakeTimers()
    defineHeight(120)
    try {
      const { w } = await mountNav()
      await toggleOf(w, '我的房屋').trigger('click')
      expect(toggleOf(w, '我的房屋').attributes('aria-expanded')).toBe('true')
      const ul = w.find('#side-sub-units')
      expect(ul.exists()).toBe(true)
      expect(ul.attributes('style')).toContain('height: 120px')
      expect(ul.element.style.height).toBe('120px')
      expect(ul.element.style.overflow).toBe('hidden')
      await vi.advanceTimersByTimeAsync(300)
      expect(ul.element.style.height).toBe('')
      // 收起：先过渡到 0，结束后移除
      await toggleOf(w, '我的房屋').trigger('click')
      expect(toggleOf(w, '我的房屋').attributes('aria-expanded')).toBe('false')
      const leaving = w.find('#side-sub-units')
      if (leaving.exists()) expect(leaving.element.style.height).toBe('0px')
      await vi.advanceTimersByTimeAsync(300)
      await flushPromises()
      expect(w.find('#side-sub-units').exists()).toBe(false)
    } finally {
      resetHeight()
    }
  })

  it('TC-UNIT-1341 / AC-253-04：系统"减少动效"开启（matchMedia reduce 命中）→ 展开/收起无高度动画（不设 transition/height 内联样式），功能照常（aria-expanded 与 DOM 存在性变化）', async () => {
    defineHeight(120)
    globalThis.matchMedia = vi.fn(() => ({ matches: true }))
    try {
      const { w } = await mountNav()
      await toggleOf(w, '我的房屋').trigger('click')
      const ul = w.find('#side-sub-units')
      expect(ul.exists()).toBe(true)
      expect(ul.element.style.transition).toBe('')
      expect(ul.element.style.height).toBe('')
      expect(globalThis.matchMedia).toHaveBeenCalledWith('(prefers-reduced-motion: reduce)')
      await toggleOf(w, '我的房屋').trigger('click')
      await flushPromises()
      expect(w.find('#side-sub-units').exists()).toBe(false)
    } finally {
      resetHeight()
    }
  })

  it('TC-UNIT-1342 / AC-253-02、AC-253-05：同时至多展开一个；选中二级项仅 1 个带 is-active 且 aria-current；二级项带错峰序号 --i；Esc 收起并把焦点还给一级按钮（既有行为不变）', async () => {
    const { w, router } = await mountNav()
    await toggleOf(w, '我的房屋').trigger('click')
    await toggleOf(w, '决议').trigger('click')
    expect(w.findAll('.side-sub')).toHaveLength(1)
    expect(toggleOf(w, '我的房屋').attributes('aria-expanded')).toBe('false')
    await router.push('/resolutions/mine')
    await flushPromises()
    const active = w.findAll('.side-sub-item.is-active')
    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('我发起的')
    expect(active[0].attributes('aria-current')).toBe('page')
    expect(w.findAll('.side-sub li').map((li) => li.attributes('style'))).toEqual(['--i: 0;', '--i: 1;', '--i: 2;'])
    await router.push('/resolutions/todo')
    await flushPromises()
    expect(w.findAll('.side-sub-item.is-active')).toHaveLength(1)
    expect(w.find('.side-sub-item.is-active').text()).toContain('待我表决')
    await w.find('.side-sub').trigger('keydown', { key: 'Escape' })
    await flushPromises()
    expect(w.find('.side-sub').exists()).toBe(false)
    expect(document.activeElement?.getAttribute('aria-controls')).toBe('side-sub-resolutions')
  })
})
