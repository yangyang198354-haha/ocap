// ocap_brand_layout GROUP_D（MOD-131）：布局样式静态守护（IFC-331；REQ-NFUNC-038 的静态部分）。
// jsdom 不计算布局，这里只断言样式表源码里的规则；真实视口度量（无横向滚动、占用率、侧栏可见性）见 e2e_test_report 人工验证清单。
// 层级：unit（读 CSS/Vue 源文件）。TC-UNIT-861 起。
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
const mediaConditions = (css) => [...strip(css).matchAll(/@media\s+([^{]+)\{/g)].map((m) => m[1].trim())

describe('宽度与自适应变量（REQ-FUNC-212/213，AC-218-01/03、AC-219-02）', () => {
  it('TC-UNIT-861 / AC-218-03、AC-231-01：布局内 .page 取消 1180px 最大宽度（max-width:none，宽 100%）；布局外 .page 仍为 1180px（登录/注册不受影响）', () => {
    expect(decl(style, '.layout-main .page', 'max-width')).toBe('none')
    expect(decl(style, '.layout-main .page', 'width')).toBe('100%')
    expect(decl(style, '.layout-main .page', 'margin')).toBe('0')
    expect(decl(style, '.page', 'max-width')).toBe('1180px') // style.css:7 保留
    expect(decl(style, '.layout-main', 'min-width')).toBe('0')
    expect(decl(style, '.shell-main', 'min-width')).toBe('0') // 防 grid 子项撑破视口
  })

  it('TC-UNIT-862 / AC-218-04、AC-219-01：--side-w 与 --content-pad 用 clamp()（随视口按比例，不写死像素），--topbar-h 为 56px', () => {
    const root = rules(style, ':root').join(';')
    expect(root).toMatch(/--side-w:\s*clamp\(192px,\s*14vw,\s*248px\)/)
    expect(root).toMatch(/--content-pad:\s*clamp\(12px,\s*1\.2vw,\s*32px\)/)
    expect(root).toMatch(/--topbar-h:\s*56px/)
    expect(root).toMatch(/--hit-min:\s*44px/)
    expect(decl(style, '.shell', 'grid-template-columns')).toBe('var(--side-w) minmax(0, 1fr)')
  })

  it('TC-UNIT-863 / AC-218-02、AC-218-01：决议卡片与首页入口随宽度自适应——.res-grid auto-fill minmax(380px,1fr)、.home-quick-grid auto-fit minmax(150px,1fr)，都在 ≥768px 块内', () => {
    expect(style).toMatch(/@media \(min-width: 768px\)\s*\{[^@]*\.res-grid\s*\{[^}]*repeat\(auto-fill,\s*minmax\(380px,\s*1fr\)\)/)
    expect(style).toMatch(/@media \(min-width: 768px\)\s*\{[^@]*\.home-quick-grid\s*\{[^}]*repeat\(auto-fit,\s*minmax\(150px,\s*1fr\)\)/)
    expect(decl(style, '.res-grid', 'grid-template-columns')).toBe('1fr') // 窄屏单列
  })

  it('TC-UNIT-864 / AC-219-01：侧栏固定在视口左侧（sticky、100vh）且自身可滚动（overflow-y:auto），不撑高页面', () => {
    expect(decl(style, '.side', 'position')).toBe('sticky')
    expect(decl(style, '.side', 'height')).toBe('100vh')
    expect(decl(style, '.side', 'overflow-y')).toBe('auto')
  })
})

describe('断点：只用既有 768px 一对（C-70）', () => {
  it('TC-UNIT-865 / C-70：style.css 的 @media 条件只含 (max-width: 767.98px) 与 (min-width: 768px)', () => {
    const conds = new Set(mediaConditions(read('frontend/src/shared/style.css')))
    // F3（ocap_batch_1118，ADR-144、AC-252-05/AC-253-04）：断点仍只有 768px 一对；另放行唯一一个非断点条件 prefers-reduced-motion: no-preference
    const widthConds = [...conds].filter((c) => /width/.test(c)).sort()
    expect(widthConds).toEqual(['(max-width: 767.98px)', '(min-width: 768px)'])
    expect([...conds].filter((c) => !/width/.test(c)).sort()).toEqual(['(prefers-reduced-motion: no-preference)'])
    expect([...conds].sort()).toEqual(['(max-width: 767.98px)', '(min-width: 768px)', '(prefers-reduced-motion: no-preference)'])
  })

  it('TC-UNIT-866 / C-70：themes/*.web.css、*.mp.css 与生成物的 @media 条件只含 767.98px / 768px / prefers-reduced-motion，没有新断点', () => {
    const allowed = /^(\(max-width: 767\.98px\)|\(min-width: 768px\)|\(prefers-reduced-motion: reduce\))$/
    const files = ['neon', 'bento', 'terminal'].flatMap((k) => [`themes/${k}.web.css`, `themes/${k}.mp.css`])
      .concat(['frontend/src/theme/generated/themes.css'])
    const bad = []
    for (const f of files) for (const c of mediaConditions(read(f))) if (!allowed.test(c)) bad.push(`${f}: ${c}`)
    expect(bad).toEqual([])
  })

  it('TC-UNIT-867 / AC-220-01、AC-220-04、AC-230-03：窄屏块（≤767.98px）隐藏侧栏与右上角用户菜单、显示切换条/底栏；宽屏块强制隐藏底栏——两种形态不同时出现', () => {
    const narrow = style.match(/@media \(max-width: 767\.98px\)\s*\{([\s\S]*?)\n\}/)[1]
    expect(narrow).toMatch(/\.side\s*\{\s*display:\s*none;\s*\}/)
    expect(narrow).toMatch(/\.topbar-user\s*\{\s*display:\s*none;\s*\}/)
    expect(narrow).toMatch(/\.sub-nav-bar\s*\{\s*display:\s*flex;\s*\}/)
    expect(narrow).toMatch(/\.admin-menu-btn\s*\{\s*display:\s*inline-flex;\s*\}/)
    expect(narrow).toMatch(/\.shell\s*\{\s*display:\s*block;\s*\}/)
    expect(narrow).toMatch(/\.tabbar\s*\{[^}]*display:\s*flex/)
    const wide = style.match(/@media \(min-width: 768px\)\s*\{([\s\S]*?)\n\}/)[1]
    expect(wide).toMatch(/\.tabbar\s*\{\s*display:\s*none\s*!important;\s*\}/)
    // 基线：窄屏元素默认隐藏，宽屏默认布局成立
    expect(decl(style, '.sub-nav-bar', 'display')).toBe('none')
    expect(decl(style, '.admin-menu-btn', 'display')).toBe('none')
    expect(decl(style, '.tabbar', 'display')).toBe('none')
  })
})

describe('既有规则保持（既有用例 qa_unit_theme 依赖）与可操作性（REQ-NFUNC-039）', () => {
  it('TC-UNIT-868 / REQ-NFUNC-006：--hit-min:44px、.el-button 等最小高度、.tabbar a、.form-actions-sticky（仅窄屏 sticky）、:focus-visible 描边保持不变', () => {
    expect(decl(style, '.el-button', 'min-height')).toBe('var(--hit-min)')
    expect(decl(style, '.tabbar a', 'min-height')).toBe('var(--hit-min)')
    expect(decl(style, ':focus-visible', 'outline')).toBe('2px solid var(--accent)')
    const base = rules(style, '.form-actions-sticky')
    expect(base).toHaveLength(2) // 基础 + 窄屏块
    expect(base[0]).not.toMatch(/position/)
    expect(base[1]).toMatch(/position:\s*sticky/)
    expect(style.match(/@media \(max-width: 767\.98px\)\s*\{([\s\S]*?)\n\}/)[1]).toContain('.form-actions-sticky {')
  })

  it('TC-UNIT-869 / REQ-NFUNC-039、AC-212-01、AC-220-02：侧栏一二级项、窄屏切换项、用户菜单触发器、"我的"总览项的最小高度均为 var(--hit-min)（44px）', () => {
    for (const sel of ['.side-item', '.side-sub-item', '.sub-nav-item', '.user-menu-trigger', '.me-overview-item', '.admin-menu-btn']) {
      expect(decl(style, sel, 'min-height') || decl(style, sel, 'min-width'), sel).toBe('var(--hit-min)')
    }
  })

  it('TC-UNIT-870 / REQ-NFUNC-039：当前项除颜色外有形状/字重提示——3px 左侧指示条 + 加粗（650）', () => {
    const active = rules(style, '.side-item.is-active').join(';')
    expect(active).toMatch(/font-weight:\s*650/)
    expect(active).toMatch(/border-left-color:\s*var\(--accent\)/)
    expect(decl(style, '.side-item', 'border-left')).toBe('3px solid transparent')
    expect(decl(style, '.side-sub-item', 'border-left')).toBe('3px solid transparent')
  })

  it('TC-UNIT-871 / ADR-029、AC-222-01：style.css 与新增 .vue 的 <style> 不写死颜色字面量（只用语义变量）', () => {
    expect(strip(read('frontend/src/shared/style.css'))).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/)
    const dirs = ['frontend/src/layout', 'frontend/src/brand', 'frontend/src/brand/art', 'frontend/src/portal/me', 'frontend/src/portal/units']
    const bad = []
    for (const d of dirs) {
      for (const f of fs.readdirSync(path.join(ROOT, d)).filter((x) => x.endsWith('.vue'))) {
        if (/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/.test(read(`${d}/${f}`))) bad.push(`${d}/${f}`)
      }
    }
    for (const f of ['frontend/src/portal/PortalLayout.vue', 'frontend/src/portal/PortalUserMenu.vue', 'frontend/src/admin/AdminLayout.vue', 'frontend/src/admin/AdminUserMenu.vue']) {
      if (/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/.test(read(f))) bad.push(f)
    }
    expect(bad).toEqual([])
  })
})

describe('登录页自适应（AC-209-04、AC-227-04）', () => {
  it('TC-UNIT-872 / AC-209-04：.auth-shell 宽屏左右分栏（表单栏 minmax(360px,480px)），窄屏上下排列且配图条高 clamp(120px,28vw,180px)；整页铺满不设 1180px 上限', () => {
    expect(decl(style, '.auth-shell', 'grid-template-columns')).toBe('minmax(0, 1fr) minmax(360px, 480px)')
    expect(decl(style, '.auth-shell', 'min-height')).toBe('100vh')
    expect(style.match(/@media \(max-width: 767\.98px\)\s*\{([\s\S]*?)\n\}/)[1]).toMatch(/\.auth-art\s*\{[^}]*height:\s*clamp\(120px,\s*28vw,\s*180px\)/)
    expect(decl(style, '.auth-shell', 'max-width')).toBeNull()
  })

  it('TC-UNIT-873 / AC-209-04：登录/注册/管理端登录页以 AuthShell 为根，不再套 .page（避免 1180px 居中窄列与横向滚动）；配图不覆盖表单（配图与表单栏是并列的兄弟节点）', () => {
    for (const f of ['frontend/src/portal/Login.vue', 'frontend/src/portal/Register.vue', 'frontend/src/admin/AdminLogin.vue']) {
      const tpl = read(f).split('<script')[0]
      expect(tpl.trimStart().startsWith('<template>\n  <AuthShell'), f).toBe(true)
      expect(tpl, f).not.toMatch(/class="[^"]*\bpage\b/)
    }
    const shell = read('frontend/src/brand/AuthShell.vue').split('<script')[0]
    expect(shell.indexOf('class="auth-art"')).toBeGreaterThan(-1)
    expect(shell.indexOf('class="auth-panel"')).toBeGreaterThan(shell.indexOf('class="auth-art"'))
    expect(decl(style, '.auth-art', 'overflow')).toBe('hidden')
    expect(decl(style, '.auth-art', 'position')).toBe('relative')
    expect(shell).toContain('aria-hidden="true"')
  })
})

describe('管理端表格宽度（ADR-121，R-02，AC-231-02）', () => {
  // 1366 视口：1366 − 滚动条 17 − 侧栏 192 − 内容内边距 2×16.4 − 卡片内边距与边框 34 ≈ 1090
  const BUDGET = 1090
  const files = fs.readdirSync(path.join(ROOT, 'frontend/src/admin')).filter((f) => f.endsWith('.vue'))
  const tables = []
  for (const f of files) {
    const tpl = read(`frontend/src/admin/${f}`).split('<script')[0]
    let i = 0
    for (const m of tpl.matchAll(/<el-table\b[^>]*>([\s\S]*?)<\/el-table>/g)) {
      const cols = [...m[1].matchAll(/<el-table-column\b[^>]*>/g)].map((c) => c[0])
      const fixed = cols.reduce((n, c) => n + (c.match(/(?<![\w-])width="(\d+)"/) ? Number(c.match(/(?<![\w-])width="(\d+)"/)[1]) : 0), 0)
      const flex = cols.reduce((n, c) => n + (c.match(/min-width="(\d+)"/) ? Number(c.match(/min-width="(\d+)"/)[1]) : 0), 0)
      tables.push({ id: `${f}#${i++}`, cols: cols.length, total: fixed + flex })
    }
  }

  it('TC-UNIT-874 / AC-231-02、AC-219-02：除已批准加宽并对整体横向滚动的表格外，其余管理端表格合计 ≤ 1090px（设计上限 1110）', () => {
    expect(tables.length).toBeGreaterThanOrEqual(10)
    // REQ-FUNC-282/285/287/292：清册 1190、房屋关系 1550、申诉 1750、席位主表 1590 与失效折叠表 1430，按批准设计整体横向滚动
    const wide = new Set(['AdminRegistry.vue#0', 'AdminMemberships.vue#0', 'AdminAppeals.vue#0',
      'AdminSeats.vue#0', 'AdminSeats.vue#1'])
    const over = tables.filter((t) => !wide.has(t.id) && t.total > BUDGET).map((t) => `${t.id}=${t.total}`)
    expect(over).toEqual([])
  })

  it('TC-UNIT-875 / ADR-121 R-02、REQ-FUNC-282/285/287：已知最宽的表格合计与批准列宽一致，列含义与数量未变', () => {
    const by = Object.fromEntries(tables.map((t) => [t.id, t]))
    expect(by['AdminRegistry.vue#0']).toMatchObject({ cols: 9, total: 1190 })
    expect(by['AdminMemberships.vue#0']).toMatchObject({ cols: 13, total: 1550 })
    expect(by['AdminSeats.vue#0']).toMatchObject({ cols: 15, total: 1590 })
    expect(by['AdminAppeals.vue#0']).toMatchObject({ cols: 10, total: 1750 })
    expect(by['AdminUsers.vue#1']).toMatchObject({ cols: 9, total: 990 })
    expect(by['AdminUsers.vue#0']).toMatchObject({ cols: 4, total: 480 })
    // 注册用户表列顺序与含义不变（AdminUsers.vue 注册用户表）
    const tpl = read('frontend/src/admin/AdminUsers.vue').split('<script')[0]
    const labelsOf = [...tpl.split('注册用户')[1].matchAll(/<el-table-column[^>]*\blabel="([^"]+)"/g)].map((m) => m[1])
    expect(labelsOf).toEqual(['ID', '账号', '手机号', '昵称', '状态', '身份', '认证', '实名', '上次登录'])
  })
})
