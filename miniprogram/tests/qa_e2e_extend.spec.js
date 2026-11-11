// PHASE_09 E2E（替代口径）：新增“测试风格 D”只加风格定义，小程序“我的”页即出现 4 项（AC-080-01/02）
import { describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

vi.mock('@/theme/generated/registry', async () => {
  const fs = await import('node:fs')
  const os = await import('node:os')
  const path = await import('node:path')
  const { run } = await import('../../scripts/themes/build.mjs')
  const root = path.resolve(process.cwd(), '..')
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-dm-'))
  for (const k of ['neon', 'bento', 'terminal']) fs.copyFileSync(path.join(root, `themes/${k}.theme.json`), path.join(tmp, `${k}.theme.json`))
  const base = JSON.parse(fs.readFileSync(path.join(root, 'themes/terminal.theme.json'), 'utf8'))
  fs.writeFileSync(path.join(tmp, 'testd.theme.json'), JSON.stringify({ ...base, key: 'testd', name: '测试风格 D', order: 9 }))
  const { outputs } = run(tmp)
  fs.rmSync(tmp, { recursive: true, force: true })
  const text = outputs['miniprogram/theme/generated/registry.js']
  const THEMES = JSON.parse(text.match(/export const THEMES = (\[[\s\S]*?\n\])\n/)[1])
  return { THEMES, DEFAULT_THEME: 'bento' }
})

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { mountPage, respondWith, requests } from './helpers.js'
import Me from '../pages/me/index.vue'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const ME = { profile: { id: 1, nickname: '张三', phone: '138****0000' }, identities: { labels: ['户主'] } }

describe('TC-E2E-203 小程序新增测试风格 D（AC-080-01/02）', () => {
  it('“我的”页列表由 3 变 4；选择 D 后 PUT /me/theme {theme:testd} 并应用 theme-testd；页面源码无该风格痕迹', async () => {
    respondWith({ 'GET /me': ME, 'GET /ledger/reports': { results: [] }, 'PUT /me/theme': (d) => ({ theme: d.theme }) })
    const { wrapper } = await mountPage(Me)
    expect(wrapper.findAll('.theme-option .theme-name').map((n) => n.text())).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端', '测试风格 D'])
    await wrapper.find('[data-theme-key=testd]').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'PUT').data).toEqual({ theme: 'testd' })
    expect(wrapper.find('.theme-root').classes()).toContain('theme-testd')
    const files = fs.readdirSync(path.join(ROOT, 'pages'), { recursive: true }).filter((f) => String(f).endsWith('.vue'))
    expect(files).toHaveLength(13)
    for (const f of files) expect(fs.readFileSync(path.join(ROOT, 'pages', String(f)), 'utf8'), String(f)).not.toMatch(/testd|测试风格/)
  })
})
