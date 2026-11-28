// ocap_brand_layout GROUP_D（MOD-131）：品牌更名与字体守护（REQ-FUNC-201/202/217、REQ-NFUNC-041、ADR-123）。
// 层级：unit（读源文件 + 轻量渲染，不依赖浏览器）。TC-UNIT-841 起。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { ADMIN_BRAND_TITLE, BRAND_NAME } from '@/brand/brand'
import BrandMark from '@/brand/BrandMark.vue'
import BrandWordmark from '@/brand/BrandWordmark.vue'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const walk = (dir, exts) => fs.readdirSync(path.join(ROOT, dir), { withFileTypes: true }).flatMap((e) =>
  e.isDirectory() ? walk(path.join(dir, e.name), exts) : (exts.some((x) => e.name.endsWith(x)) ? [path.join(dir, e.name)] : []))
const OLD_NAMES = /业主委员会\s*[·•]\s*(登录|管理后台)|<title>\s*业主委员会\s*<\/title>|navigationBarTitleText"\s*:\s*"业主委员会"/

describe('产品名常量与网页标题', () => {
  it('TC-UNIT-841 / C-67、AC-207-01：BRAND_NAME 字面为 赛博@红枫岭（@ 半角、无空格）；管理端标题为"赛博@红枫岭 · 管理后台"', () => {
    expect(BRAND_NAME).toBe('赛博@红枫岭')
    expect(BRAND_NAME).toMatch(/^赛博@红枫岭$/)
    expect(BRAND_NAME).not.toMatch(/\s|＠/)
    expect(ADMIN_BRAND_TITLE).toBe('赛博@红枫岭 · 管理后台')
  })

  it('TC-UNIT-842 / AC-207-03、AC-207-04：index.html 静态 <title> 为 赛博@红枫岭（用户端与管理端共用），且源码没有任何地方改写 document.title', () => {
    const html = read('frontend/index.html')
    expect(html.match(/<title>([^<]*)<\/title>/)[1]).toBe('赛博@红枫岭')
    expect((html.match(/<title>/g) || [])).toHaveLength(1)
    const offenders = walk('frontend/src', ['.vue', '.js']).filter((f) => /document\.title\s*=|useTitle|useHead|\.meta\.title/.test(fs.readFileSync(path.join(ROOT, f), 'utf8')))
    expect(offenders).toEqual([])
  })
})

describe('REQ-NFUNC-041：9 处用户可见产品名位置残留旧名为 0', () => {
  it('TC-UNIT-843 / AC-223-02：逐处核对 9 处——Web 登录页、注册页、网页标题、用户端品牌位、管理端品牌位、管理端登录页（经 AuthShell 取 BRAND_NAME）、小程序登录页、小程序首页标题、小程序全局标题', () => {
    const sites = {
      '登录页/注册页/管理端登录页（AuthShell h1）': () => /<h1[^>]*><BrandWordmark\s*\/><\/h1>/.test(read('frontend/src/brand/AuthShell.vue')),
      '登录页使用 AuthShell': () => read('frontend/src/portal/Login.vue').includes('<AuthShell surface="portal">'),
      '注册页使用 AuthShell': () => read('frontend/src/portal/Register.vue').includes('<AuthShell surface="portal" subtitle="手机号注册">'),
      '管理端登录页使用 AuthShell': () => read('frontend/src/admin/AdminLogin.vue').includes('<AuthShell surface="admin" subtitle="管理后台登录">'),
      '网页标题': () => read('frontend/index.html').includes('<title>赛博@红枫岭</title>'),
      '用户端品牌位': () => (read('frontend/src/portal/PortalLayout.vue').match(/<BrandWordmark\b/g) || []).length === 2,
      '管理端品牌位': () => read('frontend/src/admin/AdminLayout.vue').includes(':aria-label="ADMIN_BRAND_TITLE"'),
      '小程序登录页': () => read('miniprogram/pages/login/index.vue').includes('<text class="auth-brand-name">赛博@红枫岭</text>'),
      '小程序首页标题': () => JSON.parse(read('miniprogram/pages.json')).pages[0].style.navigationBarTitleText === '赛博@红枫岭',
      '小程序全局标题': () => JSON.parse(read('miniprogram/pages.json')).globalStyle.navigationBarTitleText === '赛博@红枫岭'
    }
    const failed = Object.entries(sites).filter(([, fn]) => !fn()).map(([name]) => name)
    expect(failed).toEqual([])
    expect(Object.keys(sites).length).toBeGreaterThanOrEqual(9)
  })

  it('保持品牌全文可读，只把 @ 放入强调样式', () => {
    const wordmark = mount(BrandWordmark)
    expect(wordmark.text()).toBe(BRAND_NAME)
    expect(wordmark.find('.brand-at').text()).toBe('@')
  })

  it('TC-UNIT-844 / AC-223-02、AC-207-01：全仓用户可见源码中旧产品名（"业主委员会 · 登录/管理后台"、<title>业主委员会</title>、小程序标题"业主委员会"）残留数 = 0', () => {
    const files = [
      ...walk('frontend/src', ['.vue', '.js', '.css']),
      'frontend/index.html', 'miniprogram/pages.json',
      ...walk('miniprogram/pages', ['.vue']), ...walk('miniprogram/components', ['.vue'])
    ]
    const hits = files.filter((f) => OLD_NAMES.test(read(f)))
    expect(hits).toEqual([])
    // 登录页不再出现旧标题
    expect(read('frontend/src/portal/Login.vue')).not.toContain('业主委员会')
    expect(read('miniprogram/pages/login/index.vue')).not.toContain('业主委员会')
  })

  it('TC-UNIT-845 / AC-208-02：范围边界——小程序 tabBar 4 项文案与功能页标题不变（首页/决议/投票/我的）', () => {
    const cfg = JSON.parse(read('miniprogram/pages.json'))
    expect(cfg.tabBar.list.map((t) => t.text)).toEqual(['首页', '决议', '投票', '我的'])
    const titleOf = (p) => cfg.pages.find((x) => x.path === p).style.navigationBarTitleText
    expect(titleOf('pages/resolutions/index')).toBe('决议')
    expect(titleOf('pages/polls/index')).toBe('投票/调查')
    expect(titleOf('pages/claims/index')).toBe('报销/备用金')
    expect(titleOf('pages/login/index')).toBe('登录')
  })
})

describe('品牌字体（AC-209-03、ADR-123）', () => {
  const css = read('frontend/src/brand/brand.css')
  const code = css.replace(/\/\*[\s\S]*?\*\//g, '')

  it('TC-UNIT-846 / AC-209-03：@font-face 含 font-display: swap，src 为随包相对路径且文件存在（woff2 魔数），font-family 只写 OcapBrand', () => {
    expect(code).toMatch(/@font-face\s*\{[^}]*font-family:\s*"OcapBrand"/)
    expect(code).toMatch(/font-display:\s*swap/)
    const src = code.match(/src:\s*url\(['"]?(\.\/fonts\/[^'")]+)['"]?\)\s*format\('woff2'\)/)
    expect(src, 'src 必须是随包相对路径').toBeTruthy()
    const file = path.join(ROOT, 'frontend/src/brand', src[1])
    expect(fs.existsSync(file)).toBe(true)
    expect(fs.readFileSync(file).subarray(0, 4).toString('latin1')).toBe('wOF2')
    expect(code).not.toMatch(/font-family:\s*[^;]*(Smiley|得意黑)/i) // OFL 保留字体名
    expect(fs.readFileSync(path.join(ROOT, 'frontend/src/brand/fonts/OFL.txt'), 'utf8')).toContain('SIL Open Font License')
  })

  it('TC-UNIT-847 / AC-209-03：字体加载失败/子集外字符回退系统字体——--brand-font 以 "OcapBrand" 开头并以 var(--font) 兜底；.brand-font 使用该变量', () => {
    expect(code).toMatch(/--brand-font:\s*"OcapBrand",\s*var\(--font\)\s*;/)
    expect(code).toMatch(/\.brand-font\s*\{\s*font-family:\s*var\(--brand-font\)\s*;?\s*\}/)
    // 系统字体栈 --font 在每个风格里都有定义（回退目标存在）
    const themes = read('frontend/src/theme/generated/themes.css')
    expect((themes.match(/--font:/g) || []).length).toBeGreaterThanOrEqual(3)
  })

  it('TC-UNIT-848 / AC-209-03、AC-228-01：全部 .vue/.css/index.html 不引用 CDN 域名，不含 http(s) 字体 url()，无 @import 远程样式；小程序登录页不加载远程字体', () => {
    const files = [...walk('frontend/src', ['.vue', '.css']), 'frontend/index.html', 'miniprogram/pages/login/index.vue', 'themes/neon.mp.css', 'themes/bento.mp.css', 'themes/terminal.mp.css']
    const bad = []
    for (const f of files) {
      const text = read(f)
      if (/fonts\.googleapis|fonts\.gstatic|cdn\.|unpkg\.com|jsdelivr/i.test(text)) bad.push(`${f}: CDN`)
      if (/url\(\s*['"]?(https?:)?\/\//i.test(text)) bad.push(`${f}: 远程 url()`)
      if (/@import\s+(url\()?['"]?(https?:)?\/\//i.test(text)) bad.push(`${f}: 远程 @import`)
      if (/<link[^>]+rel=["']stylesheet["'][^>]+href=["']https?:/i.test(text)) bad.push(`${f}: 远程 link`)
    }
    expect(bad).toEqual([])
    expect(read('miniprogram/pages/login/index.vue')).not.toMatch(/@font-face|loadFontFace/)
  })

  it('TC-UNIT-849 / ADR-123：brand.css 在 themes.css 之后引入；新中文品牌名使用系统字体', () => {
    const main = read('frontend/src/main.js')
    expect(main.indexOf("./theme/generated/themes.css")).toBeGreaterThan(-1)
    expect(main.indexOf("./brand/brand.css")).toBeGreaterThan(main.indexOf("./theme/generated/themes.css"))
    const users = walk('frontend/src', ['.vue']).filter((f) => /class="[^"]*brand-wordmark/.test(read(f))).sort()
    expect(users).toEqual([
      path.join('frontend/src/admin/AdminLayout.vue'),
      path.join('frontend/src/brand/AuthShell.vue'),
      path.join('frontend/src/portal/PortalLayout.vue')
    ])
  })
})

describe('BrandMark 品牌标识（IFC-328）', () => {
  it('TC-UNIT-850 / IFC-328：透明枫叶标志默认 32px，size 可调，装饰图无替代文字', () => {
    const def = mount(BrandMark)
    expect(def.attributes('width')).toBe('32')
    expect(def.attributes('aria-hidden')).toBe('true')
    expect(def.element.tagName.toLowerCase()).toBe('img')
    expect(def.attributes('alt')).toBe('')
    expect(mount(BrandMark, { props: { size: 44 } }).attributes('height')).toBe('44')
    const src = read('frontend/src/brand/BrandMark.vue')
    expect(src).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/)
    expect(src).toContain("./assets/maple-leaf.png")
    const image = fs.readFileSync(path.join(ROOT, 'frontend/src/brand/assets/maple-leaf.png'))
    expect(image.subarray(0, 8)).toEqual(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
  })
})
