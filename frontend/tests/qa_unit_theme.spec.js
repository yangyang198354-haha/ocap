// PHASE_07 单元测试（ocap_ui_theme / Web）：单模块规则，外部依赖 mock。
// 溯源：AC-074-01/03、AC-075-02、AC-079-01/03/04、AC-080-03/04、AC-082-03、AC-087-01、AC-088-01/02/04、AC-089-01/02、AC-090-01、AC-084-03
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import vm from 'node:vm'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { THEMES, DEFAULT_THEME } from '@/theme/generated/registry'
import { useThemeStore } from '@/theme/store'
import { detectLowEnd } from '@/theme/apply'
import StatusTag from '@/portal/StatusTag.vue'
import { run } from '../../scripts/themes/build.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const json = (key) => JSON.parse(read(`themes/${key}.theme.json`))

// 独立的 WCAG 2.x 对比度实现（不复用被测的 contrastRatio，避免用被测代码生成期望）
function lum(hex) {
  const v = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
}
const ratio = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  document.documentElement.removeAttribute('data-perf')
  document.documentElement.classList.remove('dark')
  setActivePinia(createPinia())
})

describe('TC-UNIT-101 风格定义与明暗（AC-074-01/02/03）', () => {
  it('恰好 3 套，A/C 深色、B 浅色，没有“跟随系统”选项，也没有同风格浅深变体', () => {
    expect(THEMES).toHaveLength(3)
    expect(Object.fromEntries(THEMES.map((t) => [t.key, t.scheme]))).toEqual({ neon: 'dark', bento: 'light', terminal: 'dark' })
    expect(new Set(THEMES.map((t) => t.key)).size).toBe(3)
    expect(THEMES.some((t) => /系统|auto|system/i.test(t.name + t.key))).toBe(false)
  })
  it('明暗只取决于所选风格：所有样式源均不使用 prefers-color-scheme', () => {
    for (const rel of ['frontend/src/theme/generated/themes.css', 'frontend/src/shared/style.css',
      'themes/neon.web.css', 'themes/bento.web.css', 'themes/terminal.web.css', 'miniprogram/App.vue',
      'miniprogram/theme/generated/themes.scss', 'frontend/src/theme/apply.js', 'frontend/index.html']) {
      expect(read(rel), rel).not.toMatch(/prefers-color-scheme/)
    }
  })
})

describe('TC-UNIT-102 对比度（AC-088-01/04），独立实现交叉校验', () => {
  it('独立实现自检：黑白 = 21，同色 = 1', () => {
    expect(ratio('#000000', '#FFFFFF')).toBeCloseTo(21, 5)
    expect(ratio('#123456', '#123456')).toBeCloseTo(1, 5)
  })
  for (const key of ['neon', 'bento', 'terminal']) {
    it(`${key}：正文 / 次要 / 强调文字相对页面底色均 ≥ 4.5；声明的每个组合独立复算 ≥ 其 min`, () => {
      const def = json(key)
      const t = def.tokens
      for (const fg of ['text', 'muted', 'accentText']) {
        expect(ratio(t[fg], t.bg), `${key}.${fg}/bg`).toBeGreaterThanOrEqual(4.5)
      }
      for (const c of def.contrast) {
        const fg = t[c.fg] || c.fg
        expect(ratio(fg, c.bg), `${key}:${c.label}`).toBeGreaterThanOrEqual(c.min - 0.005)
        expect(c.min).toBeGreaterThanOrEqual(4.5)
      }
    })
  }
  it('低端降级（glassLowEnd 纯色）上的正文对比度仍 ≥ 4.5（AC-089-02）', () => {
    for (const key of ['neon', 'bento', 'terminal']) {
      const t = json(key).tokens
      expect(ratio(t.text, t.glassLowEnd), key).toBeGreaterThanOrEqual(4.5)
    }
  })
})

describe('TC-UNIT-103 构建器拒绝不合规风格（AC-080-03、AC-088-04）', () => {
  function withThemes(mutator) {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-themes-'))
    for (const k of ['neon', 'bento', 'terminal']) fs.copyFileSync(path.join(ROOT, `themes/${k}.theme.json`), path.join(tmp, `${k}.theme.json`))
    mutator(tmp)
    try { return run(tmp) } finally { fs.rmSync(tmp, { recursive: true, force: true }) }
  }
  const base = () => json('neon')
  it('对比度低于 4.5 的风格不进入注册表，并给出定位信息', () => {
    const { outputs, errors } = withThemes((dir) => {
      const d = { ...base(), key: 'lowc', name: '低对比', order: 7, tokens: { ...base().tokens, muted: '#222233' } }
      fs.writeFileSync(path.join(dir, 'lowc.theme.json'), JSON.stringify(d))
    })
    expect(outputs['frontend/src/theme/generated/registry.js']).not.toContain('低对比')
    expect(errors.join('\n')).toMatch(/lowc\.theme\.json/)
  })
  it('contrast.min 声明低于 4.5 的风格被拒', () => {
    const { outputs, errors } = withThemes((dir) => {
      const b = base()
      const d = { ...b, key: 'lowmin', name: '低门槛', order: 8, contrast: b.contrast.map((c, i) => (i === 0 ? { ...c, min: 3 } : c)) }
      fs.writeFileSync(path.join(dir, 'lowmin.theme.json'), JSON.stringify(d))
    })
    expect(outputs['frontend/src/theme/generated/registry.js']).not.toContain('低门槛')
    expect(errors.length).toBeGreaterThan(0)
  })
  it('key 与文件名不一致、非法 JSON、非法 key 格式均被拒且不影响其余三套', () => {
    const { outputs, errors } = withThemes((dir) => {
      fs.writeFileSync(path.join(dir, 'mismatch.theme.json'), JSON.stringify({ ...base(), key: 'other', name: '错位', order: 5 }))
      fs.writeFileSync(path.join(dir, 'broken.theme.json'), '{not json')
      fs.writeFileSync(path.join(dir, 'Bad.theme.json'), JSON.stringify({ ...base(), key: 'Bad', name: '大写', order: 6 }))
    })
    const reg = outputs['frontend/src/theme/generated/registry.js']
    for (const n of ['错位', '大写']) expect(reg).not.toContain(n)
    for (const n of ['霓虹玻璃', '极光 Bento', '赛博终端']) expect(reg).toContain(n)
    expect(errors.length).toBeGreaterThanOrEqual(3)
  })
  it('缺少默认风格 bento 时构建失败（fatal）', () => {
    const { fatal } = withThemes((dir) => fs.rmSync(path.join(dir, 'bento.theme.json')))
    expect(fatal).toBeTruthy()
  })
})

describe('TC-UNIT-104 首屏内联脚本（AC-079-01/02/04、AC-082-02、AC-090-02）', () => {
  const html = read('frontend/index.html')
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1]
  function runInline({ saved, pathname }) {
    const attrs = {}
    const sandbox = {
      location: { pathname },
      localStorage: { getItem: () => saved ?? null },
      document: { documentElement: { setAttribute: (k, v) => { attrs[k] = v } } }
    }
    vm.runInNewContext(script, sandbox)
    return attrs['data-theme']
  }
  it('无记忆 → bento', () => expect(runInline({ pathname: '/ocap/login' })).toBe('bento'))
  it('有合法记忆 → 同步设置记忆值（样式解析前，无先 B 后 C 的跳变）', () => {
    expect(runInline({ saved: 'terminal', pathname: '/ocap/' })).toBe('terminal')
  })
  it('格式非法（大写、空白、1 字符）→ bento', () => {
    for (const bad of ['Terminal', 'a b', 'x', '1ab', '']) expect(runInline({ saved: bad, pathname: '/' }), bad).toBe('bento')
  })
  it('管理端路径恒为 bento，不受设备记忆影响', () => {
    expect(runInline({ saved: 'terminal', pathname: '/ocap/admin/registry' })).toBe('bento')
    expect(runInline({ saved: 'neon', pathname: '/admin/login' })).toBe('bento')
  })
  it('存储不可用（抛错）→ bento，不抛出', () => {
    const attrs = {}
    vm.runInNewContext(script, {
      location: { pathname: '/' },
      localStorage: { getItem: () => { throw new Error('denied') } },
      document: { documentElement: { setAttribute: (k, v) => { attrs[k] = v } } }
    })
    expect(attrs['data-theme']).toBe('bento')
  })
  it('格式合法但已下线的 key：根选择器默认变量即风格 B，页面可读（AC-079-04 渲染兜底）', () => {
    const css = read('frontend/src/theme/generated/themes.css')
    const rootBlock = css.match(/:root\s*\{[\s\S]*?\n\}/)[0]
    expect(rootBlock).toContain('--bg: #F3F4FA')
    expect(rootBlock).toContain('--text: #11121A')
    expect(css).not.toMatch(/data-theme="retired/)
  })
})

describe('TC-UNIT-105 样式规则存在性（AC-089-01/02、AC-088-02、AC-084-03）', () => {
  const css = read('frontend/src/theme/generated/themes.css')
  const base = read('frontend/src/shared/style.css')
  it('三套风格各有 html[data-theme] 作用域变量块', () => {
    for (const key of ['neon', 'bento', 'terminal']) expect(css).toContain(`html[data-theme="${key}"]`)
  })
  it('prefers-reduced-motion：关闭 animation 与 transition，隐藏装饰层', () => {
    const block = css.match(/@media \(prefers-reduced-motion: reduce\)\s*\{[\s\S]*?\n\}/)[0]
    expect(block).toMatch(/animation:\s*none\s*!important/)
    expect(block).toMatch(/transition:\s*none\s*!important/)
    expect(block).toMatch(/\.theme-decor\s*\{\s*display:\s*none\s*!important/)
  })
  it('data-perf=low：玻璃模糊降级为不透明纯色；A、C 的循环动画被关闭', () => {
    const block = css.match(/html\[data-perf="low"\]\s*\{[\s\S]*?\}/)[0]
    expect(block).toMatch(/--blur:\s*none/)
    expect(block).toMatch(/--glass:\s*var\(--glass-low-end\)/)
    expect(css).toMatch(/html\[data-theme="neon"\]\[data-perf="low"\][^{]*\{\s*animation:\s*none/)
    expect(css).toMatch(/html\[data-theme="terminal"\]\[data-perf="low"\][^{]*\{\s*animation:\s*none/)
  })
  it('点击区域 ≥ 44px：--hit-min 为 44px 并用于按钮/输入框/标签栏（AC-088-02）', () => {
    expect(base).toMatch(/--hit-min:\s*44px/)
    expect(base).toMatch(/\.el-button,[^{]*\.el-input__wrapper[^{]*\{\s*min-height:\s*var\(--hit-min\)/)
    expect(base).toMatch(/\.tabbar a\s*\{[^}]*min-height:\s*var\(--hit-min\)/)
  })
  it('桌面布局不变：宽屏 .tabbar 隐藏且 .form-actions-sticky 非吸底；吸底仅在 ≤767.98px 媒体查询内', () => {
    expect(base).toMatch(/\.tabbar\s*\{\s*display:\s*none;\s*\}/)
    const desktop = base.split('@media (max-width: 767.98px)')[0]
    expect(desktop).toMatch(/\.form-actions-sticky\s*\{[^}]*\}/)
    expect(desktop.match(/\.form-actions-sticky\s*\{([^}]*)\}/)[1]).not.toMatch(/position/)
    expect(base.split('@media (max-width: 767.98px)')[1]).toMatch(/\.form-actions-sticky\s*\{[^}]*position:\s*sticky/)
  })
  it('焦点环：:focus-visible 有可见描边（AC-088-03）', () => {
    expect(base).toMatch(/:focus-visible\s*\{[^}]*(outline|box-shadow)/)
  })
})

describe('TC-UNIT-106 低端设备判定与降级标记（AC-089-02）', () => {
  const setNav = (props) => {
    for (const [k, v] of Object.entries(props)) Object.defineProperty(navigator, k, { value: v, configurable: true })
  }
  it('内存 ≤4GB 或 CPU ≤4 核 → data-perf=low；配置充足 → 无标记', () => {
    setNav({ deviceMemory: 2, hardwareConcurrency: 8 })
    expect(detectLowEnd()).toBe(true)
    expect(document.documentElement.getAttribute('data-perf')).toBe('low')
    setNav({ deviceMemory: 8, hardwareConcurrency: 4 })
    expect(detectLowEnd()).toBe(true)
    setNav({ deviceMemory: 16, hardwareConcurrency: 12 })
    expect(detectLowEnd()).toBe(false)
    expect(document.documentElement.hasAttribute('data-perf')).toBe(false)
  })
})

describe('TC-UNIT-107 状态标签 圆点 + 文字 + 语义色（AC-087-01）', () => {
  it('表决中=警示、已通过=成功、未通过=危险；三者文字互不相同且各带圆点', () => {
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
    expect(out.APPROVED.text).toBe('通过')
    expect(out.REJECTED.text).toBe('未通过')
  })
  it('未知状态显示原值，不留空', () => {
    expect(mount(StatusTag, { props: { status: 'WEIRD' } }).text()).toBe('WEIRD')
  })
})

describe('TC-UNIT-108 风格入口范围（AC-075-02、AC-079-03、AC-080-04、AC-082-03）', () => {
  const vue = (dir) => fs.readdirSync(path.join(ROOT, dir)).filter((f) => f.endsWith('.vue')).map((f) => `${dir}/${f}`)
  it('只有个人中心 Me.vue 引用 ThemePicker；管理端、登录/注册/回调页没有任何风格入口', () => {
    const users = [...vue('frontend/src/portal'), ...vue('frontend/src/admin')]
      .filter((f) => /ThemePicker|界面风格|useThemeStore\(\)\.select|\.select\(/.test(read(f)) && /ThemePicker|界面风格/.test(read(f)))
    expect(users).toEqual(['frontend/src/portal/Me.vue'])
  })
  it('管理端无“全站默认风格”“新增风格”等设置入口（文案与接口均无）', () => {
    for (const f of vue('frontend/src/admin')) expect(read(f), f).not.toMatch(/默认风格|新增风格|风格设置|\/theme/)
    expect(read('frontend/src/shared/api.js')).not.toMatch(/admin[A-Za-z]*\.[a-z]+\([^)]*theme/i)
  })
  it('路由：用户端 14 个页面组件、管理端 9 个页面组件均存在', () => {
    const router = read('frontend/src/router/index.js')
    const comps = [...router.matchAll(/import\('@\/(portal|admin)\/(\w+)\.vue'\)/g)].map((m) => `${m[1]}/${m[2]}`)
    expect(comps.filter((c) => c.startsWith('portal/')).length).toBe(15) // 14 页 + PortalLayout
    expect(comps.filter((c) => c.startsWith('admin/')).length).toBe(10) // 9 页 + AdminLayout
  })
})

describe('TC-UNIT-109 点击到应用的同步耗时（AC-090-01 自动化部分）', () => {
  it('select() 触发后 data-theme 与 dark 类在 1 s 内变化（jsdom 逻辑耗时，非真实渲染）', async () => {
    mocked.http.put.mockResolvedValue({ theme: 'terminal' })
    const store = useThemeStore()
    const t0 = performance.now()
    const p = store.select('terminal')
    expect(document.documentElement.getAttribute('data-theme')).toBe('terminal') // 乐观应用，同步完成
    expect(performance.now() - t0).toBeLessThan(1000)
    await p
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(DEFAULT_THEME).toBe('bento')
  })
  it('选择不存在的风格被拒绝且 DOM 不变（AC-086-02）', async () => {
    const store = useThemeStore()
    store.initFromDevice()
    await expect(store.select('retired')).rejects.toThrow()
    expect(document.documentElement.getAttribute('data-theme')).toBe('bento')
    expect(mocked.http.put).not.toHaveBeenCalled()
  })
})
