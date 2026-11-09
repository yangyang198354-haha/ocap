// MOD-027：风格体系守护测试（US-074/076/078/079/080/082/086/088；ADR-027/029/030）
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { THEMES, DEFAULT_THEME } from '@/theme/generated/registry'
import { useThemeStore } from '@/theme/store'
import ThemePicker from '@/theme/ThemePicker.vue'
import ElementPlus from 'element-plus'
import { run } from '../../scripts/themes/build.mjs'

const { http } = mocked
const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src')
const ROOT = path.resolve(SRC, '../..')

function vueFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) return e.name === 'generated' ? [] : vueFiles(p)
    return p.endsWith('.vue') ? [p] : []
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  document.documentElement.classList.remove('dark')
  setActivePinia(createPinia())
})

describe('页面不含颜色字面量（ADR-029；AC-080-02）', () => {
  it('frontend/src 下 .vue 文件无十六进制 / rgb() / hsl() 颜色字面量', () => {
    const bad = []
    for (const file of vueFiles(SRC)) {
      const text = fs.readFileSync(file, 'utf8')
      const hit = text.match(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/g)
      if (hit) bad.push(`${path.relative(SRC, file)}: ${hit.join(',')}`)
    }
    expect(bad).toEqual([])
  })
})

describe('风格注册表（US-074/US-075）', () => {
  it('恰好 3 套，名称与顺序为 霓虹玻璃 / 极光 Bento / 赛博终端，默认 bento', () => {
    expect(THEMES.map((t) => t.name)).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端'])
    expect(THEMES.map((t) => t.key)).toEqual(['neon', 'bento', 'terminal'])
    expect(THEMES.map((t) => t.scheme)).toEqual(['dark', 'light', 'dark'])
    expect(DEFAULT_THEME).toBe('bento')
    for (const t of THEMES) expect(t.swatch).toHaveLength(3)
  })
})

describe('ThemeStore 优先级（ADR-027 六条）', () => {
  it('1 设备记忆合法 → 应用；缺失 / 格式非法 / 未注册 → bento', () => {
    const store = useThemeStore()
    localStorage.setItem('ocap_theme', 'terminal')
    store.initFromDevice()
    expect(store.current).toBe('terminal')
    expect(document.documentElement.getAttribute('data-theme')).toBe('terminal')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    for (const bad of ['', 'Neon', 'retired-style', 'a b']) {
      localStorage.setItem('ocap_theme', bad)
      store.initFromDevice()
      expect(store.current).toBe('bento')
    }
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('3 账号值权威：有效 → 应用并写回；null → bento 并写回（不沿用他人记忆，AC-078-03）', async () => {
    const store = useThemeStore()
    localStorage.setItem('ocap_theme', 'terminal')
    http.get.mockResolvedValueOnce({ theme: 'neon' })
    await store.reconcileAfterLogin()
    expect(http.get).toHaveBeenCalledWith('/me/theme', { params: undefined })
    expect(store.current).toBe('neon')
    expect(localStorage.getItem('ocap_theme')).toBe('neon')
    http.get.mockResolvedValueOnce({ theme: null })
    await store.reconcileAfterLogin()
    expect(store.current).toBe('bento')
    expect(localStorage.getItem('ocap_theme')).toBe('bento')
  })

  it('3 账号值已下线 → 回退 bento，不写库（AC-086-01）', async () => {
    const store = useThemeStore()
    http.get.mockResolvedValueOnce({ theme: 'retired' })
    await store.reconcileAfterLogin()
    expect(store.current).toBe('bento')
    expect(http.put).not.toHaveBeenCalled()
  })

  it('3 读取失败 → 保持当前且不清空设备记忆（AC-090-03）', async () => {
    const store = useThemeStore()
    localStorage.setItem('ocap_theme', 'neon')
    store.initFromDevice()
    http.get.mockRejectedValueOnce(new Error('timeout'))
    await store.reconcileAfterLogin()
    expect(store.current).toBe('neon')
    expect(localStorage.getItem('ocap_theme')).toBe('neon')
  })

  it('5 点选：乐观应用 + PUT /me/theme {theme}；失败回滚并抛出（AC-076-03）', async () => {
    const store = useThemeStore()
    http.put.mockResolvedValueOnce({ theme: 'neon' })
    await store.select('neon')
    expect(http.put).toHaveBeenCalledWith('/me/theme', { theme: 'neon' })
    expect(store.current).toBe('neon')
    http.put.mockRejectedValueOnce(new Error('offline'))
    await expect(store.select('terminal')).rejects.toThrow()
    expect(store.current).toBe('neon')
    expect(localStorage.getItem('ocap_theme')).toBe('neon')
    expect(document.documentElement.getAttribute('data-theme')).toBe('neon')
  })

  it('1 管理端固定 bento，不读写设备记忆（AC-082-02）', () => {
    const store = useThemeStore()
    localStorage.setItem('ocap_theme', 'terminal')
    store.initFromDevice()
    store.forAdminRoute()
    expect(document.documentElement.getAttribute('data-theme')).toBe('bento')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    store.initFromDevice()
    expect(store.current).toBe('terminal')
  })
})

describe('ThemePicker（AC-074-01、AC-076-01/03）', () => {
  function mountPicker() {
    return mount(ThemePicker, { global: { plugins: [ElementPlus] } })
  }
  it('渲染 3 个选项，当前项被选中，点击后切换', async () => {
    const wrapper = mountPicker()
    expect(wrapper.findAll('[role=radio]')).toHaveLength(3)
    expect(wrapper.find('[data-theme-key=bento]').attributes('aria-checked')).toBe('true')
    http.put.mockResolvedValueOnce({ theme: 'terminal' })
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-theme-key=terminal]').attributes('aria-checked')).toBe('true')
    expect(document.documentElement.getAttribute('data-theme')).toBe('terminal')
  })
  it('保存失败回到保存前的风格', async () => {
    const wrapper = mountPicker()
    http.put.mockRejectedValueOnce(new Error('offline'))
    await wrapper.find('[data-theme-key=neon]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-theme-key=bento]').attributes('aria-checked')).toBe('true')
  })
})

describe('新增风格不改业务页面（AC-080-01/03）', () => {
  it('合规的测试风格 D 出现在生成的注册表；缺字段的不出现且给出可定位错误', () => {
    const tmp = fs.mkdtempSync(path.join(fs.realpathSync(process.env.TMPDIR || '/tmp'), 'themes-'))
    const copy = (name) => fs.copyFileSync(path.join(ROOT, 'themes', name), path.join(tmp, name))
    ;['neon', 'bento', 'terminal'].forEach((k) => copy(`${k}.theme.json`))
    const base = JSON.parse(fs.readFileSync(path.join(ROOT, 'themes/neon.theme.json'), 'utf8'))
    fs.writeFileSync(path.join(tmp, 'testd.theme.json'), JSON.stringify({ ...base, key: 'testd', name: '测试风格 D', order: 9 }))
    const broken = { ...base, key: 'broken', name: '坏风格', order: 10, tokens: { ...base.tokens } }
    delete broken.tokens.accent
    fs.writeFileSync(path.join(tmp, 'broken.theme.json'), JSON.stringify(broken))
    const { outputs, errors } = run(tmp)
    const registry = outputs['frontend/src/theme/generated/registry.js']
    expect(registry).toContain('测试风格 D')
    expect(registry).not.toContain('坏风格')
    expect(outputs['miniprogram/theme/generated/registry.js']).toContain('测试风格 D')
    expect(errors.join('\n')).toMatch(/themes\/broken\.theme\.json:tokens\.accent: 缺少必填项/)
    fs.rmSync(tmp, { recursive: true, force: true })
  })
})

describe('底部标签栏与导航高亮（AC-084-01、AC-085-01/02）', () => {
  async function mountBar(path) {
    const { createMemoryHistory, createRouter } = await import('vue-router')
    const BottomTabBar = (await import('@/portal/BottomTabBar.vue')).default
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }]
    })
    router.push(path)
    await router.isReady()
    return mount(BottomTabBar, { global: { plugins: [router] } })
  }
  it('恰好 5 项，顺序与文案固定，每项带图标', async () => {
    const wrapper = await mountBar('/')
    const links = wrapper.findAll('a')
    expect(links.map((a) => a.text())).toEqual(['首页', '决议', '投票', '报销', '我的'])
    expect(links.map((a) => a.attributes('href'))).toEqual(['/', '/resolutions', '/polls', '/claims', '/me'])
    expect(wrapper.findAll('svg')).toHaveLength(5)
  })
  it('决议详情页仅高亮“决议”；切到投票页高亮项数量恒为 1', async () => {
    let wrapper = await mountBar('/resolutions/12')
    expect(wrapper.findAll('a.is-active').map((a) => a.text())).toEqual(['决议'])
    wrapper = await mountBar('/polls')
    expect(wrapper.findAll('a.is-active').map((a) => a.text())).toEqual(['投票'])
    wrapper = await mountBar('/')
    expect(wrapper.findAll('a.is-active').map((a) => a.text())).toEqual(['首页'])
  })
})
