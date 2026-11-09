// PHASE_09 E2E（替代口径）：新增“测试风格 D”只加风格定义、不改业务页面，即出现在个人中心并可全站应用
// 注册表由 scripts/themes/build.mjs 对“三套 + 测试风格 D”的临时目录实际生成后注入（vi.mock），其余全部为真实模块。
// 溯源：AC-080-01、AC-080-02、AC-080-03
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('@/theme/generated/registry', async () => {
  const fs = await import('node:fs')
  const os = await import('node:os')
  const path = await import('node:path')
  const { run } = await import('../../scripts/themes/build.mjs')
  const root = path.resolve(process.cwd(), '..')
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-d-'))
  for (const k of ['neon', 'bento', 'terminal']) fs.copyFileSync(path.join(root, `themes/${k}.theme.json`), path.join(tmp, `${k}.theme.json`))
  const base = JSON.parse(fs.readFileSync(path.join(root, 'themes/terminal.theme.json'), 'utf8'))
  fs.writeFileSync(path.join(tmp, 'testd.theme.json'), JSON.stringify({ ...base, key: 'testd', name: '测试风格 D', order: 9 }))
  const { outputs, errors } = run(tmp)
  fs.rmSync(tmp, { recursive: true, force: true })
  const text = outputs['frontend/src/theme/generated/registry.js']
  const THEMES = JSON.parse(text.match(/export const THEMES = (\[[\s\S]*?\n\])\n/)[1])
  globalThis.__QA_D_ERRORS__ = errors
  globalThis.__QA_D_CSS__ = outputs['frontend/src/theme/generated/themes.css']
  return { THEMES, DEFAULT_THEME: 'bento' }
})

import App from '@/App.vue'
import router from '@/router'

const { http } = mocked
const html = () => document.documentElement
const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src')
vi.setConfig({ testTimeout: 60000 })

beforeEach(async () => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
  html().removeAttribute('data-theme')
  let saved = null
  http.get.mockImplementation(async (url) => {
    if (url === '/me/theme') return { theme: saved }
    if (url === '/me') return { profile: { id: 1, nickname: 'u' }, identities: { is_guest: false, units: [], committee: null, labels: ['户主'] } }
    if (url === '/me/profile') return { nickname: 'u' }
    return { results: [] }
  })
  http.put.mockImplementation(async (url, body) => { saved = body.theme; return { theme: body.theme } })
})

describe('TC-E2E-103 新增测试风格 D（AC-080-01/02/03）', () => {
  it('个人中心列表由 3 变 4，含“测试风格 D”；选择后全站应用该风格；业务页面源码零改动（无 testd 字样）', async () => {
    expect(globalThis.__QA_D_ERRORS__).toEqual([])
    expect(globalThis.__QA_D_CSS__).toContain('html[data-theme="testd"]')
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(App, { global: { plugins: [pinia, router, ElementPlus] }, attachTo: document.body })
    await router.push('/me')
    await flushPromises()
    await flushPromises()
    const names = wrapper.findAll('[role=radio] .theme-name').map((n) => n.text())
    expect(names).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端', '测试风格 D'])
    await wrapper.find('[data-theme-key=testd]').trigger('click')
    await flushPromises()
    expect(http.put).toHaveBeenCalledWith('/me/theme', { theme: 'testd' })
    for (const p of ['/resolutions', '/polls', '/claims', '/units', '/tasks', '/reports']) {
      await router.push(p)
      await flushPromises()
      expect(html().getAttribute('data-theme'), p).toBe('testd')
    }
    // 业务页面文件不含该风格的任何痕迹
    const pages = ['portal', 'admin'].flatMap((d) => fs.readdirSync(path.join(SRC, d)).filter((f) => f.endsWith('.vue')).map((f) => path.join(SRC, d, f)))
    expect(pages.length).toBeGreaterThanOrEqual(24)
    for (const f of pages) expect(fs.readFileSync(f, 'utf8'), f).not.toMatch(/testd|测试风格/)
    wrapper.unmount()
  })
})
