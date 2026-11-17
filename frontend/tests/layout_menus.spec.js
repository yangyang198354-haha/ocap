// ocap_brand_layout GROUP_D（MOD-131）：导航配置与纯函数守护（IFC-316/317/330）。
// 层级：unit（纯函数 + 配置常量，无框架组件）。TC-UNIT-801 起。
import { describe, expect, it } from 'vitest'
import {
  ADMIN_MENU, LEGACY_UNITS_HASH, PORTAL_MENU, PORTAL_USER_MENU, isPathMatch, nextOpenKey, resolveActive, visibleMenu
} from '@/layout/menus'
import { truncateLabel } from '@/layout/labels'

const labels = (menu) => menu.map((n) => n.label)

describe('用户端菜单配置（US-210/211/217/229）', () => {
  it('TC-UNIT-801 / AC-210-01、AC-229-01：业委会成员 9 个一级项按序，信息公开为末位', () => {
    expect(labels(visibleMenu(PORTAL_MENU, { isCommittee: true }))).toEqual(
      ['主页', '我的房屋', '决议', '投票/调查', '报销/备用金', '收入表', '财务报表', '待办', '信息公开']
    )
  })

  it('TC-UNIT-802 / AC-211-01、AC-211-02：非业委会成员恰 6 项且没有置灰项；成员 9 项全部显示', () => {
    expect(labels(visibleMenu(PORTAL_MENU, { isCommittee: false }))).toEqual(
      ['主页', '我的房屋', '决议', '投票/调查', '财务报表', '信息公开']
    )
    expect(visibleMenu(PORTAL_MENU, { isCommittee: true })).toHaveLength(9)
    // 被隐藏的三项恰为 audience=committee 的三项（不是靠置灰/disabled 字段）
    const hidden = PORTAL_MENU.filter((n) => n.audience === 'committee').map((n) => n.label)
    expect(hidden).toEqual(['报销/备用金', '收入表', '待办'])
    for (const node of PORTAL_MENU) expect(node).not.toHaveProperty('disabled')
  })

  it('TC-UNIT-803 / AC-211-04：me 未加载（ctx 缺失或 isCommittee 非真）时先显示全员 6 项，不闪现业委会专属项', () => {
    for (const ctx of [undefined, null, {}, { isCommittee: false }, { isCommittee: undefined }]) {
      const shown = labels(visibleMenu(PORTAL_MENU, ctx))
      expect(shown, JSON.stringify(ctx)).toHaveLength(6)
      for (const t of ['报销/备用金', '收入表', '待办']) expect(shown).not.toContain(t)
    }
    expect(visibleMenu(null, { isCommittee: true })).toEqual([])
  })

  it('TC-UNIT-804 / AC-236-01（旧 AC-214-01、AC-215-01、AC-215-02）：二级项数量——我的房屋 5、决议 3、报销 2；其余一级项无 children', () => {
    const byKey = Object.fromEntries(PORTAL_MENU.map((n) => [n.key, n]))
    // 改写：旧 6 项（含"待我审批的同住人申请""选择房屋"）→ 新 5 项（IFC-339，AC-236-01、Q-IP-13=A）
    expect(byKey.units.children.map((c) => c.label)).toEqual(
      ['我的身份与房屋', '认证产权', '认证申诉', '我的同住人申请', '我的申诉']
    )
    expect(byKey.units.children.some((c) => c.label === '选择房屋' || c.label === '待我审批的同住人申请')).toBe(false)
    expect(byKey.resolutions.children.map((c) => c.label)).toEqual(['公开决议', '我发起的', '待我表决'])
    expect(byKey.claims.children.map((c) => c.label)).toEqual(['我提交的', '待我审批'])
    const leaves = PORTAL_MENU.filter((n) => !n.children).map((n) => n.label)
    expect(leaves).toEqual(['主页', '投票/调查', '收入表', '财务报表', '待办', '信息公开']) // AC-217-01 的 6 项
    for (const n of PORTAL_MENU) expect(Boolean(n.to) !== Boolean(n.children), n.key).toBe(true) // to 与 children 二选一
  })

  it('TC-UNIT-805 / AC-233-01（旧 AC-212-02、AC-213-01）：个人中心 7 项按序（第 2 项改名"我的身份与房屋"，地址不变），地址互不相同且都在 /me/ 下（退出登录为动作，不在配置内）', () => {
    // 改写：旧第 2 项文案"我的身份" → "我的身份与房屋"
    expect(labels(PORTAL_USER_MENU)).toEqual(['界面风格', '我的身份与房屋', '个人资料', '手机号', '设置密码', '邮箱验证', '账号注销'])
    expect(PORTAL_USER_MENU.map((i) => i.to)).toEqual(
      ['/me/style', '/me/identity', '/me/profile', '/me/phone', '/me/password', '/me/email', '/me/cancel']
    )
    expect(new Set(PORTAL_USER_MENU.map((i) => i.to)).size).toBe(7)
    expect(PORTAL_USER_MENU.some((i) => i.label === '退出登录')).toBe(false)
  })

  it('TC-UNIT-806 / AC-235-01（旧 AC-214-03）：仅"我的身份与房屋"带 pendingReview 角标键', () => {
    const badged = PORTAL_MENU.flatMap((n) => n.children || []).filter((c) => c.badge)
    // 改写：角标由已取消的"待我审批的同住人申请"项迁到"我的身份与房屋"项（ADR-133、Q-IP-04=A）
    expect(badged.map((c) => [c.label, c.badge])).toEqual([['我的身份与房屋', 'pendingReview']])
  })

  it('TC-UNIT-807 / AC-235-03（旧 REQ-FUNC-215、AC-221-02）：LEGACY_UNITS_HASH 只剩 #appeal → /units/appeal（#review 改由 /units#review 同页定位）', () => {
    // 改写：旧 { '#review': '/units/review', '#appeal': ... } → 新仅 #appeal（IFC-339，ADR-133）
    expect(LEGACY_UNITS_HASH).toEqual({ '#appeal': '/units/appeal' })
    expect(Object.keys(LEGACY_UNITS_HASH)).not.toContain('#review')
    const units = PORTAL_MENU.find((n) => n.key === 'units')
    for (const target of Object.values(LEGACY_UNITS_HASH)) expect(units.children.some((c) => c.to === target), target).toBe(true)
  })
})

describe('管理端菜单配置（US-224/225）', () => {
  it('TC-UNIT-808 / AC-224-01：9 个一级项按序', () => {
    expect(labels(ADMIN_MENU)).toEqual(['业主清册', '申诉', '房屋关系', '业委会席位', '审批流程', '财务', '账号', '内容管理', '审计/配置'])
  })

  it('TC-UNIT-809 / AC-224-03：业主清册、申诉、房屋关系、业委会席位、审批流程 5 项直达且指向原路径', () => {
    const direct = ADMIN_MENU.slice(0, 5)
    expect(direct.map((n) => n.to)).toEqual(
      ['/admin/registry', '/admin/appeals', '/admin/memberships', '/admin/seats', '/admin/flows']
    )
    for (const n of direct) expect(n.children).toBeUndefined()
  })

  it('TC-UNIT-810 / AC-225-01、AC-225-02、AC-225-03：财务 2、账号 2、内容管理 7、审计/配置 2 个二级项', () => {
    const byKey = Object.fromEntries(ADMIN_MENU.map((n) => [n.key, n]))
    expect(byKey.finance.children.map((c) => c.label)).toEqual(['报销/备用金记录', '金额上限'])
    expect(byKey.users.children.map((c) => c.label)).toEqual(['管理员账号', '注册用户'])
    expect(byKey.audit.children.map((c) => c.label)).toEqual(['系统配置', '审计日志'])
    expect(byKey.content.children.map((c) => c.label)).toEqual([
      '信息公开', '版式模板', '素材库', 'AI 服务·模型与生成服务', 'AI 服务·提示词模板', '平台账户', '内容参数'
    ])
    for (const n of ADMIN_MENU) expect(n.audience).toBe('all')
  })

  it('TC-UNIT-811 / IFC-316：全部菜单 key 唯一，to 为绝对路径；管理端路径均在 /admin 下', () => {
    const keys = []
    const tos = []
    for (const menu of [PORTAL_MENU, ADMIN_MENU]) {
      for (const n of menu) {
        keys.push(n.key)
        if (n.to) tos.push(n.to)
        for (const c of n.children || []) { keys.push(c.key); tos.push(c.to) }
      }
    }
    expect(new Set(keys).size).toBe(keys.length)
    for (const to of tos) expect(to.startsWith('/'), to).toBe(true)
    for (const n of ADMIN_MENU) for (const to of [n.to, ...(n.children || []).map((c) => c.to)].filter(Boolean)) expect(to.startsWith('/admin/'), to).toBe(true)
  })
})

describe('isPathMatch / resolveActive / nextOpenKey', () => {
  it('TC-UNIT-812 / IFC-317：isPathMatch——"/" 只精确匹配；前缀按路径段边界，不误吞 /resolutions2', () => {
    expect(isPathMatch('/', '/')).toBe(true)
    expect(isPathMatch('/units', '/')).toBe(false)
    expect(isPathMatch('/resolutions', '/resolutions')).toBe(true)
    expect(isPathMatch('/resolutions/12', '/resolutions')).toBe(true)
    expect(isPathMatch('/resolutions2', '/resolutions')).toBe(false)
    expect(isPathMatch('/unit', '/units')).toBe(false)
    expect(isPathMatch(undefined, '/')).toBe(false)
    expect(isPathMatch('/x', null)).toBe(false)
  })

  it('TC-UNIT-813 / AC-210-02、AC-215-04：/resolutions/12 仅"决议"一级高亮，二级无高亮；/info/5 仅"信息公开"', () => {
    const r = resolveActive(PORTAL_MENU, '/resolutions/12')
    expect(r.node.label).toBe('决议')
    expect(r.leaf).toBeNull()
    const i = resolveActive(PORTAL_MENU, '/info/5')
    expect(i.node.label).toBe('信息公开')
    expect(i.leaf).toBeNull()
    // 任一路径至多命中一个一级项（find 取首个）：逐项验证"高亮数 ≤ 1"
    for (const p of ['/', '/units', '/units/review', '/resolutions/mine', '/polls/3', '/claims/todo', '/tasks', '/reports', '/info']) {
      const hits = PORTAL_MENU.filter((n) => n.match.some((m) => isPathMatch(p, m)))
      expect(hits.length, p).toBe(1)
      expect(resolveActive(PORTAL_MENU, p).node.key, p).toBe(hits[0].key)
    }
  })

  it('TC-UNIT-814 / AC-217-02、AC-216-04：/polls/3 仍高亮"投票/调查"；/units/appeals 解析到我的房屋 › 我的申诉；主页只在 "/" 高亮', () => {
    expect(resolveActive(PORTAL_MENU, '/polls/3').node.label).toBe('投票/调查')
    const u = resolveActive(PORTAL_MENU, '/units/appeals')
    expect([u.node.label, u.leaf.label]).toEqual(['我的房屋', '我的申诉'])
    expect(resolveActive(PORTAL_MENU, '/').node.label).toBe('主页')
    expect(resolveActive(PORTAL_MENU, '/units').leaf.label).toBe('我的身份与房屋')
  })

  it('TC-UNIT-815 / AC-213-01、AC-221-01：个人中心 /me/* 与未知路径不命中任何一级项', () => {
    for (const p of ['/me', '/me/profile', '/nope', '/login']) expect(resolveActive(PORTAL_MENU, p)).toEqual({ node: null, leaf: null })
  })

  it('TC-UNIT-816 / AC-224-02、AC-225-02、AC-225-04：管理端编辑页高亮"内容管理 › 信息公开"；提示词模板与模型服务二级项互不混淆；注册用户分区', () => {
    const e = resolveActive(ADMIN_MENU, '/admin/content/posts/12')
    expect([e.node.label, e.leaf.label]).toEqual(['内容管理', '信息公开'])
    const p = resolveActive(ADMIN_MENU, '/admin/content/services/prompts')
    expect(p.leaf.label).toBe('AI 服务·提示词模板')
    expect(resolveActive(ADMIN_MENU, '/admin/content/services').leaf.label).toBe('AI 服务·模型与生成服务')
    const r = resolveActive(ADMIN_MENU, '/admin/users/registered')
    expect([r.node.label, r.leaf.label]).toEqual(['账号', '注册用户'])
    expect(resolveActive(ADMIN_MENU, '/admin/registry').leaf).toBeNull()
  })

  it('TC-UNIT-817 / AC-216-01、AC-216-04：nextOpenKey——主页与无二级项一级为 null；有二级项一级返回其 key', () => {
    expect(nextOpenKey(PORTAL_MENU, '/')).toBeNull()
    expect(nextOpenKey(PORTAL_MENU, '/polls/3')).toBeNull()
    expect(nextOpenKey(PORTAL_MENU, '/units/review')).toBe('units')
    expect(nextOpenKey(PORTAL_MENU, '/resolutions/12')).toBe('resolutions')
    expect(nextOpenKey(ADMIN_MENU, '/admin/audit/logs')).toBe('audit')
    expect(nextOpenKey(ADMIN_MENU, '/admin/flows')).toBeNull()
  })

  it('TC-UNIT-818 / IFC-317 输入校验：空串、非字符串、空菜单不抛错，返回空结果', () => {
    for (const bad of ['', null, undefined, 42, {}]) {
      expect(resolveActive(PORTAL_MENU, bad)).toEqual({ node: null, leaf: null })
      expect(nextOpenKey(PORTAL_MENU, bad)).toBeNull()
    }
    expect(resolveActive(null, '/')).toEqual({ node: null, leaf: null })
    expect(nextOpenKey([], '/units')).toBeNull()
  })
})

describe('truncateLabel（IFC-330）', () => {
  it('TC-UNIT-819 / AC-212-04、AC-226-05：恰 12 个字不截断；13 个字截为前 12 个并加省略号', () => {
    expect(truncateLabel('一二三四五六七八九十甲乙')).toBe('一二三四五六七八九十甲乙')
    expect(truncateLabel('一二三四五六七八九十甲乙丙')).toBe('一二三四五六七八九十甲乙…')
    expect(truncateLabel('abcdefghijklm')).toBe('abcdefghijkl…')
  })

  it('TC-UNIT-820 / IFC-330：按 Unicode 码点计数（非 BMP 字符算 1 个），自定义 max 生效', () => {
    const emoji = '😀'.repeat(13)
    expect([...truncateLabel(emoji)]).toHaveLength(13) // 12 个 + 省略号
    expect(truncateLabel(emoji).endsWith('…')).toBe(true)
    expect(truncateLabel('😀'.repeat(12))).toBe('😀'.repeat(12))
    expect(truncateLabel('abcdef', 3)).toBe('abc…')
    expect(truncateLabel('abc', 3)).toBe('abc')
  })

  it('TC-UNIT-821 / AC-212-04：非字符串或空值返回空串（调用方再回退"业主"/"管理员"）', () => {
    for (const bad of [null, undefined, '', 0, 12, {}, []]) expect(truncateLabel(bad)).toBe('')
  })
})
