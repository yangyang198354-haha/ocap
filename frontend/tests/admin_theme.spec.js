// MOD-071/IFC-258：管理端主题化守护（ADR-075 完成口径 1~9；US-142）。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import ElementPlus from 'element-plus'

import AdminLayout from '@/admin/AdminLayout.vue'
import { contrastRatio, mix } from '../../scripts/themes/schema.mjs'
import { run } from '../../scripts/themes/build.mjs'

const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src')
const ROOT = path.resolve(SRC, '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')

const PREFIX = 'html[data-theme="bento"][data-surface="admin"]'
const bentoWeb = read('themes/bento.web.css')
const generated = read('frontend/src/theme/generated/themes.css')
const themeJson = JSON.parse(read('themes/bento.theme.json'))

function adminBlock(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = generated.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`))
  return match ? match[1] : null
}

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('口径 1~4：作用域、渐变顶栏与零回归（AC-142-01~04）', () => {
  it('bento.web.css 中含 .admin-bar 的选择器全部以管理端前缀开头', () => {
    const selectors = bentoWeb
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .split('\n')
      .filter((line) => line.includes('{') && line.includes('.admin-bar'))
      .flatMap((line) => line.split('{')[0].split(','))
      .map((item) => item.trim())
      .filter(Boolean)
    expect(selectors.length).toBeGreaterThan(0)
    for (const selector of selectors) expect(selector.startsWith(PREFIX), selector).toBe(true)
  })

  it('neon/terminal 不含管理端顶栏规则', () => {
    for (const key of ['neon', 'terminal']) {
      expect(read(`themes/${key}.web.css`)).not.toContain('.admin-bar')
      const start = generated.indexOf(`html[data-theme="${key}"]`)
      const next = key === 'neon' ? generated.indexOf('html[data-theme="bento"]') : generated.indexOf('/* 低端设备降级')
      expect(generated.slice(start, next)).not.toContain('.admin-bar')
    }
  })

  it('管理端顶栏使用渐变与 onHero 文字；侧栏品牌/当前项高亮改由 .side-item.is-active 承担，悬停规则在高亮之前（0.4 布局同步：原顶栏 .brand/.topnav 改为侧栏）', () => {
    const bar = adminBlock(`${PREFIX} .admin-bar`)
    expect(bar).toMatch(/background:\s*var\(--hero\)/)
    expect(bar).toMatch(/color:\s*var\(--on-hero\)/)
    // 原：.admin-bar .brand 取 on-hero；新：顶栏内的用户菜单触发器取 on-hero，透明底
    const triggerRule = generated.split('}').find((rule) => rule.includes(`${PREFIX} .admin-bar .user-menu-trigger,`))
    const trigger = triggerRule && triggerRule.slice(triggerRule.indexOf('{') + 1)
    expect(trigger).toMatch(/color:\s*var\(--on-hero\)/)
    expect(trigger).toMatch(/background:\s*transparent/)
    // 原：.admin-bar .topnav a.is-active 为表面色胶囊 + 强调色文字；新：侧栏当前项（黑色胶囊，与用户端 B 同款）不得缺失
    expect(bentoWeb).toMatch(/\.side-item\.is-active[\s\S]{0,240}?\{\s*background:\s*rgba\(79,70,229,\.10\);\s*color:\s*var\(--accent-text\);/)
    // 原：hover 规则位于 is-active 规则之前；新：触发器 hover 规则存在且位于 focus-visible 规则之前
    expect(bentoWeb.indexOf(`${PREFIX} .admin-bar .user-menu-trigger:hover`)).toBeGreaterThan(0)
    expect(bentoWeb.indexOf(`${PREFIX} .admin-bar .user-menu-trigger:hover`))
      .toBeLessThan(bentoWeb.indexOf(`${PREFIX} .admin-bar :focus-visible`))
  })

  it('用户端 B 风格的黑色高亮胶囊原样保留（选择器由 .topnav 迁为侧栏 .side-item，.tabbar 保留）', () => {
    expect(bentoWeb).toContain('html[data-theme="bento"] .side-item.is-active')
    expect(bentoWeb).toContain('html[data-theme="bento"] .tabbar a.is-active { background: rgba(79,70,229,.10); color: var(--accent-text); }')
    expect(bentoWeb).toContain('html[data-theme="bento"] .side-item, html[data-theme="bento"] .side-sub-item, html[data-theme="bento"] .sub-nav-item { border-radius: 999px; }')
    expect(bentoWeb).not.toContain('.topnav')
  })

  it('管理端主按钮在生成物中取强调色', () => {
    const block = adminBlock(`${PREFIX} .el-button--primary`)
    expect(block).toMatch(/--el-button-bg-color:\s*var\(--accent\)/)
  })

  it('管理端 .vue 无颜色字面量，静态内联 style 无颜色类属性，<style> 仅用变量', () => {
    const files = []
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name)
        if (entry.isDirectory()) walk(full)
        else if (entry.name.endsWith('.vue')) files.push(full)
      }
    }
    walk(path.join(SRC, 'admin'))
    const bad = []
    for (const file of files) {
      const text = fs.readFileSync(file, 'utf8')
      if (/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/.test(text)) bad.push(`${file}: 颜色字面量`)
      for (const style of text.matchAll(/(?<!:)\bstyle="([^"]*)"/g)) {
        if (/(color|background|border|box-shadow|font-family|opacity)/i.test(style[1])) bad.push(`${file}: 内联样式 ${style[1]}`)
      }
      for (const block of text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)) {
        for (const decl of block[1].matchAll(/(?:^|;)\s*(color|background|border|box-shadow|font-family|opacity)\s*:\s*([^;]+)/g)) {
          const value = decl[2].trim()
          if (!/^(var\(--[\w-]+\)|transparent|inherit|currentColor)$/.test(value)) bad.push(`${file}: ${decl[0]}`)
        }
      }
    }
    expect(bad).toEqual([])
  })
})

describe('口径 5~7：对比度与叠加层（AC-142-05、REQ-NFUNC-21）', () => {
  it('对比度项覆盖渐变三个停点与主按钮/高亮文字', () => {
    const pairs = themeJson.contrast.map((item) => `${item.fg}/${item.bg}`)
    for (const pair of ['onHero/#4F46E5', 'onHero/#7C3AED', 'onHero/#DB2777', 'accentText/#FFFFFF', 'onAccent/#4F46E5']) {
      expect(pairs).toContain(pair)
    }
    const heroStops = [...themeJson.tokens.hero.matchAll(/#[0-9A-Fa-f]{6}/g)].map((m) => m[0])
    for (const stop of heroStops) expect(pairs).toContain(`onHero/${stop}`)
  })

  it('渐变插值采样 ≥1000 点，白字对比度均 ≥4.5', () => {
    const inner = themeJson.tokens.hero.match(/linear-gradient\(([^)]+)\)/)[1]
    const stops = [...inner.matchAll(/(#[0-9A-Fa-f]{6})\s+(\d+)%/g)].map((m) => ({ color: m[1], at: Number(m[2]) }))
    expect(stops.length).toBeGreaterThanOrEqual(2)
    const samples = 1000
    for (let i = 0; i < samples; i++) {
      const pos = (100 * i) / (samples - 1)
      const right = stops.findIndex((stop) => stop.at >= pos)
      let color
      if (right <= 0) color = stops[0].color
      else {
        const a = stops[right - 1]
        const b = stops[right]
        color = mix(a.color, b.color, (pos - a.at) / (b.at - a.at))
      }
      expect(contrastRatio('#FFFFFF', color), `${pos}% ${color}`).toBeGreaterThanOrEqual(4.5)
    }
  })

  it('管理端顶栏的半透明叠加层只能是深色 rgb(17,18,26)', () => {
    const rules = bentoWeb.split('}').filter((rule) => rule.includes('.admin-bar') && rule.includes('rgba('))
    expect(rules.length).toBeGreaterThan(0)
    for (const rule of rules) {
      for (const rgba of rule.matchAll(/rgba\(([^)]+)\)/g)) {
        expect(rgba[1].replace(/\s/g, '')).toMatch(/^17,18,26,/)
      }
    }
  })
})

describe('口径 8~9：布局结构与构建校验（AC-139-01、AC-142-04）', () => {
  it('AdminLayout 渲染侧栏品牌、9 个一级导航（含“内容管理”下的版式模板二级项，REQ-FUNC-153）、当前页高亮与右上角用户菜单（原：顶栏 14 个链接与切换入口）', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/admin/registry', component: { template: '<div />' } },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } }
      ]
    })
    router.push('/admin/registry')
    await router.isReady()
    const wrapper = mount(AdminLayout, { global: { plugins: [createPinia(), router, ElementPlus] } })
    await flushPromises()
    expect(wrapper.find('.admin-side .side-brand').text()).toBe('Cyber@红枫岭 · 管理后台')
    expect(wrapper.find('.admin-bar .brand').exists()).toBe(false)
    expect(wrapper.findAll('.admin-side .side-nav .side-item')).toHaveLength(9)
    expect(wrapper.findAll('.admin-bar .topnav')).toHaveLength(0)
    expect(wrapper.find('.admin-bar .user-menu-trigger').exists()).toBe(true)
    expect(wrapper.find('.admin-side .side-item.is-active').text()).toBe('业主清册')
    // 版式模板（REQ-FUNC-153）现为“内容管理”的二级项：展开后可见
    await wrapper.findAll('.admin-side .side-group-toggle').find((b) => b.text().includes('内容管理')).trigger('click')
    expect(wrapper.find('.admin-side .side-sub').text()).toContain('版式模板')
    wrapper.unmount()
  })

  it('themes 校验无错误，生成物与源同步', () => {
    const result = run(path.join(ROOT, 'themes'))
    expect(result.errors).toEqual([])
  })
})
