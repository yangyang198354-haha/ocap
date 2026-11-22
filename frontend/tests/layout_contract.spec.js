// ocap_brand_layout GROUP_D（MOD-131，画像 P5/P6 契约要求）：新增页面（me/*、units/*、分区页、用户菜单）对 api.js 的调用契约。
// 本批 frontend/src/shared/api.js 与 miniprogram/utils/api.js 零改动；这里证明：新页面只经 api.js 既有函数发请求，
// 且这些函数的 方法+路径 能对应到后端路由（静态解析 backend/apps/*/urls.py；Django resolve() 级校验见 backend/tests/integration/test_frontend_contract.py，本机无 Django 未运行）。
// 层级：integration（跨 前端页面 ↔ api.js ↔ 后端路由表）。TC-INT-921 起。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import * as api from '@/shared/api'

const { http, adminHttp } = mocked
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')
const list = (dir, ext) => fs.readdirSync(path.join(ROOT, dir)).filter((f) => f.endsWith(ext)).map((f) => `${dir}/${f}`)

// 本批新增或改造、会发请求的前端文件
const NEW_FILES = [
  ...list('frontend/src/portal/me', '.vue'), 'frontend/src/portal/me/useProfile.js',
  ...list('frontend/src/portal/units', '.vue'), 'frontend/src/stores/housing.js',
  'frontend/src/portal/Me.vue', 'frontend/src/portal/Units.vue', 'frontend/src/portal/Resolutions.vue', 'frontend/src/portal/Claims.vue',
  'frontend/src/portal/PortalLayout.vue', 'frontend/src/portal/PortalUserMenu.vue',
  'frontend/src/admin/AdminLayout.vue', 'frontend/src/admin/AdminUserMenu.vue', 'frontend/src/admin/adminSession.js', 'frontend/src/admin/AdminLogin.vue',
  'frontend/src/admin/AdminFinance.vue', 'frontend/src/admin/AdminUsers.vue', 'frontend/src/admin/AdminAudit.vue', 'frontend/src/admin/AdminAiServices.vue',
  ...list('frontend/src/brand', '.vue')
]
const CLIENTS = ['authApi', 'meApi', 'unitApi', 'approvalApi', 'resolutionApi', 'claimApi', 'incomeApi', 'ledgerApi', 'pollApi', 'attachmentApi', 'infoApi', 'admin']
const REF_RE = new RegExp(`\\b(${CLIENTS.join('|')})\\.([A-Za-z_]\\w*)\\s*\\(`, 'g')
const EXPORTS = { ...api }

function refsOf(file) {
  const text = read(file)
  return [...text.matchAll(REF_RE)].map((m) => [m[1], m[2], file])
}

// 把后端 urls.py 的 path("...") 转为正则
function backendPatterns() {
  const dirs = fs.readdirSync(path.join(ROOT, 'backend/apps'))
  const out = []
  for (const d of dirs) {
    const f = path.join(ROOT, 'backend/apps', d, 'urls.py')
    if (!fs.existsSync(f)) continue
    for (const m of fs.readFileSync(f, 'utf8').matchAll(/\bpath\(\s*"([^"]*)"/g)) {
      const rx = m[1].replace(/<(?:int|str|uuid|slug):[^>]+>/g, '[^/]+').replace(/<[^>]+>/g, '[^/]+')
      out.push(new RegExp(`^/${rx}/?$`))
    }
  }
  return out
}

beforeEach(() => {
  vi.clearAllMocks()
  for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockReset().mockResolvedValue({})
})

describe('新增页面只经 api.js 既有函数发请求', () => {
  it('TC-INT-921 / REQ-NFUNC-040、C-64：新页面/仓库/菜单里引用的 api 函数（meApi/unitApi/…/admin.*）全部是 api.js 既有导出的函数', () => {
    const refs = NEW_FILES.flatMap(refsOf)
    expect(refs.length).toBeGreaterThan(30)
    const missing = refs.filter(([client, fn]) => typeof EXPORTS[client]?.[fn] !== 'function').map(([c, f, file]) => `${file}: ${c}.${f}`)
    expect(missing).toEqual([])
    // 个人中心与我的房屋相关的函数必须被覆盖到（拆页后没有遗漏调用）
    const used = new Set(refs.map(([c, f]) => `${c}.${f}`))
    for (const must of ['meApi.profile', 'meApi.updateProfile', 'meApi.housing', 'meApi.sendCode', 'meApi.bindPhone', 'meApi.changePhone', 'meApi.setPassword', 'meApi.verifyEmail', 'meApi.cancelAccount',
      'unitApi.certify', 'unitApi.submitAppeal', 'unitApi.withdrawAppeal', 'unitApi.createResidentApplication', 'unitApi.withdrawResidentApplication', 'unitApi.decideResidentApplication', 'unitApi.removeResident', 'unitApi.leaveUnit', 'unitApi.myAppeals', 'unitApi.myResidentApplications', 'unitApi.residentApplicationsToReview',
      'admin.login', 'admin.users', 'admin.admins', 'admin.claims', 'admin.auditLogs', 'admin.contentServices', 'admin.promptTemplates', 'resolutionApi.list', 'claimApi.list']) {
      expect(used.has(must), must).toBe(true)
    }
    // F1（ocap_batch_1118，AC-244-02）：旧清单 unitApi.createAppeal → 新 unitApi.submitAppeal（createAppeal 仅保留导出，Web 页面不再引用）
    expect(used.has('unitApi.createAppeal')).toBe(false)
    expect(typeof EXPORTS.unitApi.createAppeal).toBe('function')
    // 新增调用也须被页面引用到：参与人、管理员取选项、业主候选（resolutionApi.participants 由 ResolutionDetail 使用）
    // 引用（调用或作为 fetcher 传入）均算被页面使用到
    const pagesText = ['frontend/src/portal/ResolutionDetail.vue', 'frontend/src/admin/AdminSeats.vue', 'frontend/src/admin/parts/SeatHolderPicker.vue'].map(read).join('\n')
    for (const must of ['resolutionApi.participants', 'admin.unitOptions', 'admin.ownerCandidates']) expect(pagesText.includes(must), must).toBe(true)
  })

  it('TC-INT-922 / ADR-117：新增/改造文件不直接引入 HTTP 客户端（http/adminHttp）发请求；只允许取/存令牌（getToken/setToken）', () => {
    const offenders = []
    for (const file of NEW_FILES) {
      const text = read(file)
      for (const m of text.matchAll(/import\s*\{([^}]*)\}\s*from\s*'@\/shared\/http'/g)) {
        const names = m[1].split(',').map((s) => s.trim()).filter(Boolean)
        const bad = names.filter((n) => !['getToken', 'setToken'].includes(n))
        if (bad.length) offenders.push(`${file}: ${bad.join(',')}`)
      }
      if (/\b(?:http|adminHttp)\.(?:get|post|put|patch|delete)\(/.test(text)) offenders.push(`${file}: 直接调用 http 客户端`)
    }
    expect(offenders).toEqual([])
  })

  it('TC-INT-923 / REQ-NFUNC-044（旧 REQ-NFUNC-040）：api.js 导出的函数集合与契约基线一致（本批仅新增 meApi 的 3 个 registry-matches 函数）', () => {
    const names = Object.fromEntries(CLIENTS.map((c) => [c, Object.keys(EXPORTS[c] || {}).sort()]))
    // 改写：meApi 基线加入 confirmRegistryMatches / dismissRegistryMatches / registryMatches（IFC-343）
    expect(names.meApi).toEqual(['bindPhone', 'cancelAccount', 'changePhone', 'confirmRegistryMatches', 'dismissRegistryMatches', 'housing', 'limits', 'me', 'profile', 'registryMatches', 'sendCode', 'setPassword', 'setTheme', 'theme', 'updateProfile', 'userProfile', 'verifyEmail'])
    // F2（ocap_batch_1118，IFC-363）：基线集合加 unitApi.submitAppeal、resolutionApi.participants、admin.unitOptions、admin.ownerCandidates
    expect(names.unitApi).toEqual(['certify', 'createAppeal', 'createResidentApplication', 'decideResidentApplication', 'leaveUnit', 'myAppeals', 'myResidentApplications', 'options', 'removeResident', 'residentApplicationsToReview', 'submitAppeal', 'withdrawAppeal', 'withdrawResidentApplication'])
    expect(names.resolutionApi).toEqual(['create', 'detail', 'list', 'participants', 'resubmit', 'vote', 'withdraw'])
    expect(names.admin).toContain('unitOptions')
    expect(names.admin).toContain('ownerCandidates')
    expect(names.attachmentApi).toEqual(['download', 'upload'])
  })
})

describe('请求 方法+路径 与后端路由对应', () => {
  // [客户端, 调用, 期望方法, 期望路径]
  const CASES = [
    ['member', () => api.meApi.me(), 'GET', '/me'],
    ['member', () => api.meApi.housing(), 'GET', '/me/housing'],
    ['member', () => api.meApi.profile(), 'GET', '/me/profile'],
    ['member', () => api.meApi.updateProfile({ nickname: 'x' }), 'PATCH', '/me/profile'],
    ['member', () => api.meApi.sendCode('BIND_PHONE', '13900000000'), 'POST', '/me/codes'],
    ['member', () => api.meApi.bindPhone('13900000000', '123456'), 'POST', '/me/phone/bind'],
    ['member', () => api.meApi.changePhone('1', '2', '3', '4'), 'POST', '/me/phone/change'],
    ['member', () => api.meApi.setPassword({ password: 'a' }), 'PUT', '/me/password'],
    ['member', () => api.meApi.verifyEmail('123456', 'a@b.cn'), 'POST', '/me/email/verify'],
    ['member', () => api.meApi.cancelAccount('13900000000', '123456'), 'POST', '/me/cancel'],
    ['member', () => api.meApi.registryMatches(), 'GET', '/me/registry-matches'],
    ['member', () => api.meApi.confirmRegistryMatches([1, 2]), 'POST', '/me/registry-matches/confirm'],
    ['member', () => api.meApi.dismissRegistryMatches(), 'POST', '/me/registry-matches/dismiss'],
    ['member', () => api.meApi.theme(), 'GET', '/me/theme'],
    ['member', () => api.meApi.setTheme('bento'), 'PUT', '/me/theme'],
    ['member', () => api.unitApi.options({}), 'GET', '/units/options'],
    ['member', () => api.unitApi.certify(7, '张三'), 'POST', '/certifications'],
    ['member', () => api.unitApi.createAppeal({ unit_id: 7 }), 'POST', '/appeals'],
    ['member', () => api.unitApi.myAppeals(), 'GET', '/appeals/mine'],
    ['member', () => api.unitApi.createResidentApplication({ unit_id: 7 }), 'POST', '/resident-applications'],
    ['member', () => api.unitApi.myResidentApplications(), 'GET', '/resident-applications/mine'],
    ['member', () => api.unitApi.residentApplicationsToReview(), 'GET', '/resident-applications/to-review'],
    ['member', () => api.unitApi.decideResidentApplication(8, 'APPROVE'), 'POST', '/resident-applications/8/decision'],
    ['member', () => api.unitApi.removeResident(1, 9), 'DELETE', '/units/1/residents/9'],
    ['member', () => api.unitApi.leaveUnit(1), 'POST', '/units/1/leave'],
    ['member', () => api.resolutionApi.list('mine', {}), 'GET', '/resolutions'],
    ['member', () => api.claimApi.list({ scope: 'todo' }), 'GET', '/claims'],
    ['member', () => api.attachmentApi.upload(new File(['x'], 'a.png'), 'AVATAR'), 'POST', '/attachments'],
    ['member', () => api.authApi.logout(), 'POST', '/auth/logout'],
    ['admin', () => api.admin.login('a', 'b'), 'POST', '/admin/auth/login'],
    ['admin', () => api.admin.theme(), 'GET', '/admin/me/theme'],
    ['admin', () => api.admin.setTheme('bento'), 'PUT', '/admin/me/theme'],
    ['admin', () => api.admin.admins(), 'GET', '/admin/admins'],
    ['admin', () => api.admin.users({}), 'GET', '/admin/users'],
    ['admin', () => api.admin.claims({}), 'GET', '/admin/claims'],
    ['admin', () => api.admin.auditLogs({}), 'GET', '/admin/audit-logs'],
    ['admin', () => api.admin.systemConfigAll(), 'GET', '/admin/system-config'],
    ['admin', () => api.admin.systemConfig('audit.retention_months'), 'GET', '/admin/system-config/audit.retention_months'],
    ['admin', () => api.admin.updateSystemConfig('claim.amount_max', '1'), 'PUT', '/admin/system-config/claim.amount_max'],
    ['admin', () => api.admin.contentServices(), 'GET', '/admin/content/services'],
    ['admin', () => api.admin.promptTemplates(), 'GET', '/admin/content/prompt-templates']
  ]

  it('TC-INT-924 / AC-209-06、AC-213-02、AC-214-05：新页面用到的每个 api 函数发出的 方法+路径 与契约基线一致（含客户端：用户端令牌 vs 管理端令牌）', async () => {
    const wrong = []
    for (const [client, call, method, urlPath] of CASES) {
      for (const c of [http, adminHttp]) for (const m of Object.values(c)) m.mockClear()
      await call()
      const own = client === 'admin' ? adminHttp : http
      const other = client === 'admin' ? http : adminHttp
      const hits = Object.entries(own).filter(([, m]) => m.mock.calls.length)
      const otherHits = Object.entries(other).filter(([, m]) => m.mock.calls.length)
      if (hits.length !== 1 || otherHits.length) { wrong.push(`${method} ${urlPath}: 客户端不符`); continue }
      const [verb, mock] = hits[0]
      if (verb.toUpperCase() !== method || mock.mock.calls[0][0] !== urlPath) wrong.push(`${method} ${urlPath} ≠ ${verb.toUpperCase()} ${mock.mock.calls[0][0]}`)
    }
    expect(wrong).toEqual([])
    expect(CASES.length).toBeGreaterThanOrEqual(35)
  })

  it('TC-INT-925 / GR-C-004：上述 路径 全部能对应到后端 urls.py 声明的路由（静态解析；参数段按 <int:…>/<str:…> 通配）', () => {
    const patterns = backendPatterns()
    expect(patterns.length).toBeGreaterThan(100)
    const unresolved = CASES.map(([, , method, urlPath]) => [method, urlPath]).filter(([, urlPath]) => !patterns.some((rx) => rx.test(urlPath.replace(/^\//, '/'))))
    expect(unresolved).toEqual([])
  })

  it('TC-INT-926 / AC-225-02：页面写成的请求参数形状——决议 scope 与报销 scope 取自路由 section（public|mine|todo / mine|todo）', async () => {
    await api.resolutionApi.list('todo', { page: 2 })
    expect(http.get).toHaveBeenCalledWith('/resolutions', { params: { scope: 'todo', page: 2 } })
    await api.claimApi.list({ scope: 'mine', page: 1 })
    expect(http.get).toHaveBeenCalledWith('/claims', { params: { scope: 'mine', page: 1 } })
  })
})
