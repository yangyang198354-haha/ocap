// PHASE_07 单元测试（ocap_ui_theme / 小程序）：单模块规则，uni 为桩（不代表微信真机行为）
// 溯源：AC-074-01/03、AC-077-01、AC-079-04、AC-083-02、AC-086-01、AC-087-03、AC-089-01
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { THEMES, DEFAULT_THEME } from '@/theme/generated/registry'
import { THEMES as WEB_THEMES } from '../../frontend/src/theme/generated/registry.js'
import { useThemeStore } from '@/store/theme'
import StatusTag from '../components/StatusTag.vue'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const pagesJson = () => JSON.parse(read('pages.json'))
const bento = () => JSON.parse(fs.readFileSync(path.join(ROOT, '../themes/bento.theme.json'), 'utf8'))

describe('TC-UNIT-201 风格注册表与 Web 端一致（AC-074-01/03）', () => {
  it('小程序与 Web 的风格 key / 名称 / 明暗 / 顺序完全一致，默认 bento', () => {
    const pick = (list) => list.map(({ key, name, scheme, order }) => ({ key, name, scheme, order }))
    expect(pick(THEMES)).toEqual(pick(WEB_THEMES))
    expect(THEMES.map((t) => t.name)).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端'])
    expect(DEFAULT_THEME).toBe('bento')
  })
  it('每套风格带完整 tokens 与原生 native 配置', () => {
    for (const t of THEMES) {
      expect(Object.keys(t.tokens).length, t.key).toBeGreaterThan(15)
      for (const k of ['--bg', '--text', '--accent', '--muted']) expect(t.tokens[k], `${t.key} ${k}`).toMatch(/^#[0-9A-Fa-f]{6}$/)
      expect(t.native.tabBar.selectedColor).toMatch(/^#[0-9A-Fa-f]{6}$/)
      expect(['#ffffff', '#000000']).toContain(t.native.navBar.frontColor)
    }
  })
  it('不使用 prefers-color-scheme，明暗只取决于风格', () => {
    for (const f of ['App.vue', 'theme/generated/themes.scss', 'components/ThemeRoot.vue']) expect(read(f), f).not.toMatch(/prefers-color-scheme/)
  })
})

describe('TC-UNIT-202 底部标签栏（AC-083-02、AC-077-01）', () => {
  it('pages.json tabBar 保持 4 项：首页 / 决议 / 投票 / 我的，报销入口不在标签栏', () => {
    const list = pagesJson().tabBar.list
    expect(list.map((i) => i.text)).toEqual(['首页', '决议', '投票', '我的'])
    expect(list.map((i) => i.pagePath)).toEqual(['pages/index/index', 'pages/resolutions/index', 'pages/polls/index', 'pages/me/index'])
  })
  it('tabBar 初值取风格 B 的原生色值（首帧即正确）', () => {
    const tb = pagesJson().tabBar
    const n = bento().native.tabBar
    expect([tb.color, tb.selectedColor, tb.backgroundColor, tb.borderStyle]).toEqual([n.color, n.selectedColor, n.backgroundColor, n.borderStyle])
  })
  it('页面清单为 13 页', () => {
    expect(pagesJson().pages).toHaveLength(13)
  })
})

describe('TC-UNIT-203 风格 store 规则（AC-079-04、AC-086-01）', () => {
  it('设备记忆缺失 / 空串 / 大写 / 未注册 key → bento；合法已注册 → 原值（首帧）', () => {
    for (const [saved, expected] of [['', 'bento'], ['Neon', 'bento'], ['retired-d', 'bento'], ['x', 'bento'], ['neon', 'neon'], ['terminal', 'terminal']]) {
      uni.setStorageSync('ocap_theme', saved)
      setActivePinia(createPinia())
      expect(useThemeStore().current, saved).toBe(expected)
    }
  })
  it('select 不存在的风格被拒绝且不发请求', async () => {
    setActivePinia(createPinia())
    const store = useThemeStore()
    await expect(store.select('retired-d')).rejects.toThrow()
    expect(uni.request).not.toHaveBeenCalled()
    expect(store.current).toBe('bento')
  })
  it('原生 API 缺失（如非 tabBar 页 / 平台不支持）时 applyNative 不抛错', () => {
    const saved = { tab: uni.setTabBarStyle, nav: uni.setNavigationBarColor }
    uni.setTabBarStyle = undefined
    uni.setNavigationBarColor = () => { throw new Error('unsupported') }
    setActivePinia(createPinia())
    try {
      expect(() => useThemeStore().applyNative('neon')).not.toThrow()
    } finally {
      uni.setTabBarStyle = saved.tab
      uni.setNavigationBarColor = saved.nav
    }
  })
  it('cssVarsText 含当前风格的变量，随 current 变化', () => {
    setActivePinia(createPinia())
    const store = useThemeStore()
    expect(store.cssVarsText).toContain('--bg:#F3F4FA')
    store.current = 'terminal'
    expect(store.cssVarsText).toContain('--accent:#C6FF3D')
  })
})

describe('TC-UNIT-204 状态标签 圆点 + 文字 + 语义色（AC-087-03）', () => {
  it('表决中=警示、已通过=成功、未通过=危险，文字互不相同', () => {
    const out = {}
    for (const s of ['OPEN', 'APPROVED', 'REJECTED']) {
      const w = mount(StatusTag, { props: { status: s } })
      expect(w.find('.tag-dot').exists(), s).toBe(true)
      out[s] = { text: w.text(), cls: w.classes() }
    }
    expect(out.OPEN.cls).toContain('is-warning')
    expect(out.APPROVED.cls).toContain('is-success')
    expect(out.REJECTED.cls).toContain('is-danger')
    expect(new Set(Object.values(out).map((o) => o.text)).size).toBe(3)
  })
})

describe('TC-UNIT-205 动效约束（AC-089-01）', () => {
  it('小程序样式中无循环装饰动画（animation ... infinite）', () => {
    for (const f of ['App.vue', 'theme/generated/themes.scss', 'components/ThemeRoot.vue']) expect(read(f), f).not.toMatch(/infinite/)
    for (const k of ['neon', 'bento', 'terminal']) expect(fs.readFileSync(path.join(ROOT, `../themes/${k}.mp.css`), 'utf8'), k).not.toMatch(/infinite/)
  })
})
