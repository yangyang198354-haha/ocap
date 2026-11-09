// MOD-029：小程序风格体系（US-074/077/078/079/083/086；ADR-027/028）。uni 为桩，不代表微信真机行为。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { mountPage, respondWith, requests } from './helpers.js'
import { THEMES } from '@/theme/generated/registry'
import { useThemeStore } from '@/store/theme'
import ThemeRoot from '../components/ThemeRoot.vue'
import Me from '../pages/me/index.vue'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

function vueFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) return vueFiles(p)
    return p.endsWith('.vue') ? [p] : []
  })
}

describe('页面不含颜色字面量（ADR-029）', () => {
  it('pages 与 components 下 .vue 无颜色字面量（App.vue 基础样式表与生成物豁免）', () => {
    const bad = []
    for (const file of [...vueFiles(path.join(ROOT, 'pages')), ...vueFiles(path.join(ROOT, 'components'))]) {
      const hit = fs.readFileSync(file, 'utf8').match(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/g)
      if (hit) bad.push(`${path.relative(ROOT, file)}: ${hit.join(',')}`)
    }
    expect(bad).toEqual([])
  })
  it('11 个页面根节点均套 ThemeRoot', () => {
    const pages = vueFiles(path.join(ROOT, 'pages'))
    expect(pages).toHaveLength(11)
    for (const file of pages) expect(fs.readFileSync(file, 'utf8'), file).toContain('<ThemeRoot>')
  })
})

describe('风格 store', () => {
  it('注册表 3 套；设备记忆合法 → 首帧即用；非法/下线 → bento', () => {
    expect(THEMES.map((t) => t.name)).toEqual(['霓虹玻璃', '极光 Bento', '赛博终端'])
    setActivePinia(createPinia())
    expect(useThemeStore().current).toBe('bento')
    uni.setStorageSync('ocap_theme', 'terminal')
    setActivePinia(createPinia())
    expect(useThemeStore().current).toBe('terminal')
    uni.setStorageSync('ocap_theme', 'retired')
    setActivePinia(createPinia())
    expect(useThemeStore().current).toBe('bento')
  })

  it('reconcileAfterLogin：账号值权威；null → bento；失败保持当前（AC-077-02、AC-078-03）', async () => {
    uni.setStorageSync('ocap_theme', 'terminal')
    setActivePinia(createPinia())
    const store = useThemeStore()
    respondWith({ 'GET /me/theme': { theme: 'neon' } })
    await store.reconcileAfterLogin()
    expect(store.current).toBe('neon')
    expect(uni.getStorageSync('ocap_theme')).toBe('neon')
    respondWith({ 'GET /me/theme': { theme: null } })
    await store.reconcileAfterLogin()
    expect(store.current).toBe('bento')
    respondWith({})
    uni.setStorageSync('ocap_theme', 'neon')
    store.current = 'neon'
    await store.reconcileAfterLogin()
    expect(store.current).toBe('neon')
  })

  it('applyNative 调用 setTabBarStyle / setNavigationBarColor（AC-077-01）', () => {
    setActivePinia(createPinia())
    const store = useThemeStore()
    store.applyNative('neon')
    expect(uni.setTabBarStyle).toHaveBeenCalledWith(expect.objectContaining({ selectedColor: '#A996FF', backgroundColor: '#0B0C16' }))
    expect(uni.setNavigationBarColor).toHaveBeenCalledWith(expect.objectContaining({ frontColor: '#ffffff' }))
  })
})

describe('ThemeRoot 变量注入', () => {
  it('根节点带 theme-<key> 类与 CSS 变量，随风格变化', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(ThemeRoot, { global: { plugins: [pinia] }, slots: { default: '<view class="x" />' } })
    expect(wrapper.classes()).toContain('theme-bento')
    expect(wrapper.attributes('style')).toMatch(/--bg:\s*#F3F4FA/)
    useThemeStore().current = 'terminal'
    await flushPromises()
    expect(wrapper.classes()).toContain('theme-terminal')
    expect(wrapper.attributes('style')).toMatch(/--accent:\s*#C6FF3D/)
    expect(wrapper.find('.x').exists()).toBe(true)
  })
})

describe('“我的”页风格选择（AC-077-01/04）', () => {
  const ME = { profile: { id: 1, nickname: '张三', phone: '138****0000' }, identities: { labels: ['户主'] } }
  it('列出全部启用风格；点选后 PUT /me/theme {theme} 并切换', async () => {
    respondWith({ 'GET /me': ME, 'GET /ledger/reports': { results: [] }, 'PUT /me/theme': { theme: 'neon' } })
    const { wrapper } = await mountPage(Me)
    expect(wrapper.findAll('.theme-option')).toHaveLength(3)
    await wrapper.find('[data-theme-key=neon]').trigger('click')
    await flushPromises()
    expect(requests().find((r) => r.method === 'PUT' && r.path === '/me/theme').data).toEqual({ theme: 'neon' })
    expect(wrapper.find('[data-theme-key=neon]').classes()).toContain('is-selected')
  })
  it('保存失败：回滚并 toast“保存失败”', async () => {
    respondWith({ 'GET /me': ME, 'GET /ledger/reports': { results: [] } })
    const { wrapper } = await mountPage(Me)
    await wrapper.find('[data-theme-key=terminal]').trigger('click')
    await flushPromises()
    expect(uni.showToast).toHaveBeenCalledWith(expect.objectContaining({ title: '保存失败' }))
    expect(wrapper.find('[data-theme-key=bento]').classes()).toContain('is-selected')
  })
})
