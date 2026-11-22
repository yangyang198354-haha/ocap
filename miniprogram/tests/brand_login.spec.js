// ocap_brand_layout GROUP_D（MOD-131）：小程序品牌更名与登录页三版配图（MOD-129 / IFC-329，US-208、US-228）。
// 层级：integration（真实登录页 + 真实 store/api/http，uni.request 由带表的替身应答；样式文件做静态断言）。TC-UNIT-881 起。
// 限制：WXSS 在微信开发者工具/真机的实际渲染（渐变、多重阴影）jsdom 无法验证，见 e2e_test_report 人工验证清单。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountPage, requests, respondWith } from './helpers.js'
import Login from '../pages/login/index.vue'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const pagesJson = JSON.parse(read('miniprogram/pages.json'))
const KEYS = ['neon', 'bento', 'terminal']

beforeEach(() => {
  respondWith({})
  uni.reLaunch.mockClear()
  uni.showToast.mockClear()
})

describe('pages.json 标题（US-208）', () => {
  it('TC-UNIT-881 / AC-208-02：首页 navigationBarTitleText 与 globalStyle 均为 Cyber@红枫岭', () => {
    expect(pagesJson.pages[0].path).toBe('pages/index/index')
    expect(pagesJson.pages[0].style.navigationBarTitleText).toBe('Cyber@红枫岭')
    expect(pagesJson.globalStyle.navigationBarTitleText).toBe('Cyber@红枫岭')
  })

  it('TC-UNIT-882 / AC-208-02：tabBar 4 项文案与其余页面功能名不变（只改首页与全局标题）', () => {
    expect(pagesJson.tabBar.list.map((t) => t.text)).toEqual(['首页', '决议', '投票', '我的'])
    const titleOf = (p) => pagesJson.pages.find((x) => x.path === p).style.navigationBarTitleText
    expect(titleOf('pages/login/index')).toBe('登录')
    expect(titleOf('pages/resolutions/index')).toBe('决议')
    expect(titleOf('pages/polls/index')).toBe('投票/调查')
    expect(titleOf('pages/claims/index')).toBe('报销/备用金')
    expect(titleOf('pages/me/index')).toBe('我的')
    expect(pagesJson.pages).toHaveLength(18)
    // 其余页面标题没有被误改为品牌名
    const branded = pagesJson.pages.filter((p) => p.style.navigationBarTitleText.includes('Cyber@'))
    expect(branded.map((p) => p.path)).toEqual(['pages/index/index'])
  })

  it('TC-UNIT-883 / REQ-NFUNC-041、AC-223-02：小程序源码用户可见处无旧产品名"业主委员会 · 登录"/"业主委员会"标题（manifest 描述不在本批范围，保持原样）', () => {
    expect(JSON.stringify(pagesJson)).not.toMatch(/业主委员会/)
    expect(read('miniprogram/pages/login/index.vue')).not.toContain('业主委员会')
    expect(read('miniprogram/manifest.json')).toContain('"description": "业主委员会小程序"')
  })
})

describe('登录页品牌头与配图（US-208、US-228）', () => {
  it('TC-UNIT-884 / AC-208-01、AC-228-01：三种风格下页面标题含"Cyber@红枫岭"，不再出现"业主委员会 · 登录"；子标题"登录"', async () => {
    for (const key of KEYS) {
      uni.setStorageSync('ocap_theme', key)
      const { wrapper } = await mountPage(Login, { token: '' })
      expect(wrapper.find('.auth-brand-name').text(), key).toBe('Cyber@红枫岭')
      expect(wrapper.find('.auth-brand-sub').text(), key).toBe('登录')
      expect(wrapper.text(), key).not.toContain('业主委员会')
      expect(wrapper.find('.brand-mark').exists(), key).toBe(true)
      wrapper.unmount()
    }
  })

  it('TC-UNIT-885 / AC-228-01：三种风格各渲染在对应 theme-<key> 根容器下，配图为 4 个空 view（art-a~d），无文本', async () => {
    for (const key of KEYS) {
      uni.setStorageSync('ocap_theme', key)
      const { wrapper } = await mountPage(Login, { token: '' })
      const root = wrapper.find('.theme-root')
      expect(root.classes(), key).toContain(`theme-${key}`)
      const art = root.find('.auth-art')
      expect(art.exists(), key).toBe(true)
      expect(art.attributes('aria-hidden')).toBe('true')
      expect(art.findAll('view').map((v) => v.classes()[0]), key).toEqual(['art-a', 'art-b', 'art-c', 'art-d'])
      expect(art.text(), key).toBe('')
      wrapper.unmount()
    }
  })

  it('TC-UNIT-886 / AC-228-02：无风格记忆（或记忆已下线）显示 bento 版；登录页没有风格入口', async () => {
    let { wrapper } = await mountPage(Login, { token: '' })
    expect(wrapper.find('.theme-root').classes()).toContain('theme-bento')
    expect(wrapper.find('.theme-option').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('界面风格')
    wrapper.unmount()
    uni.setStorageSync('ocap_theme', 'retired-d')
    ;({ wrapper } = await mountPage(Login, { token: '' }))
    expect(wrapper.find('.theme-root').classes()).toContain('theme-bento')
    expect(wrapper.find('[data-theme-key]').exists()).toBe(false)
  })

  it('TC-UNIT-887 / AC-228-01：登录页模板与样式无颜色字面量（颜色全取 CSS 变量）、无内联颜色、无远程字体/资源', () => {
    const src = read('miniprogram/pages/login/index.vue')
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/)
    expect(src).not.toMatch(/style="[^"]*(color|background|border-color|box-shadow)/i)
    expect(src).not.toMatch(/@font-face|url\(|https?:\/\//)
  })

  it('TC-UNIT-888 / AC-208-01、AC-228-03：验证码登录、密码登录、微信一键登录三个入口仍在', async () => {
    const { wrapper } = await mountPage(Login, { token: '' })
    const buttons = wrapper.findAll('button').map((b) => b.text())
    expect(buttons).toContain('验证码登录')
    expect(buttons).toContain('密码登录')
    expect(buttons).toContain('微信一键登录')
    expect(wrapper.findAll('button').filter((b) => b.text() === '登录')).toHaveLength(1) // 当前模式的提交按钮
    await wrapper.findAll('button').find((b) => b.text() === '密码登录').trigger('click')
    expect(wrapper.find('input[placeholder="账号 / 手机号"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="密码"]').exists()).toBe(true)
  })

  it('TC-UNIT-889 / AC-208-03：未注册手机号提示语原样保留（不因改名而改变）', async () => {
    const { wrapper } = await mountPage(Login, { token: '' })
    expect(wrapper.text()).toContain('未注册的手机号不会自动创建账号，请先在 Web 端注册，或使用微信一键登录。')
  })

  it('TC-UNIT-890 / AC-228-03：登录请求路径与字段不变——验证码 POST /auth/login/code {phone,code,client}、密码 POST /auth/login/password {identifier,password,client}、微信 POST /auth/wechat/miniapp {code}', async () => {
    respondWith({
      'POST /auth/login/code': { token: 'T1', is_new: false },
      'POST /auth/login/password': { token: 'T2', is_new: false },
      'POST /auth/wechat/miniapp': { token: 'T3', is_new: false },
      'GET /me': { profile: { id: 1, nickname: 'u' }, identities: { labels: ['游客'] } },
      'GET /me/theme': { theme: null }
    })
    const { wrapper } = await mountPage(Login, { token: '' })
    wrapper.vm.phone = '13800000000'
    wrapper.vm.code = '123456'
    await wrapper.vm.loginCode()
    wrapper.vm.identifier = 'alice'
    wrapper.vm.password = 'Ocap2026pass'
    await wrapper.vm.loginPassword()
    uni.login = vi.fn(({ success }) => success({ code: 'WXCODE' }))
    wrapper.vm.loginWechat()
    await flushPromises()
    const posts = requests().filter((r) => r.method === 'POST')
    expect(posts.find((r) => r.path === '/auth/login/code').data).toEqual({ phone: '13800000000', code: '123456', client: 'miniapp' })
    expect(posts.find((r) => r.path === '/auth/login/password').data).toEqual({ identifier: 'alice', password: 'Ocap2026pass', client: 'miniapp' })
    expect(posts.find((r) => r.path === '/auth/wechat/miniapp').data).toEqual({ code: 'WXCODE' })
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/index/index' })
  })

  it('TC-UNIT-891 / AC-228-03：登录失败（密码错误）显示服务端文案，不进入首页', async () => {
    uni.request.mockImplementation(({ url, success }) => {
      if (url.endsWith('/auth/login/password')) return success({ statusCode: 401, data: { code: 'LOGIN_FAILED', message: '账号或密码错误' } })
      return success({ statusCode: 404, data: { message: url } })
    })
    const { wrapper } = await mountPage(Login, { token: '' })
    wrapper.vm.identifier = 'alice'
    wrapper.vm.password = 'bad'
    await wrapper.vm.loginPassword()
    await flushPromises()
    expect(uni.showToast).toHaveBeenCalledWith(expect.objectContaining({ title: '账号或密码错误' }))
    // 401 时 http.js 会回登录页（reLaunch 到 /pages/login/index），但绝不会进入首页或资料设置页
    expect(uni.reLaunch).not.toHaveBeenCalledWith({ url: '/pages/index/index' })
    expect(uni.reLaunch).not.toHaveBeenCalledWith({ url: '/pages/profile-setup/index' })
  })
})

describe('三版 CSS 配图（themes/*.mp.css 与生成的 themes.scss）', () => {
  const SCSS = read('miniprogram/theme/generated/themes.scss')

  it('TC-UNIT-892 / AC-228-01：每套风格的 .mp.css 都定义 .auth-art 与 .art-a~.art-d，选择器均以 .theme-<key> 开头，并已进入生成物 themes.scss', () => {
    for (const key of KEYS) {
      const css = read(`themes/${key}.mp.css`)
      for (const part of ['.auth-art', '.auth-art .art-a', '.auth-art .art-b', '.auth-art .art-c', '.auth-art .art-d']) {
        expect(css, `${key} ${part}`).toContain(`.theme-${key} ${part}`)
        expect(SCSS, `scss ${key} ${part}`).toContain(`.theme-${key} ${part}`)
      }
      const selectors = css.replace(/\/\*[\s\S]*?\*\//g, '').split('}').map((r) => r.split('{')[0].trim()).filter((s) => s.includes('.auth-art'))
      for (const s of selectors) expect(s.startsWith(`.theme-${key}`), s).toBe(true)
    }
  })

  it('TC-UNIT-893 / ADR-032、AC-228-01：配图只用 CSS（渐变/边框/阴影/定位）——不用 backdrop-filter、SVG/url() 背景、循环动画与远程资源', () => {
    for (const key of KEYS) {
      const rules = read(`themes/${key}.mp.css`).replace(/\/\*[\s\S]*?\*\//g, '').split('}').filter((r) => r.includes('.auth-art'))
      expect(rules.length, key).toBeGreaterThanOrEqual(5)
      for (const r of rules) {
        expect(r, key).not.toMatch(/backdrop-filter/)
        expect(r, key).not.toMatch(/url\(/)
        expect(r, key).not.toMatch(/animation|@keyframes/)
        expect(r, key).not.toMatch(/https?:\/\//)
      }
    }
  })

  it('TC-UNIT-894 / AC-209-05(1)（小程序侧）：三版各含至少 1 类科技视觉元素——neon 网格+发光描边、bento 光晕/点阵、terminal 扫描线+发光边框+等宽字形', () => {
    const css = (key) => read(`themes/${key}.mp.css`)
    expect(css('neon')).toMatch(/linear-gradient\(var\(--accent\) 1px/) // 网格线条
    expect(css('neon')).toMatch(/box-shadow:\s*0 0 \d+rpx var\(--accent-2\)/) // 发光描边
    expect(css('bento')).toMatch(/radial-gradient\(/) // 点阵/光晕
    expect(css('terminal')).toMatch(/repeating-linear-gradient\(/) // 扫描线
    expect(css('terminal')).toMatch(/font-family:\s*var\(--mono\)/) // 等宽字形装饰
    expect(css('terminal')).toMatch(/box-shadow:/)
  })

  it('TC-UNIT-895 / AC-228-01：三版配图互不相同（构图不同）', () => {
    const art = (key) => read(`themes/${key}.mp.css`).split('\n').filter((l) => l.includes('.auth-art')).map((l) => l.replace(`.theme-${key}`, '')).join('\n')
    expect(new Set(KEYS.map(art)).size).toBe(3)
  })
})
