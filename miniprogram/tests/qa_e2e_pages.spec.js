// PHASE_09 E2E（替代口径）：小程序 11 页 × 三套风格逐页走查（自动化部分）；真实页面 + 真实 store/api/http，uni 为桩
// 视觉/真机行为见人工验证清单。溯源：AC-083-01/04、AC-087-03（自动化部分）、AC-074-01
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it } from 'vitest'
import { mountPage } from './helpers.js'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const pagesJson = JSON.parse(fs.readFileSync(path.join(ROOT, 'pages.json'), 'utf8'))
const modules = import.meta.glob('../pages/**/*.vue')

const ME = { profile: { id: 1, nickname: '张三', phone: '138****0000' }, identities: { labels: ['户主'], committee: { position: 'CHAIR' }, units: [{ id: 1 }] } }

beforeEach(() => {
  uni.request.mockImplementation(({ url, success }) => {
    const p = url.replace(/^\/api\/v1/, '')
    if (p === '/me') return success({ statusCode: 200, data: ME })
    if (p === '/me/theme') return success({ statusCode: 200, data: { theme: null } })
    if (/^\/(resolutions|polls)\/\d+$/.test(p)) return success({ statusCode: 200, data: { id: 1, title: '示例', status: 'OPEN', questions: [], options: [] } })
    return success({ statusCode: 200, data: { results: [], count: 0 } })
  })
})

describe('TC-E2E-202 小程序 11 页 × 三套风格逐页走查（AC-083-01/04 自动化部分）', () => {
  it('pages.json 的 11 个页面都套 ThemeRoot：theme-<key> 类、CSS 变量、文本与风格无关、无内联颜色', async () => {
    const pages = pagesJson.pages.map((p) => p.path)
    expect(pages).toHaveLength(11)
    const bad = []
    const texts = {}
    for (const page of pages) {
      const mod = modules[`../${page}.vue`]
      expect(mod, page).toBeTruthy()
      const component = (await mod()).default
      texts[page] = {}
      for (const key of ['neon', 'bento', 'terminal']) {
        uni.setStorageSync('ocap_theme', key)
        const { wrapper } = await mountPage(component, { query: { id: '1' } })
        const root = wrapper.find('.theme-root')
        if (!root.exists() || !root.classes().includes(`theme-${key}`)) bad.push(`${page} ${key}: 缺少 theme-${key}`)
        else if (!root.attributes('style')?.includes('--bg:')) bad.push(`${page} ${key}: 未注入 CSS 变量`)
        const html = wrapper.html()
        const inline = [...html.matchAll(/style="([^"]*)"/g)].map((m) => m[1]).filter((s) => /#[0-9a-fA-F]{3,8}\b|rgba?\(/.test(s) && !s.startsWith('--bg:'))
        // 风格选择器色块（我的页）是数据驱动的内联背景，豁免
        const nonSwatch = page.includes('/me/') ? [] : inline
        if (nonSwatch.length) bad.push(`${page} ${key}: 内联颜色 ${nonSwatch.join('|')}`)
        const clone = wrapper.element.cloneNode(true)
        clone.querySelectorAll('.theme-option').forEach((n) => n.remove())
        texts[page][key] = clone.textContent.replace(/\s+/g, ' ').trim()
        wrapper.unmount()
      }
    }
    expect(bad).toEqual([])
    expect(pages.filter((p) => new Set(Object.values(texts[p])).size !== 1)).toEqual([])
    expect(pages.filter((p) => texts[p].bento.length === 0)).toEqual([])
  })
})
