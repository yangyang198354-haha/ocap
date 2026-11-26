// ocap_typography_unify GROUP_D：排版令牌与主题清理静态守护（MOD-221/222/227）。
// jsdom 不计算真实布局/对比度，这里按 layout_css.spec.js 的既定模式断言样式表源码里的规则；
// 真实视口度量（375px 换行、无横向滚动、中文宽度误差 ≤2px）见 e2e_test_report 人工验证清单。
// 层级：unit（读 CSS 源文件）。TC-UNIT-2100 起。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
// Windows 检出（core.autocrlf=true）为 CRLF，断言按 LF 口径比较
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r\n/g, '\n')
const strip = (css) => css.replace(/\/\*[\s\S]*?\*\//g, '')
const style = strip(read('frontend/src/shared/style.css'))

// 取某选择器（完整匹配，可含逗号列表中的其一）的声明块；允许在 @media 内
const rules = (css, selector) => {
  const out = []
  for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const sels = m[1].split(',').map((s) => s.trim())
    if (sels.includes(selector)) out.push(m[2])
  }
  return out
}
const decl = (css, selector, prop) => {
  const hit = rules(css, selector).find((b) => new RegExp(`(^|;|\\s)${prop}\\s*:`).test(b))
  return hit ? hit.match(new RegExp(`(?:^|;|\\s)${prop}\\s*:\\s*([^;]+)`))[1].trim() : null
}
const rootVar = (css, name) => {
  const m = rules(css, ':root').join('\n').match(new RegExp(`${name}:\\s*([^;\\n]+)`))
  return m ? m[1].trim() : null
}
// 在一份 CSS 里找出选择器命中 pred 的所有声明块（选择器按逗号拆分后任一命中）
const blocksBySelector = (css, pred) => {
  const out = []
  for (const m of strip(css).matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const sels = m[1].split(',').map((s) => s.trim())
    if (sels.some(pred)) out.push({ selectors: sels, block: m[2] })
  }
  return out
}
const hasProp = (block, prop) => new RegExp(`(^|;|\\s)${prop}\\s*:`).test(block)
const propVal = (block, prop) => {
  const m = block.match(new RegExp(`(?:^|;|\\s)${prop}\\s*:\\s*([^;]+)`))
  return m ? m[1].trim() : null
}

describe('排版令牌（MOD-221，AC-365-01/02/03）', () => {
  it('TC-UNIT-2101 / AC-365-01：页面标题令牌 24px/32px/700，窄屏 <768 降为 22px/30px，.page-head h1/.page-title 只引用令牌', () => {
    expect(rootVar(style, '--text-page-title')).toBe('24px')
    expect(rootVar(style, '--leading-page-title')).toBe('32px')
    expect(rootVar(style, '--text-page-title-sm')).toBe('22px')
    expect(rootVar(style, '--leading-page-title-sm')).toBe('30px')
    expect(rootVar(style, '--weight-title')).toBe('700')
    // 基础规则引用令牌，不写死像素/字重
    const base = rules(style, '.page-head h1, .page-title').join(';') || rules(style, '.page-head h1').join(';')
    expect(base).toMatch(/font-size:\s*var\(--text-page-title\)/)
    expect(base).toMatch(/line-height:\s*var\(--leading-page-title\)/)
    expect(base).toMatch(/font-weight:\s*var\(--weight-title\)/)
    expect(base).not.toMatch(/font-size:\s*24px/)
    expect(base).not.toMatch(/font-weight:\s*700/)
    // 窄屏块（max-width: 767.98px，等价 <768）切到小一档令牌
    const narrow = style.match(/@media \(max-width: 767\.98px\)\s*\{([\s\S]*?)\n\}/)
    expect(narrow).not.toBeNull()
    expect(narrow[1]).toMatch(/\.page-head h1[^{]*\{[^}]*font-size:\s*var\(--text-page-title-sm\)/)
    expect(narrow[1]).toMatch(/line-height:\s*var\(--leading-page-title-sm\)/)
  })

  it('TC-UNIT-2102 / AC-365-02、AC-367-01：卡片标题令牌 18px/26px/650，.title 只引用令牌；bento 不再放大到 20px', () => {
    expect(rootVar(style, '--text-card-title')).toBe('18px')
    expect(rootVar(style, '--leading-card-title')).toBe('26px')
    expect(rootVar(style, '--weight-card-title')).toBe('650')
    const title = rules(style, '.title').join(';')
    expect(title).toMatch(/font-size:\s*var\(--text-card-title\)/)
    expect(title).toMatch(/line-height:\s*var\(--leading-card-title\)/)
    expect(title).toMatch(/font-weight:\s*var\(--weight-card-title\)/)
    expect(title).not.toMatch(/font-size:\s*18px/)
    // bento 源与生成态都不存在 .home-grid .title 的 20px 覆盖
    for (const f of ['themes/bento.web.css', 'frontend/src/theme/generated/themes.css']) {
      const css = strip(read(f))
      const overrides = blocksBySelector(css, (s) => /\.home-grid\s+\.title/.test(s) || /\.title/.test(s) && /home-grid/.test(s))
        .filter(({ block }) => propVal(block, 'font-size') === '20px')
      expect(overrides, `${f} 不应存在 .home-grid .title font-size:20px 覆盖`).toEqual([])
    }
  })

  it('TC-UNIT-2103 / AC-365-03：分区标题令牌 14px/20px；.title/.section-title/.page-head h1 字号均来自令牌，无浏览器默认', () => {
    expect(rootVar(style, '--text-section-title')).toBe('14px')
    expect(rootVar(style, '--leading-section-title')).toBe('20px')
    const section = rules(style, '.section-title').join(';')
    expect(section).toMatch(/font-size:\s*var\(--text-section-title\)/)
    expect(section).toMatch(/line-height:\s*var\(--leading-section-title\)/)
    // 三个层级选择器的 font-size 声明都必须是 var(...)，无字面量 px
    for (const sel of ['.page-head h1', '.page-title', '.title', '.section-title']) {
      const blocks = rules(style, sel)
      expect(blocks.length, `${sel} 应存在`).toBeGreaterThan(0)
      for (const b of blocks) {
        if (hasProp(b, 'font-size')) expect(b).toMatch(/font-size:\s*var\(--text-/)
      }
    }
  })
})

describe('一级/二级导航字体统一（MOD-221/222，AC-366-01/02）', () => {
  it('TC-UNIT-2104 / AC-366-01：一级导航令牌 15px/22px/600；bento/neon/terminal 三套主题的 .side-item 均不覆盖 font-size', () => {
    expect(rootVar(style, '--text-nav-primary')).toBe('15px')
    expect(rootVar(style, '--leading-nav-primary')).toBe('22px')
    expect(rootVar(style, '--weight-nav-primary')).toBe('600')
    const nav = rules(style, '.side-item').join(';')
    expect(nav).toMatch(/font-size:\s*var\(--text-nav-primary\)/)
    expect(nav).toMatch(/font-weight:\s*var\(--weight-nav-primary\)/)
    // 三套主题源 + 生成态：.side-item（非 is-active、非伪元素、非 side-sub-item）规则块不含 font-size
    const isPlainSideItem = (s) => /\.side-item\b/.test(s) && !/\.side-sub-item/.test(s) && !/\.is-active/.test(s) && !/::/.test(s)
    for (const f of ['themes/bento.web.css', 'themes/neon.web.css', 'themes/terminal.web.css', 'frontend/src/theme/generated/themes.css']) {
      const bad = blocksBySelector(strip(read(f)), isPlainSideItem).filter(({ block }) => hasProp(block, 'font-size'))
      expect(bad.map((b) => b.selectors.join(',')), `${f} 的 .side-item 不应覆盖 font-size（基线 16/17px 已删除）`).toEqual([])
    }
  })

  it('TC-UNIT-2105 / AC-366-02：二级导航令牌 13px/20px/500，.side-sub-item 与 .sub-nav-item 引用令牌且小于一级', () => {
    expect(rootVar(style, '--text-nav-secondary')).toBe('13px')
    expect(rootVar(style, '--leading-nav-secondary')).toBe('20px')
    expect(rootVar(style, '--weight-nav-secondary')).toBe('500')
    // 二级字号(13) 严格小于一级(15)
    expect(parseInt(rootVar(style, '--text-nav-secondary'), 10)).toBeLessThan(parseInt(rootVar(style, '--text-nav-primary'), 10))
    for (const sel of ['.side-sub-item', '.sub-nav-item']) {
      const block = rules(style, sel).join(';')
      expect(block, `${sel} 应存在`).not.toBe('')
      expect(block).toMatch(/font-size:\s*var\(--text-nav-secondary\)/)
      expect(block).toMatch(/font-weight:\s*var\(--weight-nav-secondary\)/)
    }
    // 三主题不覆盖二级导航字号
    const isSecondary = (s) => (/\.side-sub-item\b/.test(s) || /\.sub-nav-item\b/.test(s)) && !/\.is-active/.test(s) && !/::/.test(s)
    for (const f of ['themes/bento.web.css', 'themes/neon.web.css', 'themes/terminal.web.css']) {
      const bad = blocksBySelector(strip(read(f)), isSecondary).filter(({ block }) => hasProp(block, 'font-size'))
      expect(bad.map((b) => b.selectors.join(',')), `${f} 不应覆盖二级导航字号`).toEqual([])
    }
  })
})

describe('terminal 主题清理（MOD-222，AC-366-03、AC-367-03、AC-362-01）', () => {
  const terminal = strip(read('themes/terminal.web.css'))
  const generated = strip(read('frontend/src/theme/generated/themes.css'))
  // 受 AC-366-03 约束的"标题/导航"选择器：不得被强制大写
  const TITLE_NAV = ['.title', '.page-head h1', '.side-item', '.side-sub-item', '.sub-nav-item']

  it('TC-UNIT-2106 / AC-366-03、AC-367-03：terminal 标题/导航不强制 uppercase、不设 .06em 字距；仍保留 --mono 字族', () => {
    for (const sel of TITLE_NAV) {
      const pred = (s) => new RegExp(sel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/ /g, '\\s+')).test(s) || s.includes(sel)
      const blocks = blocksBySelector(terminal, pred).filter(({ selectors }) =>
        selectors.some((s) => /title|side-item|side-sub-item|sub-nav-item|page-head/.test(s)))
      for (const { block, selectors } of blocks) {
        // 排除 .is-active / 伪元素 / 非标题类（如 .chip、.auth-sub、表头）——只看标题/导航本体
        const relevant = selectors.filter((s) => !/\.is-active|::|\.chip|auth-sub|el-table|reports-accounts-head|el-tabs/.test(s))
        if (relevant.length === 0) continue
        expect(block, `terminal ${relevant.join(',')} 不应 text-transform: uppercase`).not.toMatch(/text-transform:\s*uppercase/)
        if (hasProp(block, 'letter-spacing')) {
          expect(propVal(block, 'letter-spacing'), `terminal ${relevant.join(',')} 字距不应为 .06em`).not.toBe('.06em')
        }
      }
    }
    // terminal 仍为标题/导航设置 --mono 字族（中文宽度由字族统一，不靠 uppercase 拉宽）
    expect(terminal).toMatch(/\.title[^{]*\{[^}]*font-family:\s*var\(--mono\)/)
    expect(terminal).toMatch(/\.side-item[^{]*\{[^}]*font-family:\s*var\(--mono\)/)
  })

  it('TC-UNIT-2107 / AC-362-01：全站不存在 .page-eyebrow 规则（style.css + 三主题 + 生成态）', () => {
    const files = ['frontend/src/shared/style.css', 'themes/bento.web.css', 'themes/neon.web.css', 'themes/terminal.web.css', 'frontend/src/theme/generated/themes.css']
    for (const f of files) {
      const css = strip(read(f))
      const eyebrowRules = blocksBySelector(css, (s) => /\.page-eyebrow\b/.test(s))
      expect(eyebrowRules, `${f} 不应存在 .page-eyebrow 规则`).toEqual([])
    }
  })

  it('TC-UNIT-2108 / AC-362-01、AC-369-02：terminal 无 .page-head h1::before "> " 前缀；.page-head h1 无 ellipsis/nowrap 截断', () => {
    // 不应存在给页面标题加 "> " 的伪元素
    const prefixBlocks = blocksBySelector(terminal, (s) => /\.page-head\s+h1::?before/.test(s))
      .filter(({ block }) => /content:\s*['"]>\s?['"]/.test(block))
    expect(prefixBlocks, 'terminal 不应给 .page-head h1 加 "> " 前缀').toEqual([])
    // 生成态同步无此前缀
    const genPrefix = blocksBySelector(generated, (s) => /\.page-head\s+h1::?before/.test(s))
      .filter(({ block }) => /content:\s*['"]>\s?['"]/.test(block))
    expect(genPrefix, 'generated themes.css 不应给 .page-head h1 加 "> " 前缀').toEqual([])
    // 页面标题规则不含截断属性（允许长标题换行，AC-369-02）
    const base = rules(style, '.page-head h1, .page-title').join(';') || rules(style, '.page-head h1').join(';')
    expect(base).not.toMatch(/text-overflow:\s*ellipsis/)
    expect(base).not.toMatch(/white-space:\s*nowrap/)
  })
})

describe('主题生成态与源一致（MOD-227，回归）', () => {
  it('TC-UNIT-2109 / REQ-NFUNC-080：生成态已同步主题清理——无 .side-item 字号覆盖、无 20px 标题放大、terminal .title 不 uppercase', () => {
    const gen = strip(read('frontend/src/theme/generated/themes.css'))
    // 生成态不重复声明 style.css 基础令牌（由生成器设计决定；theme_build 守护源==生成态一致）。
    // 这里守护本次清理结果已传播到生成态：
    const isPlainSideItem = (s) => /\.side-item\b/.test(s) && !/\.side-sub-item/.test(s) && !/\.is-active/.test(s) && !/::/.test(s)
    const badSide = blocksBySelector(gen, isPlainSideItem).filter(({ block }) => hasProp(block, 'font-size'))
    expect(badSide.map((b) => b.selectors.join(',')), '生成态 .side-item 不应覆盖 font-size').toEqual([])
    const badTitle = blocksBySelector(gen, (s) => /\.home-grid\s+\.title/.test(s)).filter(({ block }) => propVal(block, 'font-size') === '20px')
    expect(badTitle, '生成态不应存在 .home-grid .title font-size:20px').toEqual([])
    // 生成态（含 terminal）标题类不强制大写
    const titleUpper = blocksBySelector(gen, (s) => /\.title\b/.test(s) && !/\.is-active|::|\.chip|auth-sub|el-table|reports-accounts-head|el-tabs/.test(s))
      .filter(({ block }) => /text-transform:\s*uppercase/.test(block))
    expect(titleUpper.map((b) => b.selectors.join(',')), '生成态 .title 不应 text-transform: uppercase').toEqual([])
  })
})
