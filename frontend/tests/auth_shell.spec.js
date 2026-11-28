// ocap_brand_layout GROUP_D（MOD-131）：登录/注册/管理端登录品牌外壳 AuthShell 与三套配图（IFC-327）。
// 层级：integration（真实页面 + 真实风格 store + 真实 api.js，仅 mock HTTP 层）。TC-INT-861 起。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage } from './helpers.js'
import Login from '@/portal/Login.vue'
import Register from '@/portal/Register.vue'
import AdminLogin from '@/admin/AdminLogin.vue'
import NeonArt from '@/brand/art/NeonArt.vue'
import BentoArt from '@/brand/art/BentoArt.vue'
import TerminalArt from '@/brand/art/TerminalArt.vue'
import { artFor } from '@/brand/art'
import { THEMES } from '@/theme/generated/registry'
import { useThemeStore } from '@/theme/store'
import { useAdminThemeStore } from '@/theme/adminStore'
import { ADMIN_NAME_KEY } from '@/admin/adminSession'

const { http, adminHttp } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const flush = async () => { await flushPromises(); await new Promise((r) => setTimeout(r, 0)); await flushPromises() }
const artClass = (wrapper) => {
  const svg = wrapper.find('.auth-art svg')
  return svg.exists() ? (svg.classes()[0] || 'bento-art') : null
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset()
  localStorage.clear()
  document.body.innerHTML = ''
  document.documentElement.removeAttribute('data-theme')
})

describe('artFor 配图注册表（IFC-327）', () => {
  it('TC-INT-861 / AC-209-01：neon/bento/terminal 返回三个互不相同的组件', () => {
    expect(artFor('neon')).toBe(NeonArt)
    expect(artFor('bento')).toBe(BentoArt)
    expect(artFor('terminal')).toBe(TerminalArt)
    expect(new Set([artFor('neon'), artFor('bento'), artFor('terminal')]).size).toBe(3)
  })

  it('TC-INT-862 / AC-209-02：未知、缺失、非字符串的 key 回退 bento（与 DEFAULT_THEME 一致）', () => {
    for (const bad of ['retired-d', '', undefined, null, 42, {}]) expect(artFor(bad), String(bad)).toBe(BentoArt)
  })

  // IFC-327 契约"其他/缺失 → BentoArt"：原型链上的键名（__proto__、constructor、toString）不得被当成配图组件。
  // 现行实现 ARTS[themeKey] 会返回 Object.prototype / Object 函数（DEF-001，MINOR；经 AuthShell 取到的 key 已由 resolveKey 白名单过滤，当前不可达，但契约函数本身不满足）。
  it('TC-INT-874 / AC-209-02、IFC-327：原型链键名（__proto__、constructor、toString、hasOwnProperty）回退 bento', () => {
    for (const bad of ['__proto__', 'constructor', 'toString', 'hasOwnProperty']) expect(artFor(bad), bad).toBe(BentoArt)
  })
})

describe('三套风格各一版（AC-209-01、AC-209-02、AC-227-01）', () => {
  it('TC-INT-863 / AC-209-01：设备记忆分别为 neon/bento/terminal——/login 与 /register 共 6 个版本都含品牌名 h1 与 1 张配图，且 3 套配图结构互不相同', async () => {
    const seen = {}
    for (const key of ['neon', 'bento', 'terminal']) {
      for (const [name, page] of [['login', Login], ['register', Register]]) {
        document.body.innerHTML = ''
        localStorage.setItem('ocap_theme', key)
        const mounted = await mountPage(page)
        useThemeStore(mounted.pinia).initFromDevice()
        await flush()
        const w = mounted.wrapper
        expect(w.find('h1.auth-brand').text(), `${key}/${name}`).toBe('赛博@红枫岭')
        expect(w.findAll('.auth-art svg'), `${key}/${name}`).toHaveLength(1)
        expect(w.find('.auth-art').attributes('aria-hidden')).toBe('true')
        expect(w.find('.auth-brand').classes()).toContain('brand-wordmark')
        expect(w.find('h1 .brand-at').text()).toBe('@')
        if (name === 'login') expect(w.find('.auth-sub').exists()).toBe(false)
        else expect(w.find('.auth-sub').text()).toBe('手机号注册')
        ;(seen[key] ||= new Set()).add(artClass(w))
        seen[key].html = w.find('.auth-art').html()
        w.unmount()
      }
    }
    expect(artClass).toBeTruthy()
    const htmls = ['neon', 'bento', 'terminal'].map((k) => seen[k].html)
    expect(new Set(htmls).size).toBe(3)
    expect([...seen.neon][0]).toBe('neon-art')
    expect([...seen.terminal][0]).toBe('terminal-art')
  })

  it('TC-INT-864 / AC-209-02：无风格记忆或记忆值不在注册表中——/login 显示 bento 版；页面没有 [role=radio] 与"界面风格"入口', async () => {
    for (const saved of [null, 'retired-d']) {
      document.body.innerHTML = ''
      localStorage.clear()
      if (saved) localStorage.setItem('ocap_theme', saved)
      const mounted = await mountPage(Login)
      useThemeStore(mounted.pinia).initFromDevice()
      await flush()
      expect(useThemeStore(mounted.pinia).current).toBe('bento')
      expect(mounted.wrapper.find('.auth-art svg').classes()).not.toContain('neon-art')
      expect(mounted.wrapper.find('.auth-art svg').classes()).not.toContain('terminal-art')
      expect(mounted.wrapper.find('[role=radio]').exists()).toBe(false)
      expect(mounted.wrapper.text()).not.toContain('界面风格')
      expect(mounted.wrapper.find('.theme-picker, [data-theme-key]').exists()).toBe(false)
      mounted.wrapper.unmount()
    }
  })

  it('TC-INT-865 / AC-227-01、AC-227-02：管理端登录页读 ocap_admin_theme，不读 ocap_theme；无管理端记忆为 bento；无风格入口', async () => {
    localStorage.setItem('ocap_theme', 'terminal')
    localStorage.setItem('ocap_admin_theme', 'neon')
    let m = await mountPage(AdminLogin)
    useThemeStore(m.pinia).initFromDevice()
    useAdminThemeStore(m.pinia).initFromDevice()
    await flush()
    expect(m.wrapper.find('.auth-art svg').classes()).toContain('neon-art')
    expect(m.wrapper.find('h1.auth-brand').text()).toBe('赛博@红枫岭')
    expect(m.wrapper.find('.auth-sub').text()).toBe('管理后台登录')
    expect(m.wrapper.find('[role=radio]').exists()).toBe(false)
    m.wrapper.unmount()
    document.body.innerHTML = ''
    localStorage.removeItem('ocap_admin_theme')
    m = await mountPage(AdminLogin)
    useThemeStore(m.pinia).initFromDevice()
    useAdminThemeStore(m.pinia).initFromDevice()
    await flush()
    expect(m.wrapper.find('.auth-art svg').classes()).not.toContain('terminal-art') // 用户端记忆 terminal 不外溢
    expect(m.wrapper.find('.auth-art svg').classes()).not.toContain('neon-art')
    expect(localStorage.getItem('ocap_theme')).toBe('terminal')
    m.wrapper.unmount()
  })

  it('TC-INT-866 / AC-209-01：三套风格的页面背景与 Web 注册表色板第 3 色一致', () => {
    const swatchBg = Object.fromEntries(THEMES.map((t) => [t.key, t.swatch[2]]))
    expect(swatchBg).toEqual({ neon: '#0B101C', bento: '#F3F4FA', terminal: '#0C0F0D' })
    const css = read('frontend/src/theme/generated/themes.css')
    for (const [key, bg] of Object.entries(swatchBg)) {
      const block = css.match(new RegExp(`html\\[data-theme="${key}"\\]\\s*\\{([^}]*)\\}`))
      expect(block, key).toBeTruthy()
      expect(block[1], key).toMatch(new RegExp(`--bg:\\s*${bg}`, 'i'))
    }
    // AuthShell 背景取 --bg（语义变量，不写死颜色）
    expect(read('frontend/src/shared/style.css')).toMatch(/\.auth-shell\s*\{[^}]*background:\s*var\(--bg\)/)
  })

  it('TC-INT-867 / ADR-029：三个配图组件、AuthShell 与 BrandMark 的 .vue 内无颜色字面量，配图 <svg> 不含文本节点（装饰字符走 CSS）', () => {
    for (const f of ['NeonArt', 'BentoArt', 'TerminalArt']) {
      const src = read(`frontend/src/brand/art/${f}.vue`)
      expect(src, f).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/)
      expect(src.split('<script')[0], f).not.toMatch(/<text[\s>]/)
    }
    for (const f of ['AuthShell.vue', 'BrandMark.vue']) {
      expect(read(`frontend/src/brand/${f}`), f).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/)
    }
  })

  it('TC-INT-868：三套登录页只放一枚枫叶，霓虹在品牌区，极光和终端在表单区', async () => {
    const orders = []
    for (const key of ['neon', 'bento', 'terminal']) {
      document.body.innerHTML = ''
      localStorage.setItem('ocap_theme', key)
      const m = await mountPage(Login)
      useThemeStore(m.pinia).initFromDevice()
      await flush()
      const shell = m.wrapper.find('.auth-shell')
      orders.push([...shell.element.children].map((c) => c.className.split(' ')[0]))
      expect(shell.findAll('img.brand-mark'), key).toHaveLength(1)
      const brandArea = key === 'neon' ? '.auth-art' : '.auth-panel'
      expect(shell.find(`${brandArea} img.brand-mark`).exists(), key).toBe(true)
      expect(shell.find(`${brandArea} .brand-at`).text(), key).toBe('@')
      expect(m.wrapper.find('.auth-panel h1').text(), key).toBe('赛博@红枫岭')
      m.wrapper.unmount()
    }
    expect(orders).toEqual([['auth-art', 'auth-panel'], ['auth-art', 'auth-panel'], ['auth-art', 'auth-panel']])
  })
})

describe('表单字段与流程不变（AC-207-01、AC-207-02、AC-209-06、AC-227-03）', () => {
  it('TC-INT-869：/login 含三种登录方式和「用户注册」入口，无重复登录标题', async () => {
    const { wrapper } = await mountPage(Login)
    await flush()
    const tabs = wrapper.findAll('.el-tabs__item').map((t) => t.text())
    expect(tabs).toEqual(['验证码', '密码', '邮箱'])
    expect(wrapper.findAll('a').find((a) => a.text() === '用户注册').attributes('href')).toBe('/register')
    expect(wrapper.find('.auth-sub').exists()).toBe(false)
    expect(wrapper.text()).toContain('赛博@红枫岭')
    expect(wrapper.text()).not.toContain('业主委员会')
  })

  it('TC-INT-870 / AC-207-02：/register 含品牌名，"注册并登录"按钮与"返回登录"链接仍存在', async () => {
    const { wrapper } = await mountPage(Register)
    expect(wrapper.text()).toContain('赛博@红枫岭')
    expect(wrapper.findAll('button').some((b) => b.text().includes('注册并登录'))).toBe(true)
    expect(wrapper.findAll('a').find((a) => a.text() === '返回登录').attributes('href')).toBe('/login')
  })

  it('TC-INT-871 / AC-209-06：密码登录请求路径/方法/字段与改动前一致（POST /auth/login/password {identifier,password,remember_me}）', async () => {
    http.post.mockRejectedValue({ code: 'LOGIN_FAILED', message: '账号或密码错误' })
    vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper } = await mountPage(Login)
    wrapper.vm.form.identifier = 'alice'
    wrapper.vm.form.password = 'Ocap2026pass'
    await wrapper.vm.loginPassword()
    await flush()
    expect(http.post).toHaveBeenCalledWith('/auth/login/password', { identifier: 'alice', password: 'Ocap2026pass', remember_me: false })
    expect(ElMessage.error).toHaveBeenCalledWith('账号或密码错误')
  })

  it('TC-INT-872 / AC-227-03：管理端登录错误密码——提示与改动前一致（服务端文案），不保存令牌与账号名；保留"不支持记住我"提示；请求 POST /admin/auth/login {username,password}', async () => {
    adminHttp.post.mockRejectedValue({ code: 'LOGIN_FAILED', message: '账号或密码错误' })
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper } = await mountPage(AdminLogin)
    expect(wrapper.text()).toContain('管理后台登录不支持"记住我"。')
    await wrapper.find('input[placeholder="管理员账号"]').setValue('admin01')
    await wrapper.find('input[placeholder="密码"]').setValue('bad')
    await wrapper.findAll('button').find((b) => b.text() === '登录').trigger('click')
    await flush()
    expect(adminHttp.post).toHaveBeenCalledWith('/admin/auth/login', { username: 'admin01', password: 'bad' })
    expect(error).toHaveBeenCalledWith('账号或密码错误')
    expect(localStorage.getItem('ocap_admin_token')).toBeNull()
    expect(localStorage.getItem(ADMIN_NAME_KEY)).toBeNull()
  })

  it('TC-INT-873 / AC-226-01：管理端登录成功——保存令牌与账号名（admin.username），并按管理员账号偏好对账', async () => {
    adminHttp.post.mockResolvedValue({ token: 'atok', admin: { username: 'admin01' } })
    adminHttp.get.mockResolvedValue({ theme: 'terminal' })
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const { wrapper, router } = await mountPage(AdminLogin)
    await wrapper.find('input[placeholder="管理员账号"]').setValue('admin01')
    await wrapper.find('input[placeholder="密码"]').setValue('Ocap2026pass')
    await wrapper.findAll('button').find((b) => b.text() === '登录').trigger('click')
    await flush()
    expect(localStorage.getItem('ocap_admin_token')).toBe('atok')
    expect(localStorage.getItem(ADMIN_NAME_KEY)).toBe('admin01')
    expect(localStorage.getItem('ocap_admin_theme')).toBe('terminal')
    expect(localStorage.getItem('ocap_token')).toBeNull() // 用户端令牌不受影响（C-69）
    expect(router.currentRoute.value.path).toBe('/admin')
  })
})
