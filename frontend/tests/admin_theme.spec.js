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

  it('管理端顶栏使用渐变与 onHero 文字，高亮为白胶囊 + 强调色文字，悬停规则在高亮之前', () => {
    const bar = adminBlock(`${PREFIX} .admin-bar`)
    expect(bar).toMatch(/background:\s*var\(--hero\)/)
    expect(bar).toMatch(/color:\s*var\(--on-hero\)/)
    const brand = adminBlock(`${PREFIX} .admin-bar .brand`)
    expect(brand).toMatch(/color:\s*var\(--on-hero\)/)
    const active = adminBlock(`${PREFIX} .admin-bar .topnav a.is-active`)
    expect(active).toMatch(/background:\s*var\(--surface\)/)
    expect(active).toMatch(/color:\s*var\(--accent-text\)/)
    expect(active).not.toMatch(/#11121A|#fff/i)
    expect(bentoWeb.indexOf(`${PREFIX} .admin-bar .topnav a:hover`))
      .toBeLessThan(bentoWeb.indexOf(`${PREFIX} .admin-bar .topnav a.is-active`))
  })

  it('用户端 B 风格的黑色高亮胶囊与胶囊容器原样保留', () => {
    expect(bentoWeb).toContain(
      'html[data-theme="bento"] .topnav a.is-active, html[data-theme="bento"] .tabbar a.is-active { background: #11121A; color: #fff; }'
    )
    expect(bentoWeb).toContain('html[data-theme="bento"] .topnav { background: var(--surface); border-radius: 999px;')
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
  it('AdminLayout 渲染品牌、13 个导航链接、当前页高亮与顶栏切换入口', async () => {
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
    expect(wrapper.find('.admin-bar .brand').exists()).toBe(true)
    expect(wrapper.findAll('.admin-bar .topnav a')).toHaveLength(13)
    expect(wrapper.find('.admin-bar .admin-theme-trigger').exists()).toBe(true)
    expect(wrapper.find('.admin-bar .topnav a.is-active').text()).toBe('业主清册')
    wrapper.unmount()
  })

  it('themes 校验无错误，生成物与源同步', () => {
    const result = run(path.join(ROOT, 'themes'))
    expect(result.errors).toEqual([])
  })
})
